import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import type { Catalogo } from '../inventario/types'
import {
  colorOcupacion,
  formatearPorcentaje,
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
      <td className="primary-cell">{cartel.nombre_visible}</td>
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
