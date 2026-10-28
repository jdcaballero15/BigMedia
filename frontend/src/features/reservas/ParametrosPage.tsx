import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import type { ParametrosDisponibilidad } from './types'

const URL = '/api/reservas/parametros/'

// RN-001 (día de borde) y RN-002 (la pendiente bloquea), con su explicación.
const OPCIONES: { campo: keyof ParametrosDisponibilidad; titulo: string; ayuda: string }[] = [
  {
    campo: 'borde_inclusivo',
    titulo: 'El día de borde se pisa',
    ayuda: 'Si una reserva termina el 15 y otra empieza el 15, ocupan el cartel el mismo día.',
  },
  {
    campo: 'tentativa_bloquea',
    titulo: 'La reserva pendiente bloquea el cupo',
    ayuda:
      'Si está marcada, no se puede confirmar una reserva donde una pendiente ya ocupa el cupo.',
  },
]

export default function ParametrosPage() {
  const [parametros, setParametros] = useState<ParametrosDisponibilidad | null>(null)
  const [error, setError] = useState('')
  const [guardado, setGuardado] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true
    void apiGet<ParametrosDisponibilidad>(URL)
      .then((datos) => {
        if (active) setParametros(datos)
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los parámetros.')
      })
    return () => {
      active = false
    }
  }, [])

  function cambiar(campo: keyof ParametrosDisponibilidad, valor: boolean) {
    if (parametros === null) return
    setParametros({ ...parametros, [campo]: valor })
    setGuardado(false)
  }

  async function guardar(event: FormEvent) {
    event.preventDefault()
    if (parametros === null) return
    setSaving(true)
    setError('')
    try {
      setParametros(await apiWrite<ParametrosDisponibilidad>(URL, 'PATCH', parametros))
      setGuardado(true)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudieron guardar los parámetros.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Configuración</p>
          <h2>Parámetros</h2>
          <p className="muted">Cómo cuenta la disponibilidad al confirmar una reserva.</p>
        </div>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {parametros === null ? (
        !error && <p className="empty">Cargando parámetros…</p>
      ) : (
        <form className="parametros" onSubmit={(event) => void guardar(event)}>
          {OPCIONES.map((opcion) => (
            <div key={opcion.campo} className="card parametro">
              <div>
                <label htmlFor={`parametro-${opcion.campo}`}>{opcion.titulo}</label>
                <p className="muted" id={`ayuda-${opcion.campo}`}>
                  {opcion.ayuda}
                </p>
              </div>
              <input
                id={`parametro-${opcion.campo}`}
                className="interruptor"
                type="checkbox"
                role="switch"
                aria-describedby={`ayuda-${opcion.campo}`}
                checked={parametros[opcion.campo]}
                onChange={(event) => cambiar(opcion.campo, event.target.checked)}
              />
            </div>
          ))}
          <p className="muted">
            El cambio rige desde la próxima confirmación: no recalcula las reservas que ya existen.
          </p>
          <div className="parametros-pie">
            {guardado && <p role="status">Parámetros guardados.</p>}
            <button type="submit" className="button-primary" disabled={saving}>
              Guardar
            </button>
          </div>
        </form>
      )}
    </section>
  )
}
