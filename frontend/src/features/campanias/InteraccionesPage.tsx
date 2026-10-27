import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import { usePuedeEditar } from '../../shared/sesion'
import type { Cliente } from '../clientes/types'
import InteraccionForm from './InteraccionForm'
import type { InteraccionInput } from './InteraccionForm'
import { TablaInteracciones } from './InteraccionesLista'
import type { Interaccion } from './types'

const URL = '/api/campanias/interacciones/'

/** Sección Interacciones del grupo Comercial (HU-020). */
export default function InteraccionesPage() {
  const puedeEditar = usePuedeEditar()
  const [interacciones, setInteracciones] = useState<Interaccion[]>([])
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [cliente, setCliente] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState<Interaccion | 'new' | null>(null)
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let active = true
    void apiGet<Cliente[]>('/api/clientes/clientes/?incluir_inactivos=1')
      .then((rows) => {
        if (active) setClientes(rows)
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los clientes.')
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    const suffix = cliente ? `?cliente=${cliente}` : ''
    void apiGet<Interaccion[]>(`${URL}${suffix}`)
      .then((rows) => {
        if (active) {
          setInteracciones(rows)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar las interacciones.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [cliente, revision])

  async function guardar(input: InteraccionInput) {
    if (editing === null) return
    if (editing === 'new') await apiWrite(URL, 'POST', input)
    else await apiWrite(`${URL}${editing.id}/`, 'PATCH', input)
    setEditing(null)
    setRevision((current) => current + 1)
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Comercial</p>
          <h2>Interacciones</h2>
          <p className="muted">Reuniones y llamadas con clientes, para no perder el rastro.</p>
        </div>
        {puedeEditar && (
          <button className="button-primary" onClick={() => setEditing('new')}>
            Nueva interacción
          </button>
        )}
      </div>
      {editing !== null && (
        <InteraccionForm
          key={editing === 'new' ? 'nueva' : editing.id}
          interaccion={editing === 'new' ? null : editing}
          clientes={clientes}
          onSave={guardar}
          onCancel={() => setEditing(null)}
        />
      )}
      <div className="filters card" role="search" aria-label="Filtros de interacciones">
        <label>
          Cliente
          <select
            value={cliente}
            onChange={(event) => {
              setLoading(true)
              setCliente(event.target.value)
            }}
          >
            <option value="">Todos</option>
            {clientes.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre_visible}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="card table-wrap section-gap">
        {loading ? (
          <p className="empty">Cargando interacciones…</p>
        ) : interacciones.length === 0 ? (
          <p className="empty">No hay interacciones para este filtro.</p>
        ) : (
          <TablaInteracciones
            filas={interacciones}
            onEditar={puedeEditar ? (fila) => setEditing(fila) : undefined}
          />
        )}
      </div>
    </section>
  )
}
