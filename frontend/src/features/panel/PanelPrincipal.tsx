import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import Cifras from '../../shared/Cifras'
import { dateAIso, formatearFecha } from '../../shared/fechas'

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

/** Parte de los carteles ocupados sobre el total, redondeada; 0 si no hay carteles. */
function porcentajeOcupado(panel: Panel): number {
  const total = panel.carteles_libres + panel.carteles_ocupados
  return total === 0 ? 0 : Math.round((panel.carteles_ocupados * 100) / total)
}

export default function PanelPrincipal() {
  const [hoy] = useState(() => dateAIso(new Date()))
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
          <Cifras
            titulo="Estado de hoy"
            cifras={[
              { etiqueta: 'Carteles libres', valor: datos.carteles_libres, tono: 'principal' },
              {
                etiqueta: 'Carteles ocupados',
                valor: datos.carteles_ocupados,
                detalle: `${porcentajeOcupado(datos)} % de ocupación`,
              },
              { etiqueta: 'Campañas activas', valor: datos.campanias_activas },
              {
                etiqueta: 'Por vencer',
                valor: datos.por_vencer.length,
                detalle: 'reservas en la lista',
                tono: 'alerta',
              },
            ]}
          />
          <div className="card">
            <div className="card-heading">
              <h3>Reservas por vencer</h3>
            </div>
            {datos.por_vencer.length === 0 ? (
              <p className="empty">Nada por vencer.</p>
            ) : (
              <ul className="lista-filas" aria-label="Reservas por vencer">
                {datos.por_vencer.map((reserva) => (
                  <li key={reserva.id}>
                    <div>
                      <strong>{reserva.nombre}</strong>
                      <small>{reserva.cartel_nombre}</small>
                    </div>
                    <span className="lista-filas-extremo">
                      {reserva.fecha_fin === hoy && (
                        <span className="etiqueta-alerta">Vence hoy</span>
                      )}
                      {formatearFecha(reserva.fecha_fin)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </section>
  )
}
