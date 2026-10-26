import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import type { ParametrosDisponibilidad } from './types'

const URL = '/api/reservas/parametros/'

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
        <form className="card section-gap" onSubmit={(event) => void guardar(event)}>
          <label className="checkline">
            <input
              type="checkbox"
              checked={parametros.borde_inclusivo}
              onChange={(event) => cambiar('borde_inclusivo', event.target.checked)}
            />
            El día de borde se pisa
          </label>
          <p className="muted">
            Si una reserva termina el 15 y otra empieza el 15, ocupan el cartel el mismo día.
          </p>
          <label className="checkline">
            <input
              type="checkbox"
              checked={parametros.tentativa_bloquea}
              onChange={(event) => cambiar('tentativa_bloquea', event.target.checked)}
            />
            La reserva pendiente bloquea el cupo
          </label>
          <p className="muted">
            Si está marcada, no se puede confirmar una reserva donde una pendiente ya ocupa el cupo.
          </p>
          <p className="muted">
            El cambio rige desde la próxima confirmación: no recalcula las reservas que ya existen.
          </p>
          {guardado && <p role="status">Parámetros guardados.</p>}
          <button type="submit" className="button-primary" disabled={saving}>
            Guardar
          </button>
        </form>
      )}
    </section>
  )
}
