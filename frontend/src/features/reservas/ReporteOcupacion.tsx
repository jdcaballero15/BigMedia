import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import { descargarCsv } from '../../shared/csv'
import { formatearPeriodo } from '../../shared/fechas'
import { descargarPdf } from '../../shared/pdf'
import Cifras from '../../shared/Cifras'
import SelectorPeriodo from '../../shared/SelectorPeriodo'
import type { Formato } from '../inventario/types'
import {
  colorOcupacion,
  formatearPorcentaje,
  nombreCartel,
  type CartelOcupacion,
  type FormatoOcupacion,
  type PeriodoOcupacion,
  type ReporteOcupacion,
} from './ocupacion'

const vacio: ReporteOcupacion = { periodos: [], carteles: [], formatos: [] }
const anioActual = new Date().getFullYear()

function valorCartel(cartel: CartelOcupacion, periodo: string): number | null {
  const celda = cartel.celdas.find((c) => c.periodo === periodo)
  return celda ? celda.porcentaje : null
}

function valorFormato(item: FormatoOcupacion, periodo: string): number | null {
  const mes = item.por_mes.find((m) => m.periodo === periodo)
  return mes ? mes.porcentaje : null
}

export default function ReporteOcupacionPage() {
  const [desde, setDesde] = useState(`${anioActual}-01`)
  const [hasta, setHasta] = useState(`${anioActual}-12`)
  const [formato, setFormato] = useState('')
  const [formatos, setFormatos] = useState<Formato[]>([])
  const [datos, setDatos] = useState<ReporteOcupacion>(vacio)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    void apiGet<Formato[]>('/api/inventario/formatos/')
      .then((filas) => {
        if (active) setFormatos(filas)
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los filtros.')
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    const params = new URLSearchParams({ desde, hasta })
    if (formato) params.set('formato', formato)
    void apiGet<ReporteOcupacion>(`/api/reservas/reporte-ocupacion/?${params}`)
      .then((reporte) => {
        if (active) {
          setDatos(reporte)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudo cargar el reporte de ocupación.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [desde, hasta, formato])

  function cambiar(apply: () => void) {
    setLoading(true)
    apply()
  }

  function exportar() {
    const columnas = [
      'Cartel',
      'Formato',
      'Modalidad',
      'Departamento',
      ...datos.periodos.map((p) => p.etiqueta),
      'Total',
    ]
    const filas = datos.carteles.map((cartel) => [
      nombreCartel(cartel),
      cartel.formato_nombre,
      cartel.modalidad,
      cartel.zona_nombre,
      ...datos.periodos.map((p) => valorCartel(cartel, p.clave) ?? 0),
      cartel.ocupacion,
    ])
    descargarCsv(`ocupacion-${desde}-${hasta}.csv`, columnas, filas)
  }

  function filtrosTexto(): string {
    const partes = [`Período: ${formatearPeriodo(desde)} a ${formatearPeriodo(hasta)}`]
    const elegido = formatos.find((f) => String(f.id) === formato)
    if (elegido) partes.push(`Formato: ${elegido.nombre}`)
    return partes.join(' · ')
  }

  function exportarPdf() {
    const columnas = [
      'Cartel',
      'Formato',
      'Modalidad',
      'Departamento',
      ...datos.periodos.map((p) => p.etiqueta),
      'Total',
    ]
    const filas = datos.carteles.map((cartel) => {
      const valor = (periodo: string) => {
        const celda = valorCartel(cartel, periodo)
        return celda === null ? '—' : formatearPorcentaje(celda)
      }
      return [
        nombreCartel(cartel),
        cartel.formato_nombre,
        cartel.modalidad === 'fija' ? 'Fija' : 'Digital',
        cartel.zona_nombre,
        ...datos.periodos.map((p) => valor(p.clave)),
        formatearPorcentaje(cartel.ocupacion),
      ]
    })
    descargarPdf(`ocupacion-${desde}-${hasta}.pdf`, 'Ocupación', filtrosTexto(), columnas, filas)
  }

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Reportes</p>
          <h2>Ocupación</h2>
          <p className="muted">
            Ocupación en días-cupo por cartel y mes. El orden es el ranking de rendimiento.
          </p>
        </div>
        <div className="section-actions">
          <button
            className="button-ghost"
            onClick={exportarPdf}
            disabled={datos.carteles.length === 0}
          >
            Exportar PDF
          </button>
          <button
            className="button-primary"
            onClick={exportar}
            disabled={datos.carteles.length === 0}
          >
            Exportar CSV
          </button>
        </div>
      </div>
      <div className="filters card">
        <SelectorPeriodo
          desde={desde}
          hasta={hasta}
          onCambiar={(nuevoDesde, nuevoHasta) =>
            cambiar(() => {
              setDesde(nuevoDesde)
              setHasta(nuevoHasta)
            })
          }
        />
        <label>
          Formato
          <select
            value={formato}
            onChange={(event) => cambiar(() => setFormato(event.target.value))}
          >
            <option value="">Todos</option>
            {formatos.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
              </option>
            ))}
          </select>
        </label>
      </div>
      {!loading && datos.carteles.length > 0 && (
        <Cifras
          titulo="Resumen del período"
          cifras={[
            ...datos.formatos.map((item, indice) => ({
              etiqueta: `Ocupación ${item.nombre}`,
              valor: formatearPorcentaje(item.ocupacion),
              tono: indice === 0 ? ('principal' as const) : undefined,
            })),
            { etiqueta: 'Carteles en el reporte', valor: datos.carteles.length },
          ]}
        />
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!loading && datos.formatos.length > 0 && (
        <div className="card table-wrap section-gap">
          <div className="card-heading">
            <div>
              <h3>Evolución por formato</h3>
              <p className="muted">Ocupación de cada formato, mes a mes.</p>
            </div>
          </div>
          <table aria-label="Ocupación por formato">
            <thead>
              <tr>
                <th>Formato</th>
                {datos.periodos.map((periodo) => (
                  <th key={periodo.clave}>{periodo.etiqueta}</th>
                ))}
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {datos.formatos.map((item) => (
                <FilaFormato key={item.formato} item={item} periodos={datos.periodos} />
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="card table-wrap">
        <div className="card-heading">
          <div>
            <h3>Mapa de calor por cartel</h3>
            <p className="muted">
              Cada celda es la ocupación del cartel en el mes: cuanto más azul, más ocupado.
            </p>
          </div>
        </div>
        {loading ? (
          <p className="empty">Cargando ocupación…</p>
        ) : datos.carteles.length === 0 ? (
          <p className="empty">No hay carteles para estos filtros.</p>
        ) : (
          <table aria-label="Ocupación por cartel y mes">
            <thead>
              <tr>
                <th>Cartel</th>
                {datos.periodos.map((periodo) => (
                  <th key={periodo.clave}>{periodo.etiqueta}</th>
                ))}
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {datos.carteles.map((cartel) => (
                <FilaCartel key={cartel.id} cartel={cartel} periodos={datos.periodos} />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}

function FilaFormato({ item, periodos }: { item: FormatoOcupacion; periodos: PeriodoOcupacion[] }) {
  return (
    <tr>
      <td className="primary-cell">{item.nombre}</td>
      {periodos.map((periodo) => {
        const valor = valorFormato(item, periodo.clave)
        return <td key={periodo.clave}>{valor === null ? '—' : formatearPorcentaje(valor)}</td>
      })}
      <td>{formatearPorcentaje(item.ocupacion)}</td>
    </tr>
  )
}

function FilaCartel({
  cartel,
  periodos,
}: {
  cartel: CartelOcupacion
  periodos: PeriodoOcupacion[]
}) {
  return (
    <tr>
      <td className="primary-cell">{nombreCartel(cartel)}</td>
      {periodos.map((periodo) => {
        const valor = valorCartel(cartel, periodo.clave)
        return (
          <td
            key={periodo.clave}
            style={valor === null ? undefined : { background: colorOcupacion(valor) }}
          >
            {valor === null ? '—' : formatearPorcentaje(valor)}
          </td>
        )
      })}
      <td>{formatearPorcentaje(cartel.ocupacion)}</td>
    </tr>
  )
}
