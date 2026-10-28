import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, apiWrite } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import type { Rubro } from './types'
import { usePuedeEditar } from '../../shared/sesion'
import MenuFila from '../../shared/MenuFila'

type Props = {
  rubros: Rubro[]
  onChanged: () => void
}

export default function RubrosAdmin({ rubros, onChanged }: Props) {
  const puedeEditar = usePuedeEditar()
  const [editing, setEditing] = useState<Rubro | 'new' | null>(null)
  const [nombre, setNombre] = useState('')
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  function openForm(rubro: Rubro | 'new') {
    setEditing(rubro)
    setNombre(rubro === 'new' ? '' : rubro.nombre)
    setErrors({})
    setError('')
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (editing === null) return
    const nuevo = editing === 'new'
    setSaving(true)
    setErrors({})
    setError('')
    try {
      await apiWrite(
        nuevo ? '/api/clientes/rubros/' : `/api/clientes/rubros/${editing.id}/`,
        nuevo ? 'POST' : 'PATCH',
        { nombre: nombre.trim() },
      )
      setEditing(null)
      onChanged()
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
      setError(cause instanceof Error ? cause.message : 'No se pudo guardar el rubro.')
    } finally {
      setSaving(false)
    }
  }

  async function inactivate(rubro: Rubro) {
    if (!window.confirm(`¿Inactivar el rubro ${rubro.nombre}? Las marcas lo conservan.`)) return
    try {
      await apiWrite(`/api/clientes/rubros/${rubro.id}/`, 'PATCH', { activo: false })
      onChanged()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudo inactivar el rubro.')
    }
  }

  return (
    <section aria-label="Rubros" className="rubros-admin">
      <div className="section-heading">
        <div>
          <h3>Rubros</h3>
          <p className="muted">Catálogo para clasificar las marcas.</p>
        </div>
        {puedeEditar && (
          <button className="button-primary" onClick={() => openForm('new')}>
            Nuevo rubro
          </button>
        )}
      </div>
      {editing !== null && (
        <form
          className="card edit-form"
          aria-label="Formulario de rubro"
          noValidate
          onSubmit={(event) => void save(event)}
        >
          <div className="form-heading">
            <h3>{editing === 'new' ? 'Nuevo rubro' : 'Renombrar rubro'}</h3>
            <button className="button-ghost" type="button" onClick={() => setEditing(null)}>
              Cancelar
            </button>
          </div>
          <div className="form-grid">
            <label>
              Nombre del rubro
              <input value={nombre} onChange={(event) => setNombre(event.target.value)} required />
              <FieldErrors messages={errors.nombre} />
            </label>
          </div>
          <button type="submit" className="button-primary" disabled={saving}>
            {saving ? 'Guardando…' : 'Guardar rubro'}
          </button>
        </form>
      )}
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div className="card table-wrap">
        {rubros.length === 0 ? (
          <p className="empty">Todavía no hay rubros.</p>
        ) : (
          <table aria-label="Rubros">
            <thead>
              <tr>
                <th>Rubro</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {rubros.map((rubro) => (
                <tr key={rubro.id}>
                  <td className="primary-cell">{rubro.nombre}</td>
                  <td>{rubro.activo ? 'Activo' : 'Inactivo'}</td>
                  <td className="row-actions">
                    {puedeEditar && (
                      <button className="button-ghost" onClick={() => openForm(rubro)}>
                        Renombrar
                      </button>
                    )}
                    <MenuFila
                      acciones={[
                        rubro.activo && {
                          etiqueta: 'Inactivar',
                          onClick: () => void inactivate(rubro),
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
