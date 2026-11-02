import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, apiWrite } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'

type Props = {
  /** El valor de `definir-clave` del link: `<uid>.<token>`. */
  codigo: string
  onListo: () => void
}

export default function DefinirClave({ codigo, onListo }: Props) {
  const [clave, setClave] = useState('')
  const [repetida, setRepetida] = useState('')
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors({})
    setError('')
    if (clave !== repetida) {
      setError('Las contraseñas no coinciden.')
      return
    }
    const separador = codigo.indexOf('.')
    setBusy(true)
    try {
      await apiWrite('/api/usuarios/definir-clave/', 'POST', {
        uid: codigo.slice(0, separador),
        token: codigo.slice(separador + 1),
        clave,
      })
      onListo()
    } catch (cause) {
      if (cause instanceof ApiError) {
        setErrors(cause.fields)
        setError(cause.fields.token?.join(' ') ?? (cause.fields.clave ? '' : cause.message))
      } else {
        setError('No se pudo definir la contraseña.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="brand-mark">BM</div>
      <p className="eyebrow">Big Media Argentina</p>
      <h1>Definí tu contraseña</h1>
      <form className="card auth-form" onSubmit={(event) => void submit(event)}>
        <label>
          Contraseña nueva
          <input
            type="password"
            autoComplete="new-password"
            value={clave}
            onChange={(event) => setClave(event.target.value)}
            required
          />
          <FieldErrors messages={errors.clave} />
        </label>
        <label>
          Repetila
          <input
            type="password"
            autoComplete="new-password"
            value={repetida}
            onChange={(event) => setRepetida(event.target.value)}
            required
          />
        </label>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" disabled={busy}>
          {busy ? 'Guardando…' : 'Guardar contraseña'}
        </button>
      </form>
    </div>
  )
}
