import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import type { Cartel, Catalogo, Estado, Formato, Proveedor } from './types'
import CartelForm from './CartelForm'
import type { CartelInput } from './CartelForm'
import { usePuedeEditar } from '../../shared/sesion'

type Catalogos = {
  formatos: Formato[]
  zonas: Catalogo[]
  estados: Estado[]
  proveedores: Proveedor[]
}

export default function CartelesPage() {
  const puedeEditar = usePuedeEditar()
  const [catalogos, setCatalogos] = useState<Catalogos>({
    formatos: [],
    zonas: [],
    estados: [],
    proveedores: [],
  })
  const [carteles, setCarteles] = useState<Cartel[]>([])
  const [zona, setZona] = useState('')
  const [formato, setFormato] = useState('')
  const [modalidad, setModalidad] = useState('')
  const [estado, setEstado] = useState('')
  const [q, setQ] = useState('')
  const [incluirBajas, setIncluirBajas] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState<Cartel | 'new' | null>(null)
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let active = true
    void Promise.all([
      apiGet<Formato[]>('/api/inventario/formatos/?incluir_inactivos=1'),
      apiGet<Catalogo[]>('/api/inventario/zonas/?incluir_inactivos=1'),
      apiGet<Estado[]>('/api/inventario/estados/?incluir_inactivos=1'),
      apiGet<Proveedor[]>('/api/inventario/proveedores/?incluir_inactivos=1'),
    ])
      .then(([formatos, zonas, estados, proveedores]) => {
        if (active) setCatalogos({ formatos, zonas, estados, proveedores })
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
    if (estado) params.set('estado', estado)
    if (q.trim()) params.set('q', q.trim())
    if (incluirBajas) params.set('incluir_bajas', '1')
    const suffix = params.toString() ? `?${params}` : ''
    void apiGet<Cartel[]>(`/api/inventario/carteles/${suffix}`)
      .then((rows) => {
        if (active) {
          setCarteles(rows)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los carteles.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [zona, formato, modalidad, estado, q, incluirBajas, revision])

  async function saveCartel(input: CartelInput) {
    if (editing === null) return
    const path =
      editing === 'new' ? '/api/inventario/carteles/' : `/api/inventario/carteles/${editing.id}/`
    await apiWrite(path, editing === 'new' ? 'POST' : 'PATCH', input)
    setEditing(null)
    setRevision((current) => current + 1)
  }

  async function darDeBaja(cartel: Cartel) {
    const baja = catalogos.estados.find((item) => item.es_baja)
    if (!baja) {
      setError('No existe el estado De baja.')
      return
    }
    if (
      !window.confirm(`¿Dar de baja ${cartel.nombre_visible}? El registro seguirá en el historial.`)
    )
      return
    try {
      await apiWrite(`/api/inventario/carteles/${cartel.id}/`, 'PATCH', { estado: baja.id })
      setRevision((current) => current + 1)
    } catch {
      setError('No se pudo dar de baja el cartel.')
    }
  }

  return (
    <section className="inventory-page">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Inventario</p>
          <h2>Carteles</h2>
          <p className="muted">Consultá y filtrá los espacios disponibles para vender.</p>
        </div>
        {puedeEditar && (
          <button className="button-primary" onClick={() => setEditing('new')}>
            Nuevo cartel
          </button>
        )}
      </div>
      {editing !== null && (
        <CartelForm
          key={editing === 'new' ? 'new' : editing.id}
          cartel={editing === 'new' ? null : editing}
          formatos={catalogos.formatos}
          zonas={catalogos.zonas}
          proveedores={catalogos.proveedores}
          estados={catalogos.estados}
          onSave={saveCartel}
          onCancel={() => setEditing(null)}
        />
      )}
      <div className="filters card">
        <label>
          Departamento
          <select
            value={zona}
            onChange={(event) => {
              setLoading(true)
              setZona(event.target.value)
            }}
            aria-label="Zona"
          >
            <option value="">Todos</option>
            {catalogos.zonas.map((item) => (
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
            onChange={(event) => {
              setLoading(true)
              setFormato(event.target.value)
            }}
          >
            <option value="">Todos</option>
            {catalogos.formatos.map((item) => (
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
            onChange={(event) => {
              setLoading(true)
              setModalidad(event.target.value)
            }}
          >
            <option value="">Todas</option>
            <option value="fija">Fija</option>
            <option value="digital">Digital</option>
          </select>
        </label>
        <label>
          Estado
          <select
            value={estado}
            onChange={(event) => {
              setLoading(true)
              setEstado(event.target.value)
            }}
          >
            <option value="">Todos</option>
            {catalogos.estados.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
              </option>
            ))}
          </select>
        </label>
        <label>
          Dirección
          <input
            value={q}
            onChange={(event) => {
              setLoading(true)
              setQ(event.target.value)
            }}
            placeholder="Buscar dirección"
          />
        </label>
        <label className="checkline">
          <input
            type="checkbox"
            checked={incluirBajas}
            onChange={(event) => {
              setLoading(true)
              setIncluirBajas(event.target.checked)
            }}
          />
          Incluir bajas
        </label>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="card table-wrap">
        {loading ? (
          <p className="empty">Cargando carteles…</p>
        ) : carteles.length === 0 ? (
          <p className="empty">No hay carteles para estos filtros.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Cartel</th>
                <th>Formato</th>
                <th>Zona</th>
                <th>Proveedor</th>
                <th>Estado</th>
                <th>Capacidad</th>
                <th>Tarifa de lista</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {carteles.map((item) => (
                <tr key={item.id}>
                  <td className="primary-cell">{item.nombre_visible}</td>
                  <td>{item.formato_nombre}</td>
                  <td>{item.zona_nombre}</td>
                  <td>{item.proveedor_nombre ?? '—'}</td>
                  <td>{item.estado_nombre}</td>
                  <td>{item.capacidad}</td>
                  <td>{item.tarifa_lista ?? 'Sin tarifa'}</td>
                  <td className="row-actions">
                    {puedeEditar && (
                      <button className="button-ghost" onClick={() => setEditing(item)}>
                        Editar
                      </button>
                    )}
                    {puedeEditar &&
                      !catalogos.estados.find((state) => state.id === item.estado)?.es_baja && (
                        <button className="button-ghost" onClick={() => void darDeBaja(item)}>
                          Dar de baja
                        </button>
                      )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}
