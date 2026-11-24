import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import { dateAIso, formatearFecha } from '../../shared/fechas'
import { usePuedeEditar } from '../../shared/sesion'
import type { Interaccion } from '../campanias/types'

const URL = '/api/campanias/interacciones/'

type Carga = { estado: 'cargando' | 'error' | 'listo'; filas: Interaccion[] }

/** Recordatorios pendientes de hoy y vencidos, para todo el equipo (HU-072). */
export default function RecordatoriosPanel() {
  const puedeEditar = usePuedeEditar()
  const [hoy] = useState(() => dateAIso(new Date()))
  const [carga, setCarga] = useState<Carga>({ estado: 'cargando', filas: [] })
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let active = true
    void apiGet<Interaccion[]>(`${URL}?recordatorio=pendiente`)
      .then((filas) => {
        if (active) setCarga({ estado: 'listo', filas })
      })
      .catch(() => {
        if (active) setCarga({ estado: 'error', filas: [] })
      })
    return () => {
      active = false
    }
  }, [revision])

  async function marcarHecho(interaccion: Interaccion) {
    setError('')
    try {
      await apiWrite(`${URL}${interaccion.id}/recordatorio-hecho/`, 'POST')
      setRevision((current) => current + 1)
    } catch {
      setError('No se pudo marcar el recordatorio como hecho.')
    }
  }

  return (
    <div className="card section-gap">
      <div className="card-heading">
        <h3>Recordatorios</h3>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {carga.estado === 'cargando' ? (
        <p className="empty">Cargando recordatorios…</p>
      ) : carga.estado === 'error' ? (
        <p className="error" role="alert">
          No se pudieron cargar los recordatorios.
        </p>
      ) : carga.filas.length === 0 ? (
        <p className="empty">No hay recordatorios para hoy.</p>
      ) : (
        <ul className="lista-filas" aria-label="Recordatorios">
          {carga.filas.map((fila) => (
            <li key={fila.id}>
              <div>
                <strong>{fila.recordatorio_texto}</strong>
                <small>
                  {fila.cliente_nombre}
                  {fila.registrada_por_nombre ? ` · cargó ${fila.registrada_por_nombre}` : ''}
                </small>
              </div>
              <span className="lista-filas-extremo">
                {fila.recordatorio_fecha !== null && fila.recordatorio_fecha < hoy && (
                  <span className="etiqueta-alerta">Vencido</span>
                )}
                {formatearFecha(fila.recordatorio_fecha)}
                {puedeEditar && (
                  <button className="button-ghost" onClick={() => void marcarHecho(fila)}>
                    Hecho
                  </button>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
