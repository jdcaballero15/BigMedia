import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import CampaniasLista from '../campanias/CampaniasLista'
import MarcaForm from './MarcaForm'
import type { MarcaInput } from './MarcaForm'
import RubrosAdmin from './RubrosAdmin'
import type { Cliente, Marca, Rubro } from './types'
import { usePuedeEditar } from '../../shared/sesion'
import MenuFila from '../../shared/MenuFila'

const ERROR_RUBROS = 'No se pudieron cargar los rubros.'

/** Ficha de una marca: todas sus campañas, sin importar quién las pagó (HU-022 criterio 1). */
function FichaMarca({ marca, onClose }: { marca: Marca; onClose: () => void }) {
  const titulo = `Ficha de ${marca.nombre}`
  return (
    <section className="card edit-form" aria-label={titulo}>
      <div className="form-heading">
        <div>
          <h3>{titulo}</h3>
          <p className="muted">
            {marca.cliente_nombre} · {marca.rubro_nombre ?? 'Sin rubro'} ·{' '}
            {marca.activo ? 'Activa' : 'Inactiva'}
          </p>
        </div>
        <button type="button" className="button-ghost" onClick={onClose}>
          Cerrar
        </button>
      </div>
      <CampaniasLista
        filtro={{ marca: marca.id }}
        titulo={`Campañas de ${marca.nombre}`}
        ocultar="marca"
      />
    </section>
  )
}

export default function MarcasPage() {
  const puedeEditar = usePuedeEditar()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [rubros, setRubros] = useState<Rubro[]>([])
  const [marcas, setMarcas] = useState<Marca[]>([])
  const [cliente, setCliente] = useState('')
  const [rubro, setRubro] = useState('')
  const [q, setQ] = useState('')
  const [incluirInactivas, setIncluirInactivas] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [errorCatalogos, setErrorCatalogos] = useState('')
  const [editing, setEditing] = useState<Marca | 'new' | null>(null)
  const [ficha, setFicha] = useState<Marca | null>(null)
  const [revision, setRevision] = useState(0)
  const [revisionRubros, setRevisionRubros] = useState(0)

  useEffect(() => {
    let active = true
    // Trae también los inactivos: el formulario los oculta salvo el ya asignado a la marca.
    void apiGet<Cliente[]>('/api/clientes/clientes/?incluir_inactivos=1')
      .then((rows) => {
        if (active) setClientes(rows)
      })
      .catch(() => {
        if (active) setErrorCatalogos('No se pudieron cargar los clientes.')
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    void apiGet<Rubro[]>('/api/clientes/rubros/?incluir_inactivos=1')
      .then((rows) => {
        if (!active) return
        setRubros(rows)
        // Solo limpia su propio error: el de clientes se conserva.
        setErrorCatalogos((actual) => (actual === ERROR_RUBROS ? '' : actual))
      })
      .catch(() => {
        if (active) setErrorCatalogos(ERROR_RUBROS)
      })
    return () => {
      active = false
    }
  }, [revisionRubros])

  useEffect(() => {
    let active = true
    const params = new URLSearchParams()
    if (cliente) params.set('cliente', cliente)
    if (rubro) params.set('rubro', rubro)
    if (q.trim()) params.set('q', q.trim())
    if (incluirInactivas) params.set('incluir_inactivos', '1')
    const suffix = params.toString() ? `?${params}` : ''
    void apiGet<Marca[]>(`/api/clientes/marcas/${suffix}`)
      .then((rows) => {
        if (active) {
          setMarcas(rows)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar las marcas.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [cliente, rubro, q, incluirInactivas, revision, revisionRubros])

  async function saveMarca(input: MarcaInput) {
    if (editing === null) return
    const path = editing === 'new' ? '/api/clientes/marcas/' : `/api/clientes/marcas/${editing.id}/`
    await apiWrite(path, editing === 'new' ? 'POST' : 'PATCH', input)
    setEditing(null)
    setRevision((current) => current + 1)
  }

  async function inactivar(marca: Marca) {
    if (!window.confirm(`¿Inactivar la marca ${marca.nombre}? Seguirá en el historial.`)) return
    try {
      await apiWrite(`/api/clientes/marcas/${marca.id}/`, 'PATCH', { activo: false })
      setRevision((current) => current + 1)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudo inactivar la marca.')
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
          <h2>Marcas</h2>
          <p className="muted">Administrá quién se anuncia y qué cliente le factura.</p>
        </div>
        {puedeEditar && (
          <button className="button-primary" onClick={() => setEditing('new')}>
            Nueva marca
          </button>
        )}
      </div>
      {editing !== null && (
        <MarcaForm
          key={editing === 'new' ? 'new' : editing.id}
          marca={editing === 'new' ? null : editing}
          clientes={clientes}
          rubros={rubros}
          onSave={saveMarca}
          onCancel={() => setEditing(null)}
        />
      )}
      {ficha !== null && <FichaMarca key={ficha.id} marca={ficha} onClose={() => setFicha(null)} />}
      <div className="filters card" role="search" aria-label="Filtros de marcas">
        <label>
          Cliente
          <select
            value={cliente}
            onChange={(event) => cambiarFiltro(() => setCliente(event.target.value))}
          >
            <option value="">Todos</option>
            {clientes.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre_visible}
                {item.activo ? '' : ' (inactivo)'}
              </option>
            ))}
          </select>
        </label>
        <label>
          Rubro
          <select
            value={rubro}
            onChange={(event) => cambiarFiltro(() => setRubro(event.target.value))}
          >
            <option value="">Todos</option>
            {rubros.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
                {item.activo ? '' : ' (inactivo)'}
              </option>
            ))}
          </select>
        </label>
        <label>
          Buscar
          <input
            value={q}
            onChange={(event) => cambiarFiltro(() => setQ(event.target.value))}
            placeholder="Nombre de la marca"
          />
        </label>
        <label className="checkline">
          <input
            type="checkbox"
            checked={incluirInactivas}
            onChange={(event) => cambiarFiltro(() => setIncluirInactivas(event.target.checked))}
          />
          Incluir inactivas
        </label>
      </div>
      {errorCatalogos && (
        <p className="error" role="alert">
          {errorCatalogos}
        </p>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="card table-wrap section-gap">
        {loading ? (
          <p className="empty">Cargando marcas…</p>
        ) : marcas.length === 0 ? (
          <p className="empty">No hay marcas para estos filtros.</p>
        ) : (
          <table aria-label="Marcas">
            <thead>
              <tr>
                <th>Marca</th>
                <th>Cliente</th>
                <th>Rubro</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {marcas.map((item) => (
                <tr key={item.id}>
                  <td className="primary-cell">{item.nombre}</td>
                  <td>{item.cliente_nombre}</td>
                  <td>{item.rubro_nombre ?? 'Sin rubro'}</td>
                  <td>{item.activo ? 'Activa' : 'Inactiva'}</td>
                  <td className="row-actions">
                    <button className="button-ghost" onClick={() => setFicha(item)}>
                      Ver ficha
                    </button>
                    <MenuFila
                      acciones={[
                        { etiqueta: 'Editar', onClick: () => setEditing(item), edicion: true },
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
      <RubrosAdmin rubros={rubros} onChanged={() => setRevisionRubros((current) => current + 1)} />
    </section>
  )
}
