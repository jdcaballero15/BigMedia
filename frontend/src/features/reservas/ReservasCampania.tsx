import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import { dateAIso, formatearFecha } from '../../shared/fechas'
import type { Cartel } from '../inventario/types'
import ReservaForm from './ReservaForm'
import type { ReservaInput } from './ReservaForm'
import type { Reserva } from './types'
import { etiquetaEstadoReserva } from './types'
import CostosReserva from '../costos/CostosReserva'
import { usePuedeEditar } from '../../shared/sesion'
import MenuFila from '../../shared/MenuFila'

type Props = {
  campaniaId: number
  /** Cambia cuando se crean reservas desde otra sección (por ejemplo, "Agregar carteles"). */
  revisionExterna?: number
  onCambio?: () => void
  /** Una campaña Cancelada no admite reservas nuevas ni quitar (HU-024). */
  campaniaCancelada?: boolean
}

/** Hoy en "aaaa-mm-dd", para saber si una reserva ya está en exhibición. */
function hoy(): string {
  return dateAIso(new Date())
}

export default function ReservasCampania(props: Props) {
  const { campaniaId, revisionExterna = 0, onCambio, campaniaCancelada = false } = props
  const puedeEditar = usePuedeEditar()
  const [reservas, setReservas] = useState<Reserva[]>([])
  const [carteles, setCarteles] = useState<Cartel[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState<Reserva | 'new' | null>(null)
  const [costosDe, setCostosDe] = useState<number | null>(null)
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let active = true
    void apiGet<Cartel[]>('/api/inventario/carteles/?incluir_bajas=1')
      .then((rows) => {
        if (active) setCarteles(rows)
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los carteles.')
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    void apiGet<Reserva[]>(`/api/reservas/reservas/?campania=${campaniaId}`)
      .then((rows) => {
        if (active) {
          setReservas(rows)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar las reservas.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [campaniaId, revision, revisionExterna])

  async function saveReserva(input: ReservaInput) {
    if (editing === null) return
    const path =
      editing === 'new' ? '/api/reservas/reservas/' : `/api/reservas/reservas/${editing.id}/`
    await apiWrite(path, editing === 'new' ? 'POST' : 'PATCH', input)
    setEditing(null)
    setRevision((current) => current + 1)
    onCambio?.()
  }

  /** Saca la reserva de la campaña: la cancela o, si está en exhibición, la termina hoy (HU-037). */
  async function quitar(reserva: Reserva) {
    const enExhibicion = reserva.fecha_inicio <= hoy()
    const aviso = enExhibicion
      ? `¿Quitar ${reserva.cartel_nombre}? Ya está en exhibición: termina hoy y libera el cartel.`
      : `¿Quitar ${reserva.cartel_nombre}? La reserva se cancela y libera el cartel.`
    if (!window.confirm(aviso)) return
    try {
      await apiWrite(`/api/reservas/reservas/${reserva.id}/quitar/`, 'POST', {})
      setError('')
      setRevision((current) => current + 1)
      onCambio?.()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudo quitar la reserva.')
    }
  }

  return (
    <div className="card section-gap">
      <div className="section-heading">
        <h3>Reservas</h3>
        {puedeEditar && !campaniaCancelada && (
          <div className="row-actions">
            <button className="button-primary" onClick={() => setEditing('new')}>
              Nueva reserva
            </button>
          </div>
        )}
      </div>
      {editing !== null && (
        <ReservaForm
          key={editing === 'new' ? 'new' : editing.id}
          campaniaId={campaniaId}
          reserva={editing === 'new' ? null : editing}
          carteles={carteles}
          onSave={saveReserva}
          onCancel={() => setEditing(null)}
        />
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {loading ? (
        <p className="empty">Cargando reservas…</p>
      ) : reservas.length === 0 ? (
        <p className="empty">Esta campaña todavía no tiene reservas.</p>
      ) : (
        <table aria-label="Reservas de la campaña">
          <thead>
            <tr>
              <th>Reserva</th>
              <th>Cartel</th>
              <th>Período</th>
              <th>Estado</th>
              <th>Total</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {reservas.map((item) => (
              <tr key={item.id}>
                <td className="primary-cell">{item.nombre}</td>
                <td>{item.cartel_nombre}</td>
                <td>
                  {formatearFecha(item.fecha_inicio)} → {formatearFecha(item.fecha_fin)}
                </td>
                <td>{etiquetaEstadoReserva(item.estado_visible)}</td>
                <td>{item.total}</td>
                <td className="row-actions">
                  <button
                    className="button-ghost"
                    onClick={() => setCostosDe(costosDe === item.id ? null : item.id)}
                  >
                    Costos
                  </button>
                  <MenuFila
                    acciones={[
                      { etiqueta: 'Editar', onClick: () => setEditing(item), edicion: true },
                      !campaniaCancelada &&
                        item.estado_visible === 'confirmada' && {
                          etiqueta: 'Quitar',
                          onClick: () => void quitar(item),
                          edicion: true,
                        },
                    ]}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {costosDe !== null && <CostosReserva reservaId={costosDe} />}
    </div>
  )
}
