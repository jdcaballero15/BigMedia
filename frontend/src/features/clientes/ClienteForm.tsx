import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { TIPOS_CLIENTE } from './types'
import type { Cliente, TipoCliente } from './types'

export type ClienteInput = {
  nombre: string
  razon_social: string
  cuit: string
  tipo?: TipoCliente
  telefono: string
  correo: string
  activo: boolean
}

type Props = {
  cliente?: Cliente | null
  onSave: (input: ClienteInput) => Promise<void>
  onCancel: () => void
}

export default function ClienteForm({ cliente, onSave, onCancel }: Props) {
  const [nombre, setNombre] = useState(cliente?.nombre ?? '')
  const [razonSocial, setRazonSocial] = useState(cliente?.razon_social ?? '')
  const [cuit, setCuit] = useState(cliente?.cuit ?? '')
  const [tipo, setTipo] = useState<TipoCliente | ''>(cliente?.tipo ?? '')
  const [telefono, setTelefono] = useState(cliente?.telefono ?? '')
  const [correo, setCorreo] = useState(cliente?.correo ?? '')
  const [activo, setActivo] = useState(cliente?.activo ?? true)
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
        razon_social: razonSocial.trim(),
        cuit: cuit.trim(),
        // Sin tipo elegido no se envía: la API responde con su mensaje de obligatorio.
        ...(tipo ? { tipo } : {}),
        telefono: telefono.trim(),
        correo: correo.trim(),
        activo,
      })
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
      setGeneralError(cause instanceof Error ? cause.message : 'No se pudo guardar el cliente.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      className="card edit-form"
      aria-label="Formulario de cliente"
      noValidate
      onSubmit={(event) => void submit(event)}
    >
      <div className="form-heading">
        <h3>{cliente ? 'Editar cliente' : 'Nuevo cliente'}</h3>
        <button type="button" className="button-ghost" onClick={onCancel}>
          Cancelar
        </button>
      </div>
      <div className="form-grid">
        <label>
          Nombre de fantasía
          <input value={nombre} onChange={(event) => setNombre(event.target.value)} required />
          <FieldErrors messages={errors.nombre} />
        </label>
        <label>
          Razón social
          <input
            value={razonSocial}
            onChange={(event) => setRazonSocial(event.target.value)}
            required
          />
          <FieldErrors messages={errors.razon_social} />
        </label>
        <label>
          CUIT
          <input
            value={cuit}
            onChange={(event) => setCuit(event.target.value)}
            placeholder="20-12345678-6"
            inputMode="numeric"
          />
          <FieldErrors messages={errors.cuit} />
        </label>
        <label>
          Tipo
          <select
            value={tipo}
            onChange={(event) => setTipo(event.target.value as TipoCliente | '')}
            required
          >
            <option value="">Seleccionar</option>
            {TIPOS_CLIENTE.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.tipo} />
        </label>
        <label>
          Teléfono
          <input value={telefono} onChange={(event) => setTelefono(event.target.value)} />
          <FieldErrors messages={errors.telefono} />
        </label>
        <label>
          Correo
          <input type="email" value={correo} onChange={(event) => setCorreo(event.target.value)} />
          <FieldErrors messages={errors.correo} />
        </label>
        <label className="checkline">
          <input
            type="checkbox"
            checked={activo}
            onChange={(event) => setActivo(event.target.checked)}
          />
          Activo
        </label>
      </div>
      {!cliente && tipo === 'directo' && (
        <p className="muted">Al guardarlo se crea también una marca con su nombre.</p>
      )}
      {generalError && (
        <p className="error" role="alert">
          {generalError}
        </p>
      )}
      <button type="submit" className="button-primary" disabled={saving}>
        {saving ? 'Guardando…' : 'Guardar cliente'}
      </button>
    </form>
  )
}
