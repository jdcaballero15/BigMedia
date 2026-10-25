import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import { formatearFecha } from '../../shared/fechas'

type PorVencer = {
  id: number
  nombre: string
  cartel_nombre: string
  campania: number
  fecha_inicio: string
  fecha_fin: string
}

type Panel = {
  carteles_libres: number
  carteles_ocupados: number
  campanias_activas: number
  por_vencer: PorVencer[]
}

export default function PanelPrincipal() {
  const [datos, setDatos] = useState<Panel | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    void apiGet<Panel>('/api/reservas/panel/')
      .then((panel) => {
        if (active) setDatos(panel)
      })
      .catch(() => {
        if (active) setError('No se pudo cargar el panel.')
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <section className="inventory-page">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Inicio</p>
          <h2>Panel</h2>
          <p className="muted">El estado del negocio hoy.</p>
        </div>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {datos && (
        <>
          <div className="filters card">
            <div>
              <strong>{datos.carteles_libres}</strong> carteles libres
            </div>
            <div>
              <strong>{datos.carteles_ocupados}</strong> ocupados
            </div>
            <div>
              <strong>{datos.campanias_activas}</strong> campañas activas
            </div>
          </div>
          <div className="card table-wrap">
            <h3>Reservas por vencer</h3>
            {datos.por_vencer.length === 0 ? (
              <p className="empty">Nada por vencer.</p>
            ) : (
              <table aria-label="Reservas por vencer">
                <thead>
                  <tr>
                    <th>Reserva</th>
                    <th>Cartel</th>
                    <th>Vence</th>
                  </tr>
                </thead>
                <tbody>
                  {datos.por_vencer.map((reserva) => (
                    <tr key={reserva.id}>
                      <td className="primary-cell">{reserva.nombre}</td>
                      <td>{reserva.cartel_nombre}</td>
                      <td>{formatearFecha(reserva.fecha_fin)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </section>
  )
}
