import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import ClienteForm from './ClienteForm'
import ContactosDelCliente from './ContactosDelCliente'
import type { ClienteInput } from './ClienteForm'
import { TIPOS_CLIENTE } from './types'
import type { Cliente, Marca } from './types'
import { usePuedeEditar } from '../../shared/sesion'

type Ficha = { cliente: Cliente; recienCreado: boolean }
type MarcasCargadas = { estado: 'cargando' | 'error' | 'listo'; marcas: Marca[] }

function MarcasDelCliente({
  ficha,
  revision,
  onClose,
}: {
  ficha: Ficha
  revision: number
  onClose: () => void
}) {
  const { cliente, recienCreado } = ficha
  const [carga, setCarga] = useState<MarcasCargadas>({ estado: 'cargando', marcas: [] })

  useEffect(() => {
    let active = true
    void apiGet<Marca[]>(`/api/clientes/marcas/?cliente=${cliente.id}&incluir_inactivos=1`)
      .then((marcas) => {
        if (active) setCarga({ estado: 'listo', marcas })
      })
      .catch(() => {
        if (active) setCarga({ estado: 'error', marcas: [] })
      })
    return () => {
      active = false
    }
  }, [cliente.id, revision])

  const titulo = `Marcas de ${cliente.nombre_visible}`
  return (
    <section className="card edit-form" aria-label={titulo}>
      <div className="form-heading">
        <h3>{titulo}</h3>
        <button type="button" className="button-ghost" onClick={onClose}>
          Cerrar
        </button>
      </div>
      {/* Un cliente recién creado solo tiene marcas si la API creó su homónima. */}
      {recienCreado && carga.marcas.length > 0 && (
        <p className="notice" role="status">
          Se creó la marca «{carga.marcas[0].nombre}» para este cliente directo.
        </p>
      )}
      {carga.estado === 'cargando' ? (
        <p className="empty">Cargando marcas…</p>
      ) : carga.estado === 'error' ? (
        <p className="error" role="alert">
          No se pudieron cargar las marcas.
        </p>
      ) : carga.marcas.length === 0 ? (
        <p className="empty">Este cliente todavía no tiene marcas.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Marca</th>
              <th>Rubro</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {carga.marcas.map((marca) => (
              <tr key={marca.id}>
                <td className="primary-cell">{marca.nombre}</td>
                <td>{marca.rubro_nombre ?? 'Sin rubro'}</td>
                <td>{marca.activo ? 'Activa' : 'Inactiva'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

export default function ClientesPage() {
  const puedeEditar = usePuedeEditar()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [q, setQ] = useState('')
  const [tipo, setTipo] = useState('')
  const [incluirInactivos, setIncluirInactivos] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState<Cliente | 'new' | null>(null)
  const [ficha, setFicha] = useState<Ficha | null>(null)
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let active = true
    const params = new URLSearchParams()
    if (q.trim()) params.set('q', q.trim())
    if (tipo) params.set('tipo', tipo)
    if (incluirInactivos) params.set('incluir_inactivos', '1')
    const suffix = params.toString() ? `?${params}` : ''
    void apiGet<Cliente[]>(`/api/clientes/clientes/${suffix}`)
      .then((rows) => {
        if (active) {
          setClientes(rows)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los clientes.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [q, tipo, incluirInactivos, revision])

  function abrirEdicion(cliente: Cliente) {
    setEditing(cliente)
    setFicha({ cliente, recienCreado: false })
  }

  async function saveCliente(input: ClienteInput) {
    if (editing === null) return
    const nuevo = editing === 'new'
    const path = nuevo ? '/api/clientes/clientes/' : `/api/clientes/clientes/${editing.id}/`
    const guardado = await apiWrite<Cliente>(path, nuevo ? 'POST' : 'PATCH', input)
    setEditing(null)
    setFicha({ cliente: guardado, recienCreado: nuevo })
    setRevision((current) => current + 1)
  }

  async function inactivar(cliente: Cliente) {
    if (!window.confirm(`¿Inactivar a ${cliente.nombre_visible}? Sus datos y marcas se conservan.`))
      return
    try {
      await apiWrite(`/api/clientes/clientes/${cliente.id}/`, 'PATCH', { activo: false })
      setRevision((current) => current + 1)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudo inactivar el cliente.')
    }
  }

  function cambiarFiltro(apply: () => void) {
    setLoading(true)
    apply()
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Clientes y marcas</p>
          <h2>Clientes</h2>
          <p className="muted">Cargá y buscá a quienes les facturás, y consultá sus marcas.</p>
        </div>
        {puedeEditar && (
          <button className="button-primary" onClick={() => setEditing('new')}>
            Nuevo cliente
          </button>
        )}
      </div>
      {editing !== null && (
        <ClienteForm
          key={editing === 'new' ? 'nuevo' : `formulario-${editing.id}`}
          cliente={editing === 'new' ? null : editing}
          onSave={saveCliente}
          onCancel={() => setEditing(null)}
        />
      )}
      {ficha !== null && (
        <MarcasDelCliente
          key={`ficha-${ficha.cliente.id}`}
          ficha={ficha}
          revision={revision}
          onClose={() => setFicha(null)}
        />
      )}
      {/* Solo el intermediario formal tiene contactos múltiples (HU-068, RN-015). */}
      {ficha !== null && ficha.cliente.tipo === 'intermediario_formal' && (
        <ContactosDelCliente key={`contactos-${ficha.cliente.id}`} cliente={ficha.cliente} />
      )}
      <div className="filters card" role="search" aria-label="Filtros de clientes">
        <label>
          Buscar
          <input
            value={q}
            onChange={(event) => cambiarFiltro(() => setQ(event.target.value))}
            placeholder="Nombre o razón social"
          />
        </label>
        <label>
          Tipo de cliente
          <select
            value={tipo}
            onChange={(event) => cambiarFiltro(() => setTipo(event.target.value))}
          >
            <option value="">Todos</option>
            {TIPOS_CLIENTE.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="checkline">
          <input
            type="checkbox"
            checked={incluirInactivos}
            onChange={(event) => cambiarFiltro(() => setIncluirInactivos(event.target.checked))}
          />
          Incluir inactivos
        </label>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="card table-wrap">
        {loading ? (
          <p className="empty">Cargando clientes…</p>
        ) : clientes.length === 0 ? (
          <p className="empty">No hay clientes para estos filtros.</p>
        ) : (
          <table aria-label="Clientes">
            <thead>
              <tr>
                <th>Cliente</th>
                <th>CUIT</th>
                <th>Tipo</th>
                <th>Teléfono</th>
                <th>Correo</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {clientes.map((item) => (
                <tr key={item.id}>
                  <td className="primary-cell">
                    {item.nombre_visible}
                    {item.razon_social && (
                      <small className="cell-detail">{item.razon_social}</small>
                    )}
                  </td>
                  <td>{item.cuit || '—'}</td>
                  <td>{item.tipo_nombre || 'Sin tipo'}</td>
                  <td>{item.telefono || '—'}</td>
                  <td>{item.correo || '—'}</td>
                  <td>{item.activo ? 'Activo' : 'Inactivo'}</td>
                  <td className="row-actions">
                    <button
                      className="button-ghost"
                      onClick={() => setFicha({ cliente: item, recienCreado: false })}
                    >
                      Ver marcas
                    </button>
                    {puedeEditar && (
                      <button className="button-ghost" onClick={() => abrirEdicion(item)}>
                        Editar
                      </button>
                    )}
                    {puedeEditar && item.activo && (
                      <button className="button-ghost" onClick={() => void inactivar(item)}>
                        Inactivar
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
