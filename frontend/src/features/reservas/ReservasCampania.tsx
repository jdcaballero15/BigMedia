import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import { formatearFecha } from '../../shared/fechas'
import type { Cartel } from '../inventario/types'
import ReservaForm from './ReservaForm'
import type { ReservaInput } from './ReservaForm'
import type { Reserva, ResultadoConfirmacion } from './types'
import { etiquetaEstadoReserva } from './types'
import CostosReserva from '../costos/CostosReserva'
import { usePuedeEditar } from '../../shared/sesion'
import MenuFila from '../../shared/MenuFila'

type Props = {
  campaniaId: number
  /** Cambia cuando se crean reservas desde otra sección (por ejemplo, "Agregar carteles"). */
  revisionExterna?: number
  onCambio?: () => void
  /** "Confirmar reservas" solo se ofrece con la campaña Confirmada (HU-059). */
  campaniaConfirmada?: boolean
}

export default function ReservasCampania(props: Props) {
  const { campaniaId, revisionExterna = 0, onCambio, campaniaConfirmada = false } = props
  const puedeEditar = usePuedeEditar()
  const [reservas, setReservas] = useState<Reserva[]>([])
  const [carteles, setCarteles] = useState<Cartel[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState<Reserva | 'new' | null>(null)
  const [costosDe, setCostosDe] = useState<number | null>(null)
  const [revision, setRevision] = useState(0)
  const [confirmacion, setConfirmacion] = useState<ResultadoConfirmacion | null>(null)
  const [confirmando, setConfirmando] = useState(false)

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

  async function confirmarReservas() {
    setConfirmando(true)
    try {
      const resultado = await apiWrite<ResultadoConfirmacion>(
        '/api/reservas/reservas/confirmar-en-bloque/',
        'POST',
        { campania: campaniaId },
      )
      setConfirmacion(resultado)
      setError('')
      setRevision((current) => current + 1)
      onCambio?.()
    } catch {
      setError('No se pudieron confirmar las reservas.')
    } finally {
      setConfirmando(false)
    }
  }

  const hayPendientes = reservas.some((item) => item.estado === 'pendiente')

  return (
    <div className="card section-gap">
      <div className="section-heading">
        <h3>Reservas</h3>
        {puedeEditar && (
          <div className="row-actions">
            {campaniaConfirmada && hayPendientes && (
              <button
                className="button-primary"
                onClick={() => void confirmarReservas()}
                disabled={confirmando}
              >
                Confirmar reservas
              </button>
            )}
            <button className="button-primary" onClick={() => setEditing('new')}>
              Nueva reserva
            </button>
          </div>
        )}
      </div>
      {confirmacion && <ResumenConfirmacion resultado={confirmacion} />}
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
                <td>{etiquetaEstadoReserva(item.estado)}</td>
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

function ResumenConfirmacion({ resultado }: { resultado: ResultadoConfirmacion }) {
  const { confirmadas, conflictos } = resultado
  return (
    <div role="status" aria-label="Resultado de la confirmación">
      <p>
        {confirmadas.length === 1
          ? 'Se confirmó 1 reserva.'
          : `Se confirmaron ${confirmadas.length} reservas.`}
      </p>
      {conflictos.length > 0 && (
        <>
          <p className="error">
            {conflictos.length === 1
              ? '1 quedó Pendiente por falta de cupo:'
              : `${conflictos.length} quedaron Pendientes por falta de cupo:`}
          </p>
          <ul aria-label="Conflictos">
            {conflictos.map((item) => (
              <li key={item.reserva}>
                {item.cartel_nombre}, {formatearFecha(item.fecha_inicio)} →{' '}
                {formatearFecha(item.fecha_fin)}: ocupado por{' '}
                {item.ocupada_por.map((otra) => otra.campania_nombre).join(', ')}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
