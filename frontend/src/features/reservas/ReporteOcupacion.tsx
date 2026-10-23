import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import { descargarCsv } from '../../shared/csv'
import { descargarPdf } from '../../shared/pdf'
import type { Catalogo } from '../inventario/types'
import {
  colorOcupacion,
  formatearPorcentaje,
  nombreCartel,
  type CartelOcupacion,
  type ModalidadOcupacion,
  type PeriodoOcupacion,
  type ReporteOcupacion,
} from './ocupacion'

const vacio: ReporteOcupacion = { periodos: [], carteles: [], modalidades: [] }
const anioActual = new Date().getFullYear()

function valorCartel(cartel: CartelOcupacion, periodo: string): number | null {
  const celda = cartel.celdas.find((c) => c.periodo === periodo)
  return celda ? celda.porcentaje : null
}

function valorModalidad(modalidad: ModalidadOcupacion, periodo: string): number | null {
  const mes = modalidad.por_mes.find((m) => m.periodo === periodo)
  return mes ? mes.porcentaje : null
}

export default function ReporteOcupacionPage() {
  const [desde, setDesde] = useState(`${anioActual}-01`)
  const [hasta, setHasta] = useState(`${anioActual}-12`)
  const [zona, setZona] = useState('')
  const [modalidad, setModalidad] = useState('')
  const [zonas, setZonas] = useState<Catalogo[]>([])
  const [datos, setDatos] = useState<ReporteOcupacion>(vacio)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    void apiGet<Catalogo[]>('/api/inventario/zonas/')
      .then((filas) => {
        if (active) setZonas(filas)
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
    if (zona) params.set('zona', zona)
    if (modalidad) params.set('modalidad', modalidad)
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
  }, [desde, hasta, zona, modalidad])

  function cambiar(apply: () => void) {
    setLoading(true)
    apply()
  }

  function exportar() {
    const columnas = [
      'Cartel',
      'Modalidad',
      'Departamento',
      ...datos.periodos.map((p) => p.etiqueta),
      'Total',
    ]
    const filas = datos.carteles.map((cartel) => [
      nombreCartel(cartel),
      cartel.modalidad,
      cartel.zona_nombre,
      ...datos.periodos.map((p) => valorCartel(cartel, p.clave) ?? 0),
      cartel.ocupacion,
    ])
    descargarCsv(`ocupacion-${desde}-${hasta}.csv`, columnas, filas)
  }

  function filtrosTexto(): string {
    const partes = [`Período: ${desde} a ${hasta}`]
    const depto = zonas.find((z) => String(z.id) === zona)
    if (depto) partes.push(`Departamento: ${depto.nombre}`)
    if (modalidad) partes.push(`Modalidad: ${modalidad === 'fija' ? 'Fija' : 'Digital'}`)
    return partes.join(' · ')
  }

  function exportarPdf() {
    const columnas = [
      'Cartel',
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
        <label>
          Departamento
          <select value={zona} onChange={(event) => cambiar(() => setZona(event.target.value))}>
            <option value="">Todos</option>
            {zonas.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
              </option>
            ))}
          </select>
        </label>
        <label>
          Modalidad
          <select
            value={modalidad}
            onChange={(event) => cambiar(() => setModalidad(event.target.value))}
          >
            <option value="">Todas</option>
            <option value="fija">Fija</option>
            <option value="digital">Digital</option>
          </select>
        </label>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!loading && datos.modalidades.length > 0 && (
        <div className="card table-wrap">
          <h3>Evolución por modalidad</h3>
          <table aria-label="Ocupación por modalidad">
            <thead>
              <tr>
                <th>Modalidad</th>
                {datos.periodos.map((periodo) => (
                  <th key={periodo.clave}>{periodo.etiqueta}</th>
                ))}
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {datos.modalidades.map((item) => (
                <FilaModalidad key={item.modalidad} item={item} periodos={datos.periodos} />
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="card table-wrap">
        <h3>Mapa de calor por cartel</h3>
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

function FilaModalidad({
  item,
  periodos,
}: {
  item: ModalidadOcupacion
  periodos: PeriodoOcupacion[]
}) {
  return (
    <tr>
      <td className="primary-cell">{item.etiqueta}</td>
      {periodos.map((periodo) => {
        const valor = valorModalidad(item, periodo.clave)
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
