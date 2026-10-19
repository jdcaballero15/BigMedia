import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { vigentes } from '../../shared/opciones'
import type { Cliente, Marca, Rubro } from './types'

export type MarcaInput = {
  nombre: string
  cliente: number | null
  rubro: number | null
  activo: boolean
}

type Props = {
  marca?: Marca | null
  clientes: Cliente[]
  rubros: Rubro[]
  onSave: (input: MarcaInput) => Promise<void>
  onCancel: () => void
}

export default function MarcaForm({ marca, clientes, rubros, onSave, onCancel }: Props) {
  const [nombre, setNombre] = useState(marca?.nombre ?? '')
  const [cliente, setCliente] = useState(String(marca?.cliente ?? ''))
  const [rubro, setRubro] = useState(String(marca?.rubro ?? ''))
  const [activo, setActivo] = useState(marca?.activo ?? true)
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [generalError, setGeneralError] = useState('')
  const [saving, setSaving] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors({})
    setGeneralError('')
    setSaving(true)
    try {
      await onSave({
        nombre: nombre.trim(),
        cliente: cliente ? Number(cliente) : null,
        rubro: rubro ? Number(rubro) : null,
        activo,
      })
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
      setGeneralError(cause instanceof Error ? cause.message : 'No se pudo guardar la marca.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      className="card edit-form"
      aria-label="Formulario de marca"
      noValidate
      onSubmit={(event) => void submit(event)}
    >
      <div className="form-heading">
        <h3>{marca ? 'Editar marca' : 'Nueva marca'}</h3>
        <button type="button" className="button-ghost" onClick={onCancel}>
          Cancelar
        </button>
      </div>
      <div className="form-grid">
        <label>
          Nombre
          <input value={nombre} onChange={(event) => setNombre(event.target.value)} required />
          <FieldErrors messages={errors.nombre} />
        </label>
        <label>
          Cliente
          <select value={cliente} onChange={(event) => setCliente(event.target.value)} required>
            <option value="">Seleccionar</option>
            {vigentes(clientes, marca?.cliente).map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre_visible}
                {item.activo ? '' : ' (inactivo)'}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.cliente} />
        </label>
        <label>
          Rubro
          <select value={rubro} onChange={(event) => setRubro(event.target.value)}>
            <option value="">Sin rubro</option>
            {vigentes(rubros, marca?.rubro).map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
                {item.activo ? '' : ' (inactivo)'}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.rubro} />
        </label>
        <label className="checkline">
          <input
            type="checkbox"
            checked={activo}
            onChange={(event) => setActivo(event.target.checked)}
          />
          Activa
        </label>
      </div>
      {generalError && (
        <p className="error" role="alert">
          {generalError}
        </p>
      )}
      <button type="submit" className="button-primary" disabled={saving}>
        {saving ? 'Guardando…' : 'Guardar marca'}
      </button>
    </form>
  )
}
