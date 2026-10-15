import { useEffect, useState } from 'react'
import Login from './app/Login'
import CartelesPage from './features/inventario/CartelesPage'
import { ApiError, apiGet, apiWrite } from './shared/api'
import './App.css'

type Session = { status: 'checking' | 'anonymous' | 'offline' | 'ready'; username: string }

function App() {
  const [session, setSession] = useState<Session>({ status: 'checking', username: '' })

  useEffect(() => {
    let active = true
    void apiGet<{ username: string }>('/api/auth/me/')
      .then((user) => { if (active) setSession({ status: 'ready', username: user.username }) })
      .catch((error: unknown) => {
        if (active) setSession({ status: error instanceof ApiError && error.status === 401 ? 'anonymous' : 'offline', username: '' })
      })
    return () => { active = false }
  }, [])

  async function signOut() {
    await apiWrite('/api/auth/logout/', 'POST')
    setSession({ status: 'anonymous', username: '' })
  }

  if (session.status === 'checking') return <main className="auth-shell"><p>Comprobando sesión…</p></main>
  if (session.status === 'offline') return <main className="auth-shell"><h1>Big Media</h1><p role="alert">No se pudo conectar con la API.</p></main>
  if (session.status === 'anonymous') return <Login onLogin={(username) => setSession({ status: 'ready', username })} />

  return (
    <div className="app-shell">
      <header className="topbar"><div className="brand-mark">BM<span>.</span></div><div className="topbar-title"><strong>Big Media</strong><small>Sistema de carteles</small></div><div className="topbar-user"><span>{session.username}</span><button className="button-ghost" onClick={() => void signOut()}>Salir</button></div></header>
      <main className="app-main"><CartelesPage /></main>
    </div>
  )
}

export default App
