import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import Login from './app/Login'
import CartelesPage from './features/inventario/CartelesPage'
import CatalogosPage from './features/inventario/CatalogosPage'
import ClientesPage from './features/clientes/ClientesPage'
import MarcasPage from './features/clientes/MarcasPage'
import { ApiError, apiGet, apiWrite } from './shared/api'
import './App.css'

type Session = { status: 'checking' | 'anonymous' | 'offline' | 'ready'; username: string }
type Page = 'carteles' | 'catalogos' | 'clientes' | 'marcas'

const pages: { id: Page; label: string; render: () => ReactNode }[] = [
  { id: 'carteles', label: 'Carteles', render: () => <CartelesPage /> },
  { id: 'catalogos', label: 'Catálogos', render: () => <CatalogosPage /> },
  { id: 'clientes', label: 'Clientes', render: () => <ClientesPage /> },
  { id: 'marcas', label: 'Marcas', render: () => <MarcasPage /> },
]

function App() {
  const [session, setSession] = useState<Session>({ status: 'checking', username: '' })
  const [page, setPage] = useState<Page>('carteles')

  useEffect(() => {
    let active = true
    void apiGet<{ username: string }>('/api/auth/me/')
      .then((user) => {
        if (active) setSession({ status: 'ready', username: user.username })
      })
      .catch((error: unknown) => {
        if (active)
          setSession({
            status: error instanceof ApiError && error.status === 401 ? 'anonymous' : 'offline',
            username: '',
          })
      })
    return () => {
      active = false
    }
  }, [])

  async function signOut() {
    await apiWrite('/api/auth/logout/', 'POST')
    setSession({ status: 'anonymous', username: '' })
  }

  if (session.status === 'checking')
    return (
      <main className="auth-shell">
        <p>Comprobando sesión…</p>
      </main>
    )
  if (session.status === 'offline')
    return (
      <main className="auth-shell">
        <h1>Big Media</h1>
        <p role="alert">No se pudo conectar con la API.</p>
      </main>
    )
  if (session.status === 'anonymous')
    return <Login onLogin={(username) => setSession({ status: 'ready', username })} />

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-mark">
          BM<span>.</span>
        </div>
        <div className="topbar-title">
          <strong>Big Media</strong>
          <small>Sistema de carteles</small>
        </div>
        <nav className="topnav" aria-label="Navegación">
          {pages.map((item) => (
            <button
              key={item.id}
              className={page === item.id ? 'active' : ''}
              onClick={() => setPage(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="topbar-user">
          <span>{session.username}</span>
          <button className="button-ghost" onClick={() => void signOut()}>
            Salir
          </button>
        </div>
      </header>
      <main className="app-main">{pages.find((item) => item.id === page)?.render()}</main>
    </div>
  )
}

export default App
