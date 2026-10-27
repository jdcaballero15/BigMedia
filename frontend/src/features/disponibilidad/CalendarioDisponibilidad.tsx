import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import { formatearFecha } from '../../shared/fechas'
import type { Catalogo, Formato } from '../inventario/types'
import type { Calendario, FilaCalendario } from './types'

type Reserva = {
  id: number
  nombre: string
  campania_nombre: string
  fecha_inicio: string
  fecha_fin: string
}

type CeldaElegida = { cartel: FilaCalendario; periodo: string } | null

export default function CalendarioDisponibilidad() {
  const [calendario, setCalendario] = useState<Calendario>({ periodos: [], carteles: [] })
  const [zonas, setZonas] = useState<Catalogo[]>([])
  const [formatos, setFormatos] = useState<Formato[]>([])
  const [zona, setZona] = useState('')
  const [formato, setFormato] = useState('')
  const [modalidad, setModalidad] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [elegida, setElegida] = useState<CeldaElegida>(null)
  const [detalle, setDetalle] = useState<Reserva[]>([])

  useEffect(() => {
    let active = true
    void Promise.all([
      apiGet<Catalogo[]>('/api/inventario/zonas/'),
      apiGet<Formato[]>('/api/inventario/formatos/'),
    ])
      .then(([zonasRows, formatosRows]) => {
        if (active) {
          setZonas(zonasRows)
          setFormatos(formatosRows)
        }
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
    const params = new URLSearchParams()
    if (zona) params.set('zona', zona)
    if (formato) params.set('formato', formato)
    if (modalidad) params.set('modalidad', modalidad)
    const suffix = params.toString() ? `?${params}` : ''
    void apiGet<Calendario>(`/api/reservas/calendario/${suffix}`)
      .then((data) => {
        if (active) {
          setCalendario(data)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudo cargar el calendario.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [zona, formato, modalidad])

  function cambiar(apply: () => void) {
    setLoading(true)
    apply()
  }

  function verCelda(cartel: FilaCalendario, periodo: string, ocupados: number) {
    if (ocupados === 0) return
    setElegida({ cartel, periodo })
    const desde = `${periodo}-01`
    void apiGet<Reserva[]>(`/api/reservas/reservas/?cartel=${cartel.id}`)
      .then((reservas) =>
        setDetalle(
          reservas.filter((r) => r.fecha_fin >= desde && r.fecha_inicio <= `${periodo}-31`),
        ),
      )
      .catch(() => setDetalle([]))
  }

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Disponibilidad</p>
          <h2>Calendario a futuro</h2>
          <p className="muted">
            Qué carteles están libres por mes. Tocá una celda ocupada para ver la campaña.
          </p>
        </div>
      </div>
      <div className="filters card">
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
      <div className="card table-wrap">
        {loading ? (
          <p className="empty">Cargando calendario…</p>
        ) : calendario.carteles.length === 0 ? (
          <p className="empty">No hay carteles para estos filtros.</p>
        ) : (
          <table aria-label="Calendario de disponibilidad">
            <thead>
              <tr>
                <th>Cartel</th>
                {calendario.periodos.map((periodo) => (
                  <th key={periodo.clave}>{periodo.etiqueta}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {calendario.carteles.map((cartel) => (
                <tr key={cartel.id}>
                  <td className="primary-cell">{cartel.nombre_visible}</td>
                  {cartel.celdas.map((celda) => {
                    const lleno = celda.ocupados >= cartel.capacidad
                    const estado = celda.ocupados === 0 ? 'libre' : lleno ? 'lleno' : 'parcial'
                    return (
                      <td key={celda.periodo}>
                        <button
                          className={`celda-${estado}`}
                          disabled={celda.ocupados === 0}
                          aria-label={`${cartel.nombre_visible} ${celda.periodo}: ${celda.ocupados} de ${cartel.capacidad}`}
                          onClick={() => verCelda(cartel, celda.periodo, celda.ocupados)}
                        >
                          {celda.ocupados}/{cartel.capacidad}
                        </button>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {elegida && (
        <div className="card section-gap">
          <div className="form-heading">
            <h3>
              {elegida.cartel.nombre_visible} · {elegida.periodo}
            </h3>
            <button className="button-ghost" onClick={() => setElegida(null)}>
              Cerrar
            </button>
          </div>
          {detalle.length === 0 ? (
            <p className="empty">Sin reservas en el período.</p>
          ) : (
            <ul>
              {detalle.map((reserva) => (
                <li key={reserva.id}>
                  {reserva.campania_nombre} — {reserva.nombre} (
                  {formatearFecha(reserva.fecha_inicio)} → {formatearFecha(reserva.fecha_fin)})
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </>
  )
}
