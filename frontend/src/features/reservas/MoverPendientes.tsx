import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import { formatearFecha } from '../../shared/fechas'
import type { Reserva } from './types'

type Props = {
  campaniaId: number
  /** Fechas que tenía la campaña antes de guardar, en aaaa-mm-dd. */
  inicioAnterior: string
  finAnterior: string
  inicioNuevo: string
  finNuevo: string
  onListo: () => void
}

/** Pregunta si mover las Pendientes a las fechas nuevas de la campaña (HU-058, criterios 3 y 4). */
export default function MoverPendientes(props: Props) {
  const { campaniaId, inicioAnterior, finAnterior, onListo } = props
  const [cantidad, setCantidad] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    let active = true
    void apiGet<Reserva[]>(`/api/reservas/reservas/?campania=${campaniaId}&estado=pendiente`)
      .then((rows) => {
        if (!active) return
        // Solo las que seguían a la campaña: una tanda con otras fechas no se pisa.
        const siguen = rows.filter(
          (r) => r.fecha_inicio === inicioAnterior && r.fecha_fin === finAnterior,
        )
        if (siguen.length === 0) onListo()
        else setCantidad(siguen.length)
      })
      .catch(() => {
        if (active) onListo()
      })
    return () => {
      active = false
    }
  }, [campaniaId, inicioAnterior, finAnterior, onListo])

  async function mover() {
    setEnviando(true)
    try {
      await apiWrite('/api/reservas/reservas/mover-pendientes/', 'POST', {
        campania: campaniaId,
        fecha_inicio_anterior: inicioAnterior,
        fecha_fin_anterior: finAnterior,
      })
      onListo()
    } catch {
      setError('No se pudieron actualizar las reservas. Podés reintentar.')
      setEnviando(false)
    }
  }

  if (cantidad === null) return null
  return (
    <div
      className="card section-gap"
      role="alertdialog"
      aria-label="Actualizar reservas Pendientes"
    >
      <p>
        La campaña cambió de fechas. ¿Actualizar las {cantidad} reservas Pendientes del{' '}
        {formatearFecha(inicioAnterior)} → {formatearFecha(finAnterior)} a{' '}
        {formatearFecha(props.inicioNuevo)} → {formatearFecha(props.finNuevo)}? Las Confirmadas no
        se tocan.
      </p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="row-actions">
        <button className="button-primary" onClick={() => void mover()} disabled={enviando}>
          Actualizar Pendientes
        </button>
        <button className="button-ghost" onClick={onListo} disabled={enviando}>
          No, dejarlas
        </button>
      </div>
    </div>
  )
}
