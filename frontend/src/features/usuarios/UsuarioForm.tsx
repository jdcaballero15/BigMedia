import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import type { Rol } from '../../shared/sesion'
import { ETIQUETAS_ROL } from './types'
import type { Usuario } from './types'

export type UsuarioInput = {
  username?: string
  first_name: string
  last_name: string
  email: string
  rol: Rol
  es_gerencia: boolean
}

type Props = {
  usuario?: Usuario | null
  onSave: (input: UsuarioInput) => Promise<void>
  onCancel: () => void
}

export default function UsuarioForm({ usuario, onSave, onCancel }: Props) {
  const [username, setUsername] = useState(usuario?.username ?? '')
  const [firstName, setFirstName] = useState(usuario?.first_name ?? '')
  const [lastName, setLastName] = useState(usuario?.last_name ?? '')
  const [email, setEmail] = useState(usuario?.email ?? '')
  const [rol, setRol] = useState<Rol>(usuario?.rol ?? 'operativo')
  const [esGerencia, setEsGerencia] = useState(usuario?.es_gerencia ?? false)
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [generalError, setGeneralError] = useState('')
  const [saving, setSaving] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors({})
    setGeneralError('')
    setSaving(true)
    try {
      const input: UsuarioInput = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        rol,
        es_gerencia: esGerencia,
      }
      // El nombre de usuario se elige al crear y después no cambia.
      if (!usuario) input.username = username.trim()
      await onSave(input)
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
      setGeneralError(cause instanceof Error ? cause.message : 'No se pudo guardar el usuario.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      className="card edit-form"
      aria-label="Formulario de usuario"
      noValidate
      onSubmit={(event) => void submit(event)}
    >
      <div className="form-heading">
        <h3>{usuario ? `Editar ${usuario.username}` : 'Nuevo usuario'}</h3>
        <button type="button" className="button-ghost" onClick={onCancel}>
          Cancelar
        </button>
      </div>
      <div className="form-grid">
        {!usuario && (
          <label>
            Usuario
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="off"
              required
            />
            <FieldErrors messages={errors.username} />
          </label>
        )}
        <label>
          Nombre
          <input
            value={firstName}
            onChange={(event) => setFirstName(event.target.value)}
            required
          />
          <FieldErrors messages={errors.first_name} />
        </label>
        <label>
          Apellido
          <input value={lastName} onChange={(event) => setLastName(event.target.value)} />
          <FieldErrors messages={errors.last_name} />
        </label>
        <label>
          Correo
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <FieldErrors messages={errors.email} />
        </label>
        <label>
          Rol
          <select value={rol} onChange={(event) => setRol(event.target.value as Rol)}>
            {(Object.keys(ETIQUETAS_ROL) as Rol[]).map((valor) => (
              <option key={valor} value={valor}>
                {ETIQUETAS_ROL[valor]}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.rol} />
        </label>
        <label className="checkline">
          <input
            type="checkbox"
            checked={esGerencia}
            onChange={(event) => setEsGerencia(event.target.checked)}
          />
          Gerencia (ve ingresos y auditoría)
        </label>
      </div>
      {generalError && (
        <p className="error" role="alert">
          {generalError}
        </p>
      )}
      <button type="submit" className="button-primary" disabled={saving}>
        {saving ? 'Guardando…' : 'Guardar'}
      </button>
    </form>
  )
}
