import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import ClienteForm from './ClienteForm'
import FichaCliente from './FichaCliente'
import type { Ficha } from './FichaCliente'
import type { ClienteInput } from './ClienteForm'
import { TIPOS_CLIENTE } from './types'
import type { Cliente } from './types'
import { usePuedeEditar } from '../../shared/sesion'
import MenuFila from '../../shared/MenuFila'

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

  const formulario = editing !== null && (
    <ClienteForm
      key={editing === 'new' ? 'nuevo' : `formulario-${editing.id}`}
      cliente={editing === 'new' ? null : editing}
      onSave={saveCliente}
      onCancel={() => setEditing(null)}
    />
  )

  if (ficha !== null)
    return (
      <>
        {formulario}
        <FichaCliente
          key={ficha.cliente.id}
          ficha={ficha}
          revision={revision}
          onVolver={() => {
            setEditing(null)
            setFicha(null)
          }}
          onEditar={puedeEditar ? () => abrirEdicion(ficha.cliente) : undefined}
        />
      </>
    )

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
      {formulario}
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
                <th className="col-secundaria">Teléfono</th>
                <th className="col-secundaria">Correo</th>
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
                  <td className="col-secundaria">{item.telefono || '—'}</td>
                  <td className="col-secundaria">{item.correo || '—'}</td>
                  <td>{item.activo ? 'Activo' : 'Inactivo'}</td>
                  <td className="row-actions">
                    <button
                      className="button-ghost"
                      onClick={() => setFicha({ cliente: item, recienCreado: false })}
                    >
                      Ver ficha
                    </button>
                    <MenuFila
                      acciones={[
                        { etiqueta: 'Editar', onClick: () => abrirEdicion(item), edicion: true },
                        item.activo && {
                          etiqueta: 'Inactivar',
                          onClick: () => void inactivar(item),
                          edicion: true,
                        },
                      ]}
                    />
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
