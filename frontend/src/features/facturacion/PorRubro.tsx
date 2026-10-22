import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import { descargarCsv } from '../../shared/csv'
import { descargarPdf } from '../../shared/pdf'
import { formatearMonto } from './montos'

type RubroFila = {
  rubro: number | null
  nombre: string
  ingresos: string
  dias_cupo: number
  porcentaje_ocupacion: number
}

type ReportePorRubro = {
  rubros: RubroFila[]
  total_ingresos: string
  total_dias_cupo: number
}

const vacio: ReportePorRubro = { rubros: [], total_ingresos: '0.00', total_dias_cupo: 0 }

const anioActual = new Date().getFullYear()

export default function PorRubroPage() {
  const [desde, setDesde] = useState(`${anioActual}-01`)
  const [hasta, setHasta] = useState(`${anioActual}-12`)
  const [datos, setDatos] = useState<ReportePorRubro>(vacio)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    void apiGet<ReportePorRubro>(`/api/facturacion/por-rubro/?desde=${desde}&hasta=${hasta}`)
      .then((reporte) => {
        if (active) {
          setDatos(reporte)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudo cargar el reporte por rubro.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [desde, hasta])

  function cambiar(apply: () => void) {
    setLoading(true)
    apply()
  }

  function exportar() {
    const columnas = ['Rubro', 'Ingresos', 'Días-cupo', '% Ocupación']
    const filas = datos.rubros.map((fila) => [
      fila.nombre,
      Number(fila.ingresos),
      fila.dias_cupo,
      fila.porcentaje_ocupacion,
    ])
    descargarCsv(`por-rubro-${desde}-${hasta}.csv`, columnas, filas)
  }

  function exportarPdf() {
    const columnas = ['Rubro', 'Ingresos', 'Días-cupo', '% Ocupación']
    const filas = datos.rubros.map((fila) => [
      fila.nombre,
      formatearMonto(fila.ingresos),
      String(fila.dias_cupo),
      `${fila.porcentaje_ocupacion.toFixed(1)} %`,
    ])
    descargarPdf(
      `por-rubro-${desde}-${hasta}.pdf`,
      'Ingresos por rubro',
      `Período: ${desde} a ${hasta}`,
      columnas,
      filas,
    )
  }

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Reportes</p>
          <h2>Por rubro</h2>
          <p className="muted">Ingresos y ocupación por rubro de la marca, para el período.</p>
        </div>
        <div className="section-actions">
          <button
            className="button-ghost"
            onClick={exportarPdf}
            disabled={datos.rubros.length === 0}
          >
            Exportar PDF
          </button>
          <button
            className="button-primary"
            onClick={exportar}
            disabled={datos.rubros.length === 0}
          >
            Exportar CSV
          </button>
        </div>
      </div>
      <div className="filters card">
        <label>
          Desde
          <input
            type="month"
            value={desde}
            onChange={(event) => cambiar(() => setDesde(event.target.value))}
          />
        </label>
        <label>
          Hasta
          <input
            type="month"
            value={hasta}
            onChange={(event) => cambiar(() => setHasta(event.target.value))}
          />
        </label>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="card table-wrap">
        {loading ? (
          <p className="empty">Cargando reporte por rubro…</p>
        ) : datos.rubros.length === 0 ? (
          <p className="empty">Sin datos en el período.</p>
        ) : (
          <table aria-label="Ingresos por rubro">
            <thead>
              <tr>
                <th>Rubro</th>
                <th>Ingresos</th>
                <th>Días-cupo</th>
                <th>% Ocupación</th>
              </tr>
            </thead>
            <tbody>
              {datos.rubros.map((fila) => (
                <tr key={fila.rubro === null ? 'sin-rubro' : fila.rubro}>
                  <td className="primary-cell">{fila.nombre}</td>
                  <td>{formatearMonto(fila.ingresos)}</td>
                  <td>{fila.dias_cupo}</td>
                  <td>{fila.porcentaje_ocupacion.toFixed(1)} %</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td className="primary-cell">Total</td>
                <td>{formatearMonto(datos.total_ingresos)}</td>
                <td>{datos.total_dias_cupo}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        )}
      </div>
    </>
  )
}
