import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import type { EnvioFacturacion, ResultadoEnvio } from './types'

type Props = {
  mes: string
  puedeEditar: boolean
  /** El mes tiene ítems en Borrador: solo entonces se ofrece enviar. */
  hayBorradores: boolean
  onEnviado: () => void
}

const ENVIOS = '/api/facturacion/envios/'

function fechaHora(iso: string): string {
  return new Date(iso).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' })
}

function EnlacePlanilla({ envio }: { envio: EnvioFacturacion }) {
  return (
    <a href={`${ENVIOS}${envio.id}/planilla/`} download>
      Descargar planilla
    </a>
  )
}

/** "Enviar a facturar" del mes y los envíos ya hechos, con su planilla (HU-066). */
export default function EnviosDelMes({ mes, puedeEditar, hayBorradores, onEnviado }: Props) {
  const [envios, setEnvios] = useState<EnvioFacturacion[]>([])
  const [resultado, setResultado] = useState<ResultadoEnvio | null>(null)
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    if (!mes) return
    let active = true
    void apiGet<EnvioFacturacion[]>(`${ENVIOS}?mes=${mes}`)
      .then((filas) => {
        if (active) setEnvios(filas)
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los envíos del mes.')
      })
    return () => {
      active = false
    }
  }, [mes, revision])

  async function enviar() {
    setEnviando(true)
    try {
      const respuesta = await apiWrite<ResultadoEnvio>(ENVIOS, 'POST', { mes })
      setResultado(respuesta)
      setError('')
      setRevision((actual) => actual + 1)
      if (respuesta.envio) onEnviado()
    } catch {
      setError('No se pudo enviar a facturar.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="card section-gap" aria-label="Envíos a facturar">
      <div className="section-heading">
        <h3>Envíos a facturar</h3>
        {puedeEditar && hayBorradores && (
          <button className="button-primary" onClick={() => void enviar()} disabled={enviando}>
            Enviar a facturar
          </button>
        )}
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {resultado && <ResumenEnvio resultado={resultado} />}
      {envios.length === 0 ? (
        <p className="empty">Todavía no se envió nada de este mes.</p>
      ) : (
        <ul aria-label="Envíos del mes">
          {envios.map((envio) => (
            <li key={envio.id}>
              {fechaHora(envio.enviado_en)} · {envio.enviado_por_nombre} · {envio.cantidad} ítems ·{' '}
              <EnlacePlanilla envio={envio} />
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function ResumenEnvio({ resultado }: { resultado: ResultadoEnvio }) {
  const { envio, incompletos } = resultado
  return (
    <div role="status" aria-label="Resultado del envío">
      {envio ? (
        <p>
          Se enviaron {envio.cantidad} ítems a facturar. <EnlacePlanilla envio={envio} />
        </p>
      ) : (
        <p className="notice">No hay ítems completos para enviar.</p>
      )}
      {incompletos.length > 0 && (
        <>
          <p className="error">{incompletos.length} quedaron en Borrador porque les falta:</p>
          <ul aria-label="Ítems incompletos">
            {incompletos.map((item) => (
              <li key={item.item}>
                {item.descripcion}: {item.faltan.join(', ')}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
