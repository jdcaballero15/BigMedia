import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'

type Rentabilidad = {
  cantidad_reservas: number
  ingreso: string
  costo: string
  margen: string
  porcentaje: number | null
}

export default function RentabilidadCampania({ campaniaId }: { campaniaId: number }) {
  const [datos, setDatos] = useState<Rentabilidad | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    void apiGet<Rentabilidad>(`/api/costos/campania/?campania=${campaniaId}`)
      .then((rollup) => {
        if (active) setDatos(rollup)
      })
      .catch(() => {
        if (active) setError('No se pudo cargar la rentabilidad.')
      })
    return () => {
      active = false
    }
  }, [campaniaId])

  return (
    <div className="card section-gap">
      <h3>Costos y rentabilidad</h3>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {datos && (
        <dl className="detail-grid">
          <div>
            <dt>Reservas</dt>
            <dd>{datos.cantidad_reservas}</dd>
          </div>
          <div>
            <dt>Ingreso</dt>
            <dd>{datos.ingreso}</dd>
          </div>
          <div>
            <dt>Costo</dt>
            <dd>{datos.costo}</dd>
          </div>
          <div>
            <dt>Margen</dt>
            <dd>
              {datos.margen}
              {datos.porcentaje !== null ? ` (${datos.porcentaje}%)` : ''}
            </dd>
          </div>
        </dl>
      )}
    </div>
  )
}
