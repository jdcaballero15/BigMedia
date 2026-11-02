import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import type { Contacto } from './types'

export type ContactoInput = {
  nombre: string
  cargo: string
  correo: string
  telefono: string
  notas: string
  principal: boolean
}

type Props = {
  contacto?: Contacto | null
  onSave: (input: ContactoInput) => Promise<void>
  onCancel: () => void
}

export default function ContactoForm({ contacto, onSave, onCancel }: Props) {
  const [nombre, setNombre] = useState(contacto?.nombre ?? '')
  const [cargo, setCargo] = useState(contacto?.cargo ?? '')
  const [correo, setCorreo] = useState(contacto?.correo ?? '')
  const [telefono, setTelefono] = useState(contacto?.telefono ?? '')
  const [notas, setNotas] = useState(contacto?.notas ?? '')
  const [principal, setPrincipal] = useState(contacto?.principal ?? false)
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
        cargo: cargo.trim(),
        correo: correo.trim(),
        telefono: telefono.trim(),
        notas: notas.trim(),
        principal,
      })
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
      setGeneralError(cause instanceof Error ? cause.message : 'No se pudo guardar el contacto.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      className="card edit-form"
      aria-label="Formulario de contacto"
      noValidate
      onSubmit={(event) => void submit(event)}
    >
      <div className="form-heading">
        <h3>{contacto ? 'Editar contacto' : 'Nuevo contacto'}</h3>
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
          Cargo o área
          <input value={cargo} onChange={(event) => setCargo(event.target.value)} />
          <FieldErrors messages={errors.cargo} />
        </label>
        <label>
          Correo
          <input type="email" value={correo} onChange={(event) => setCorreo(event.target.value)} />
          <FieldErrors messages={errors.correo} />
        </label>
        <label>
          Teléfono
          <input value={telefono} onChange={(event) => setTelefono(event.target.value)} />
          <FieldErrors messages={errors.telefono} />
        </label>
        <label>
          Notas
          <textarea value={notas} onChange={(event) => setNotas(event.target.value)} />
          <FieldErrors messages={errors.notas} />
        </label>
        {(contacto?.activo ?? true) && (
          <label className="checkline">
            <input
              type="checkbox"
              checked={principal}
              onChange={(event) => setPrincipal(event.target.checked)}
            />
            Contacto principal
          </label>
        )}
      </div>
      <FieldErrors messages={errors.principal} />
      {generalError && (
        <p className="error" role="alert">
          {generalError}
        </p>
      )}
      <button type="submit" className="button-primary" disabled={saving}>
        {saving ? 'Guardando…' : 'Guardar contacto'}
      </button>
    </form>
  )
}
