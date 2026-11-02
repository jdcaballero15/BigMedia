import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, apiWrite } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import type { Rubro } from './types'
import { usePuedeEditar } from '../../shared/sesion'
import MenuFila from '../../shared/MenuFila'

/** Un catálogo de nombres con baja lógica: rubros y grupos económicos tienen la misma forma. */
type Item = Pick<Rubro, 'id' | 'nombre' | 'activo'>

type Props = {
  /** Ruta de la colección, con barra final (por ejemplo `/api/clientes/rubros/`). */
  ruta: string
  /** Título en plural (por ejemplo «Rubros»). */
  titulo: string
  descripcion: string
  /** Nombre del ítem en singular y minúscula (por ejemplo «rubro»). */
  singular: string
  items: Item[]
  onChanged: () => void
}

export default function CatalogoAdmin({
  ruta,
  titulo,
  descripcion,
  singular,
  items,
  onChanged,
}: Props) {
  const encabezado = singular.charAt(0).toUpperCase() + singular.slice(1)
  const puedeEditar = usePuedeEditar()
  const [editing, setEditing] = useState<Item | 'new' | null>(null)
  const [nombre, setNombre] = useState('')
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  function openForm(item: Item | 'new') {
    setEditing(item)
    setNombre(item === 'new' ? '' : item.nombre)
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
      await apiWrite(nuevo ? ruta : `${ruta}${editing.id}/`, nuevo ? 'POST' : 'PATCH', {
        nombre: nombre.trim(),
      })
      setEditing(null)
      onChanged()
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
      setError(cause instanceof Error ? cause.message : `No se pudo guardar el ${singular}.`)
    } finally {
      setSaving(false)
    }
  }

  async function inactivate(item: Item) {
    if (!window.confirm(`¿Inactivar el ${singular} ${item.nombre}? Las marcas lo conservan.`))
      return
    try {
      await apiWrite(`${ruta}${item.id}/`, 'PATCH', { activo: false })
      onChanged()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : `No se pudo inactivar el ${singular}.`)
    }
  }

  return (
    <section aria-label={titulo}>
      <div className="section-heading">
        <div>
          <h3>{titulo}</h3>
          <p className="muted">{descripcion}</p>
        </div>
        {puedeEditar && (
          <button className="button-primary" onClick={() => openForm('new')}>
            Nuevo {singular}
          </button>
        )}
      </div>
      {editing !== null && (
        <form
          className="card edit-form"
          aria-label={`Formulario de ${singular}`}
          noValidate
          onSubmit={(event) => void save(event)}
        >
          <div className="form-heading">
            <h3>{editing === 'new' ? `Nuevo ${singular}` : `Renombrar ${singular}`}</h3>
            <button className="button-ghost" type="button" onClick={() => setEditing(null)}>
              Cancelar
            </button>
          </div>
          <div className="form-grid">
            <label>
              Nombre del {singular}
              <input value={nombre} onChange={(event) => setNombre(event.target.value)} required />
              <FieldErrors messages={errors.nombre} />
            </label>
          </div>
          <button type="submit" className="button-primary" disabled={saving}>
            {saving ? 'Guardando…' : `Guardar ${singular}`}
          </button>
        </form>
      )}
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div className="card table-wrap">
        {items.length === 0 ? (
          <p className="empty">Todavía no hay {titulo.toLowerCase()}.</p>
        ) : (
          <table aria-label={titulo}>
            <thead>
              <tr>
                <th>{encabezado}</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="primary-cell">{item.nombre}</td>
                  <td>{item.activo ? 'Activo' : 'Inactivo'}</td>
                  <td className="row-actions">
                    {puedeEditar && (
                      <button className="button-ghost" onClick={() => openForm(item)}>
                        Renombrar
                      </button>
                    )}
                    <MenuFila
                      acciones={[
                        item.activo && {
                          etiqueta: 'Inactivar',
                          onClick: () => void inactivate(item),
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
