import { useState } from 'react'
import type { FormEvent } from 'react'
import { apiWrite } from '../shared/api'
import type { Rol } from '../shared/sesion'

type LoginProps = {
  onLogin: (username: string, esGerencia: boolean, rol: Rol) => void
  mensaje?: string
}

export default function Login({ onLogin, mensaje }: LoginProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const user = await apiWrite<{ username: string; es_gerencia: boolean; rol: Rol }>(
        '/api/auth/login/',
        'POST',
        { username, password },
      )
      onLogin(user.username, user.es_gerencia, user.rol)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudo iniciar sesión.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="brand-mark">BM</div>
      <p className="eyebrow">Big Media Argentina</p>
      <h1>Inventario de carteles</h1>
      <p className="muted">Ingresá con tu usuario para administrar los espacios publicitarios.</p>
      {mensaje && <p className="muted">{mensaje}</p>}
      <form className="card auth-form" onSubmit={(event) => void submit(event)}>
        <h2>Ingresar</h2>
        <label>
          Usuario
          <input
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" disabled={busy}>
          {busy ? 'Ingresando…' : 'Ingresar'}
        </button>
      </form>
    </div>
  )
}
