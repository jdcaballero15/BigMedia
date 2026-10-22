import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import { descargarCsv } from '../../shared/csv'
import { formatearMonto, sumarMontos } from './montos'
import type { ClienteFila, Periodo, ReporteIngresos } from './types'

const vacio: ReporteIngresos = { periodos: [], clientes: [], total: '0.00' }
const anioActual = new Date().getFullYear()

function claveCliente(cliente: ClienteFila): string {
  return cliente.cliente === null ? 'sin-cliente' : String(cliente.cliente)
}

export default function ReporteIngresosPage() {
  const [desde, setDesde] = useState(`${anioActual}-01`)
  const [hasta, setHasta] = useState(`${anioActual}-12`)
  const [datos, setDatos] = useState<ReporteIngresos>(vacio)
  const [expandidos, setExpandidos] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    void apiGet<ReporteIngresos>(`/api/facturacion/ingresos/?desde=${desde}&hasta=${hasta}`)
      .then((reporte) => {
        if (active) {
          setDatos(reporte)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudo cargar el reporte de ingresos.')
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

  function alternar(clave: string) {
    setExpandidos((previos) => {
      const siguiente = new Set(previos)
      if (siguiente.has(clave)) siguiente.delete(clave)
      else siguiente.add(clave)
      return siguiente
    })
  }

  function totalMes(periodo: Periodo): string {
    return sumarMontos(datos.clientes.map((cliente) => cliente.por_mes[periodo.mes] ?? '0.00'))
  }

  function exportar() {
    const columnas = ['Cliente', 'Marca', ...datos.periodos.map((p) => p.etiqueta), 'Total']
    const filas = datos.clientes.flatMap((cliente) =>
      cliente.marcas.map((marca) => [
        cliente.nombre,
        marca.nombre,
        ...datos.periodos.map((p) => Number(marca.por_mes[p.mes] ?? '0.00')),
        Number(marca.total),
      ]),
    )
    descargarCsv(`ingresos-${desde}-${hasta}.csv`, columnas, filas)
  }

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Reportes</p>
          <h2>Ingresos</h2>
          <p className="muted">
            Facturación por período, con el desglose de cada agencia a sus marcas.
          </p>
        </div>
        <button
          className="button-primary"
          onClick={exportar}
          disabled={datos.clientes.length === 0}
        >
          Exportar CSV
        </button>
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
          <p className="empty">Cargando ingresos…</p>
        ) : datos.clientes.length === 0 ? (
          <p className="empty">Sin ingresos en el período.</p>
        ) : (
          <table aria-label="Ingresos por cliente y marca">
            <thead>
              <tr>
                <th>Cliente / Marca</th>
                {datos.periodos.map((periodo) => (
                  <th key={periodo.mes}>{periodo.etiqueta}</th>
                ))}
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {datos.clientes.map((cliente) => {
                const clave = claveCliente(cliente)
                const abierto = expandidos.has(clave)
                return (
                  <FilasCliente
                    key={clave}
                    cliente={cliente}
                    periodos={datos.periodos}
                    abierto={abierto}
                    onAlternar={() => alternar(clave)}
                  />
                )
              })}
            </tbody>
            <tfoot>
              <tr>
                <td className="primary-cell">Total</td>
                {datos.periodos.map((periodo) => (
                  <td key={periodo.mes}>{formatearMonto(totalMes(periodo))}</td>
                ))}
                <td>{formatearMonto(datos.total)}</td>
              </tr>
            </tfoot>
          </table>
        )}
      </div>
    </>
  )
}

type FilasClienteProps = {
  cliente: ClienteFila
  periodos: Periodo[]
  abierto: boolean
  onAlternar: () => void
}

function FilasCliente({ cliente, periodos, abierto, onAlternar }: FilasClienteProps) {
  return (
    <>
      <tr>
        <td className="primary-cell">
          <button className="button-ghost" aria-expanded={abierto} onClick={onAlternar}>
            <span aria-hidden="true">{abierto ? '▾' : '▸'}</span> <span>{cliente.nombre}</span>
          </button>
        </td>
        {periodos.map((periodo) => (
          <td key={periodo.mes}>{formatearMonto(cliente.por_mes[periodo.mes] ?? '0.00')}</td>
        ))}
        <td>{formatearMonto(cliente.total)}</td>
      </tr>
      {abierto &&
        cliente.marcas.map((marca) => (
          <tr key={marca.marca === null ? 'sin-marca' : marca.marca}>
            <td className="muted indent">{marca.nombre}</td>
            {periodos.map((periodo) => (
              <td key={periodo.mes}>{formatearMonto(marca.por_mes[periodo.mes] ?? '0.00')}</td>
            ))}
            <td>{formatearMonto(marca.total)}</td>
          </tr>
        ))}
    </>
  )
}
