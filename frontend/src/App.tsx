import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import {
  CalendarDays,
  CircleDollarSign,
  LayoutDashboard,
  Layers,
  LogOut,
  Megaphone,
  Menu,
  Settings,
  Signpost,
  Tags,
  Truck,
  Users,
  X,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import Login from './app/Login'
import CartelesPage from './features/inventario/CartelesPage'
import CatalogosPage from './features/inventario/CatalogosPage'
import ClientesPage from './features/clientes/ClientesPage'
import MarcasPage from './features/clientes/MarcasPage'
import CampaniasPage from './features/campanias/CampaniasPage'
import CostosPage from './features/costos/CostosPage'
import DisponibilidadPage from './features/disponibilidad/DisponibilidadPage'
import PanelPrincipal from './features/panel/PanelPrincipal'
import { ApiError, apiGet, apiWrite } from './shared/api'
import './App.css'

type Session = { status: 'checking' | 'anonymous' | 'offline' | 'ready'; username: string }
type Page =
  | 'panel'
  | 'clientes'
  | 'marcas'
  | 'campanias'
  | 'carteles'
  | 'disponibilidad'
  | 'proveedores'
  | 'costos'
  | 'formatos'
  | 'catalogos'

type Item = { id: Page; label: string; icon: LucideIcon; render: () => ReactNode }

const sections: { title: string; items: Item[] }[] = [
  {
    title: 'Inicio',
    items: [
      { id: 'panel', label: 'Panel', icon: LayoutDashboard, render: () => <PanelPrincipal /> },
    ],
  },
  {
    title: 'Comercial',
    items: [
      { id: 'clientes', label: 'Clientes', icon: Users, render: () => <ClientesPage /> },
      { id: 'marcas', label: 'Marcas', icon: Tags, render: () => <MarcasPage /> },
      { id: 'campanias', label: 'Campañas', icon: Megaphone, render: () => <CampaniasPage /> },
    ],
  },
  {
    title: 'Inventario',
    items: [
      { id: 'carteles', label: 'Carteles', icon: Signpost, render: () => <CartelesPage /> },
      {
        id: 'disponibilidad',
        label: 'Disponibilidad',
        icon: CalendarDays,
        render: () => <DisponibilidadPage />,
      },
    ],
  },
  {
    title: 'Operación',
    items: [
      {
        id: 'proveedores',
        label: 'Proveedores',
        icon: Truck,
        render: () => (
          <CatalogosPage
            categorias={['proveedores']}
            seccion="Operación"
            titulo="Proveedores"
            descripcion="Quienes prestan servicios de alquiler, impresión o fijación."
          />
        ),
      },
      { id: 'costos', label: 'Costos', icon: CircleDollarSign, render: () => <CostosPage /> },
      {
        id: 'formatos',
        label: 'Formatos',
        icon: Layers,
        render: () => (
          <CatalogosPage
            categorias={['formatos']}
            seccion="Operación"
            titulo="Formatos"
            descripcion="Tipos de soporte, con su modalidad, capacidad y medidas."
          />
        ),
      },
    ],
  },
  {
    title: 'Configuración',
    items: [
      { id: 'catalogos', label: 'Catálogos', icon: Settings, render: () => <CatalogosPage /> },
    ],
  },
]

const pages = sections.flatMap((section) => section.items)

function App() {
  const [session, setSession] = useState<Session>({ status: 'checking', username: '' })
  const [page, setPage] = useState<Page>('clientes')
  const [menuOpen, setMenuOpen] = useState(false)

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
    <div className={menuOpen ? 'app-shell menu-open' : 'app-shell'}>
      <header className="mobile-bar">
        <button
          className="icon-button"
          aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
        </button>
        <div className="brand-mark">
          BM<span>.</span>
        </div>
      </header>
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">
            BM<span>.</span>
          </div>
          <div className="topbar-title">
            <strong>Big Media</strong>
            <small>Sistema de carteles</small>
          </div>
        </div>
        <nav className="sidenav" aria-label="Navegación">
          {sections.map((section) => (
            <div key={section.title} className="nav-section">
              <p className="nav-section-title">{section.title}</p>
              {section.items.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    key={item.id}
                    className={page === item.id ? 'active' : ''}
                    aria-current={page === item.id ? 'page' : undefined}
                    onClick={() => {
                      setPage(item.id)
                      setMenuOpen(false)
                    }}
                  >
                    <Icon aria-hidden="true" size={18} />
                    {item.label}
                  </button>
                )
              })}
            </div>
          ))}
        </nav>
        <div className="sidebar-user">
          <span>{session.username}</span>
          <button className="button-ghost" onClick={() => void signOut()}>
            <LogOut aria-hidden="true" size={16} />
            Salir
          </button>
        </div>
      </aside>
      <main className="app-main" key={page}>
        {pages.find((item) => item.id === page)?.render()}
      </main>
    </div>
  )
}

export default App
