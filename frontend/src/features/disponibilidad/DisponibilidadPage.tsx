import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import type { Catalogo, Formato } from '../inventario/types'
import type { OcupacionCartel } from './types'

type Ocupacion = '' | 'libres' | 'ocupados'

export default function DisponibilidadPage() {
  const [filas, setFilas] = useState<OcupacionCartel[]>([])
  const [zonas, setZonas] = useState<Catalogo[]>([])
  const [formatos, setFormatos] = useState<Formato[]>([])
  const [zona, setZona] = useState('')
  const [formato, setFormato] = useState('')
  const [modalidad, setModalidad] = useState('')
  const [ocupacion, setOcupacion] = useState<Ocupacion>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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
    if (ocupacion) params.set('ocupacion', ocupacion)
    const suffix = params.toString() ? `?${params}` : ''
    void apiGet<OcupacionCartel[]>(`/api/reservas/disponibilidad/${suffix}`)
      .then((rows) => {
        if (active) {
          setFilas(rows)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudo cargar la disponibilidad.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [zona, formato, modalidad, ocupacion])

  function cambiar(apply: () => void) {
    setLoading(true)
    apply()
  }

  return (
    <section className="inventory-page">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Disponibilidad</p>
          <h2>Ocupación de hoy</h2>
          <p className="muted">Qué carteles están libres u ocupados en este momento.</p>
        </div>
        <div className="row-actions" role="group" aria-label="Accesos rápidos">
          <button
            className={ocupacion === '' ? 'active' : 'button-ghost'}
            onClick={() => cambiar(() => setOcupacion(''))}
          >
            Todos
          </button>
          <button
            className={ocupacion === 'libres' ? 'active' : 'button-ghost'}
            onClick={() => cambiar(() => setOcupacion('libres'))}
          >
            Libres
          </button>
          <button
            className={ocupacion === 'ocupados' ? 'active' : 'button-ghost'}
            onClick={() => cambiar(() => setOcupacion('ocupados'))}
          >
            Ocupados
          </button>
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
          <p className="empty">Cargando disponibilidad…</p>
        ) : filas.length === 0 ? (
          <p className="empty">No hay carteles para estos filtros.</p>
        ) : (
          <table aria-label="Disponibilidad">
            <thead>
              <tr>
                <th>Cartel</th>
                <th>Formato</th>
                <th>Zona</th>
                <th>Ocupación</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((item) => (
                <tr key={item.id}>
                  <td className="primary-cell">{item.nombre_visible}</td>
                  <td>{item.formato_nombre}</td>
                  <td>{item.zona_nombre}</td>
                  <td>
                    {item.ocupados} de {item.capacidad}
                  </td>
                  <td>{item.libre ? 'Libre' : 'Ocupado'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}
