import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import { formatearFecha } from '../../shared/fechas'
import { etiquetaEstadoReserva } from './types'
import type { Reserva } from './types'

type Props = {
  cartelId: number
  cartelNombre: string
  estadoNombre: string
  onCerrar: () => void
}

/** Avisa qué reservas activas quedan en un cartel que pasó a fuera de servicio (HU-039). */
export default function ReservasAfectadas({
  cartelId,
  cartelNombre,
  estadoNombre,
  onCerrar,
}: Props) {
  const [reservas, setReservas] = useState<Reserva[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    void apiGet<Reserva[]>(`/api/reservas/reservas/?cartel=${cartelId}&vigentes=1`)
      .then((rows) => {
        if (active) setReservas(rows)
      })
      .catch(() => {
        if (active) setError('No se pudieron consultar las reservas activas del cartel.')
      })
    return () => {
      active = false
    }
  }, [cartelId])

  if (error) {
    return (
      <div className="card section-gap" role="alert">
        <p className="error">{error}</p>
        <button className="button-ghost" onClick={onCerrar}>
          Cerrar
        </button>
      </div>
    )
  }
  if (reservas === null) {
    return (
      <div className="card section-gap" role="status">
        <p>Consultando reservas activas de {cartelNombre}…</p>
      </div>
    )
  }
  if (reservas.length === 0) {
    return (
      <div className="card section-gap" role="status">
        <p>
          {cartelNombre} quedó en «{estadoNombre}» y no tiene reservas activas. Mientras no vuelva a
          un estado operativo, no admite reservas nuevas.
        </p>
        <div className="row-actions">
          <button className="button-primary" onClick={onCerrar}>
            Entendido
          </button>
        </div>
      </div>
    )
  }

  return (
    <div
      className="card section-gap"
      role="alertdialog"
      aria-label="Reservas activas del cartel fuera de servicio"
    >
      <p>
        {cartelNombre} quedó en «{estadoNombre}» y tiene {reservas.length}{' '}
        {reservas.length === 1 ? 'reserva activa' : 'reservas activas'}. No se modificaron:
        reubicalas o avisá a los clientes. Mientras no vuelva a un estado operativo, no admite
        reservas nuevas.
      </p>
      <table aria-label="Reservas activas del cartel">
        <thead>
          <tr>
            <th>Reserva</th>
            <th>Campaña</th>
            <th>Desde</th>
            <th>Hasta</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {reservas.map((item) => (
            <tr key={item.id}>
              <td>{item.nombre}</td>
              <td>{item.campania_nombre}</td>
              <td>{formatearFecha(item.fecha_inicio)}</td>
              <td>{formatearFecha(item.fecha_fin)}</td>
              <td>{etiquetaEstadoReserva(item.estado)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="row-actions">
        <button className="button-primary" onClick={onCerrar}>
          Entendido
        </button>
      </div>
    </div>
  )
}
