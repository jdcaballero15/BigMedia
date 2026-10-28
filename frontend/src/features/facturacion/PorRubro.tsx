import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import { descargarCsv } from '../../shared/csv'
import { formatearPeriodo } from '../../shared/fechas'
import { descargarPdf } from '../../shared/pdf'
import { formatearMonto } from './montos'

type Fila = {
  nombre: string
  ingresos: string
  dias_cupo: number
  porcentaje_ocupacion: number
}

type Totales = { total_ingresos: string; total_dias_cupo: number }

/** La API devuelve `rubros` (con `rubro`) o `grupos` (con `grupo`) según el corte. */
type Respuesta = Totales & {
  rubros?: (Fila & { rubro: number | null })[]
  grupos?: (Fila & { grupo: number | null })[]
}

type Reporte = Totales & { filas: (Fila & { clave: number | null })[] }

type Corte = 'rubro' | 'grupo'

/** Rubro de la marca (HU-050 criterio 1) o grupo económico de la marca (criterio 2, RN-016). */
const CORTES: Record<Corte, { ruta: string; columna: string; titulo: string }> = {
  rubro: { ruta: 'por-rubro', columna: 'Rubro', titulo: 'Ingresos por rubro' },
  grupo: { ruta: 'por-grupo', columna: 'Grupo económico', titulo: 'Ingresos por grupo económico' },
}

const vacio: Reporte = { filas: [], total_ingresos: '0.00', total_dias_cupo: 0 }

function normalizar(respuesta: Respuesta): Reporte {
  const filas = [
    ...(respuesta.rubros ?? []).map((fila) => ({ ...fila, clave: fila.rubro })),
    ...(respuesta.grupos ?? []).map((fila) => ({ ...fila, clave: fila.grupo })),
  ]
  return {
    filas,
    total_ingresos: respuesta.total_ingresos,
    total_dias_cupo: respuesta.total_dias_cupo,
  }
}

const anioActual = new Date().getFullYear()

export default function PorRubroPage() {
  const [desde, setDesde] = useState(`${anioActual}-01`)
  const [hasta, setHasta] = useState(`${anioActual}-12`)
  const [corte, setCorte] = useState<Corte>('rubro')
  const [datos, setDatos] = useState<Reporte>(vacio)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    const { ruta, titulo } = CORTES[corte]
    void apiGet<Respuesta>(`/api/facturacion/${ruta}/?desde=${desde}&hasta=${hasta}`)
      .then((respuesta) => {
        if (active) {
          setDatos(normalizar(respuesta))
          setError('')
        }
      })
      .catch(() => {
        if (active) {
          setDatos(vacio)
          setError(`No se pudo cargar el reporte de ${titulo.toLowerCase()}.`)
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [corte, desde, hasta])

  function cambiar(apply: () => void) {
    setLoading(true)
    apply()
  }

  function exportar() {
    const columnas = [CORTES[corte].columna, 'Ingresos', 'Días-cupo', '% Ocupación']
    const filas = datos.filas.map((fila) => [
      fila.nombre,
      Number(fila.ingresos),
      fila.dias_cupo,
      fila.porcentaje_ocupacion,
    ])
    descargarCsv(`${CORTES[corte].ruta}-${desde}-${hasta}.csv`, columnas, filas)
  }

  function exportarPdf() {
    const columnas = [CORTES[corte].columna, 'Ingresos', 'Días-cupo', '% Ocupación']
    const filas = datos.filas.map((fila) => [
      fila.nombre,
      formatearMonto(fila.ingresos),
      String(fila.dias_cupo),
      `${fila.porcentaje_ocupacion.toFixed(1)} %`,
    ])
    descargarPdf(
      `${CORTES[corte].ruta}-${desde}-${hasta}.pdf`,
      CORTES[corte].titulo,
      `Período: ${formatearPeriodo(desde)} a ${formatearPeriodo(hasta)}`,
      columnas,
      filas,
    )
  }

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Reportes</p>
          <h2>Por rubro o grupo</h2>
          <p className="muted">
            Ingresos y ocupación por rubro o por grupo económico de la marca, para el período.
          </p>
        </div>
        <div className="section-actions">
          <button
            className="button-ghost"
            onClick={exportarPdf}
            disabled={datos.filas.length === 0}
          >
            Exportar PDF
          </button>
          <button className="button-primary" onClick={exportar} disabled={datos.filas.length === 0}>
            Exportar CSV
          </button>
        </div>
      </div>
      <div className="filters card">
        <label>
          Cortar por
          <select
            value={corte}
            onChange={(event) => cambiar(() => setCorte(event.target.value as Corte))}
          >
            <option value="rubro">Rubro</option>
            <option value="grupo">Grupo económico</option>
          </select>
        </label>
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
          <p className="empty">Cargando reporte…</p>
        ) : datos.filas.length === 0 ? (
          <p className="empty">Sin datos en el período.</p>
        ) : (
          <table aria-label={CORTES[corte].titulo}>
            <thead>
              <tr>
                <th>{CORTES[corte].columna}</th>
                <th>Ingresos</th>
                <th>Días-cupo</th>
                <th>% Ocupación</th>
              </tr>
            </thead>
            <tbody>
              {datos.filas.map((fila) => (
                <tr key={fila.clave ?? 'sin-valor'}>
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
