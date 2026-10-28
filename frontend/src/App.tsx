import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import {
  BarChart3,
  CalendarDays,
  CircleDollarSign,
  LayoutDashboard,
  Layers,
  LogOut,
  Megaphone,
  MessagesSquare,
  Menu,
  ScrollText,
  Settings,
  Signpost,
  SlidersHorizontal,
  Tags,
  TrendingUp,
  Truck,
  UserCog,
  Users,
  X,
  Receipt,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import Login from './app/Login'
import CartelesPage from './features/inventario/CartelesPage'
import CatalogosPage from './features/inventario/CatalogosPage'
import ClientesPage from './features/clientes/ClientesPage'
import MarcasPage from './features/clientes/MarcasPage'
import CampaniasPage from './features/campanias/CampaniasPage'
import InteraccionesPage from './features/campanias/InteraccionesPage'
import CostosPage from './features/costos/CostosPage'
import DisponibilidadPage from './features/disponibilidad/DisponibilidadPage'
import ReporteIngresosPage from './features/facturacion/ReporteIngresos'
import PorRubroPage from './features/facturacion/PorRubro'
import ItemsPage from './features/facturacion/ItemsPage'
import PanelPrincipal from './features/panel/PanelPrincipal'
import AuditoriaPage from './features/auditoria/Auditoria'
import ParametrosPage from './features/reservas/ParametrosPage'
import ReporteOcupacionPage from './features/reservas/ReporteOcupacion'
import DefinirClave from './features/usuarios/DefinirClave'
import UsuariosPage from './features/usuarios/UsuariosPage'
import { ApiError, apiGet, apiWrite } from './shared/api'
import { fechaLarga } from './shared/fechas'
import { PuedeEditarContext } from './shared/sesion'
import type { Rol } from './shared/sesion'
import './App.css'

type Session = {
  status: 'checking' | 'anonymous' | 'offline' | 'ready'
  username: string
  esGerencia: boolean
  rol: Rol
}
type Page =
  | 'panel'
  | 'clientes'
  | 'marcas'
  | 'campanias'
  | 'interacciones'
  | 'items-facturacion'
  | 'carteles'
  | 'disponibilidad'
  | 'proveedores'
  | 'costos'
  | 'ingresos'
  | 'rubro'
  | 'ocupacion'
  | 'formatos'
  | 'catalogos'
  | 'parametros'
  | 'auditoria'
  | 'usuarios'

type Item = {
  id: Page
  label: string
  icon: LucideIcon
  render: () => ReactNode
  soloGerencia?: boolean
  soloAdministrador?: boolean
}

const sections: { title: string; items: Item[] }[] = [
  {
    title: 'Inicio',
    items: [
      { id: 'panel', label: 'Panel', icon: LayoutDashboard, render: () => <PanelPrincipal /> },
    ],
  },
  {
    title: 'Reportes',
    items: [
      {
        id: 'ingresos',
        label: 'Ingresos',
        icon: TrendingUp,
        render: () => <ReporteIngresosPage />,
        soloGerencia: true,
      },
      {
        id: 'rubro',
        label: 'Por rubro o grupo',
        icon: Tags,
        render: () => <PorRubroPage />,
        soloGerencia: true,
      },
      {
        id: 'ocupacion',
        label: 'Ocupación',
        icon: BarChart3,
        render: () => <ReporteOcupacionPage />,
      },
    ],
  },
  {
    title: 'Comercial',
    items: [
      { id: 'clientes', label: 'Clientes', icon: Users, render: () => <ClientesPage /> },
      { id: 'marcas', label: 'Marcas', icon: Tags, render: () => <MarcasPage /> },
      { id: 'campanias', label: 'Campañas', icon: Megaphone, render: () => <CampaniasPage /> },
      {
        id: 'interacciones',
        label: 'Interacciones',
        icon: MessagesSquare,
        render: () => <InteraccionesPage />,
      },
      {
        id: 'items-facturacion',
        label: 'Ítems a facturar',
        icon: Receipt,
        render: () => <ItemsPage />,
      },
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
      {
        id: 'parametros',
        label: 'Parámetros',
        icon: SlidersHorizontal,
        render: () => <ParametrosPage />,
        soloAdministrador: true,
      },
    ],
  },
  {
    title: 'Administración',
    items: [
      {
        id: 'auditoria',
        label: 'Auditoría',
        icon: ScrollText,
        render: () => <AuditoriaPage />,
        soloGerencia: true,
      },
      {
        id: 'usuarios',
        label: 'Usuarios',
        icon: UserCog,
        render: () => <UsuariosPage />,
        soloAdministrador: true,
      },
    ],
  },
]

const pages = sections.flatMap((section) => section.items)

/** El link de contraseña llega como `/?definir-clave=<uid>.<token>` (HU-005). */
function codigoDelLink(): string | null {
  return new URLSearchParams(window.location.search).get('definir-clave')
}

function App() {
  const [session, setSession] = useState<Session>({
    status: 'checking',
    username: '',
    esGerencia: false,
    rol: 'lectura',
  })
  const [page, setPage] = useState<Page>('clientes')
  const [menuOpen, setMenuOpen] = useState(false)
  const [hoy] = useState(() => fechaLarga(new Date()))
  const [etiqueta, setEtiqueta] = useState<{ texto: string; top: number } | null>(null)
  const [expirada, setExpirada] = useState(false)
  const [codigoClave, setCodigoClave] = useState(codigoDelLink)
  const [claveDefinida, setClaveDefinida] = useState(false)

  useEffect(() => {
    let active = true
    void apiGet<{ username: string; es_gerencia: boolean; rol: Rol }>('/api/auth/me/')
      .then((user) => {
        if (active)
          setSession({
            status: 'ready',
            username: user.username,
            esGerencia: user.es_gerencia,
            rol: user.rol,
          })
      })
      .catch((error: unknown) => {
        if (active)
          setSession({
            status: error instanceof ApiError && error.status === 401 ? 'anonymous' : 'offline',
            username: '',
            esGerencia: false,
            rol: 'lectura',
          })
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    function onSesionExpirada() {
      setSession({ status: 'anonymous', username: '', esGerencia: false, rol: 'lectura' })
      setExpirada(true)
    }
    window.addEventListener('sesion-expirada', onSesionExpirada)
    return () => {
      window.removeEventListener('sesion-expirada', onSesionExpirada)
    }
  }, [])

  async function signOut() {
    await apiWrite('/api/auth/logout/', 'POST')
    setSession({ status: 'anonymous', username: '', esGerencia: false, rol: 'lectura' })
  }

  if (codigoClave !== null)
    return (
      <DefinirClave
        codigo={codigoClave}
        onListo={() => {
          window.history.replaceState(null, '', '/')
          setCodigoClave(null)
          setClaveDefinida(true)
          setSession({ status: 'anonymous', username: '', esGerencia: false, rol: 'lectura' })
        }}
      />
    )
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
    return (
      <Login
        onLogin={(username, esGerencia, rol) => {
          setExpirada(false)
          setClaveDefinida(false)
          setSession({ status: 'ready', username, esGerencia, rol })
        }}
        mensaje={
          claveDefinida
            ? 'Listo, tu contraseña quedó definida. Ingresá con tu usuario.'
            : expirada
              ? 'Tu sesión expiró por inactividad. Ingresá de nuevo.'
              : undefined
        }
      />
    )

  const visibles = sections
    .map((section) => ({
      ...section,
      items: section.items.filter(
        (item) =>
          (!item.soloGerencia || session.esGerencia) &&
          (!item.soloAdministrador || session.rol === 'administrador'),
      ),
    }))
    .filter((section) => section.items.length > 0)

  const seccionActiva = sections.find((section) => section.items.some((item) => item.id === page))
  const paginaActiva = pages.find((item) => item.id === page)

  function mostrarEtiqueta(texto: string, elemento: HTMLElement) {
    const caja = elemento.getBoundingClientRect()
    setEtiqueta({ texto, top: caja.top + caja.height / 2 })
  }

  function botonDelMenu(id: string, texto: string, contenido: ReactNode, onClick: () => void) {
    return (
      <button
        key={id}
        className={page === id ? 'active' : ''}
        aria-label={texto}
        aria-current={page === id ? 'page' : undefined}
        onClick={onClick}
        onMouseEnter={(event) => mostrarEtiqueta(texto, event.currentTarget)}
        onFocus={(event) => mostrarEtiqueta(texto, event.currentTarget)}
        onMouseLeave={() => setEtiqueta(null)}
        onBlur={() => setEtiqueta(null)}
      >
        {contenido}
        <span className="nav-label">{texto}</span>
      </button>
    )
  }

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
        <div className="brand-mark">BM</div>
      </header>
      <aside className="sidebar">
        <div className="brand-mark" title="Big Media">
          BM
        </div>
        <nav className="sidenav" aria-label="Navegación">
          {visibles.map((section) => (
            <div
              key={section.title}
              className="nav-section"
              role="group"
              aria-label={section.title}
            >
              {section.items.map((item) => {
                const Icon = item.icon
                return botonDelMenu(
                  item.id,
                  item.label,
                  <Icon aria-hidden="true" size={20} />,
                  () => {
                    setPage(item.id)
                    setMenuOpen(false)
                  },
                )
              })}
            </div>
          ))}
        </nav>
        <div className="sidebar-user">
          <span
            className="avatar"
            title={session.username}
            onMouseEnter={(event) => mostrarEtiqueta(session.username, event.currentTarget)}
            onMouseLeave={() => setEtiqueta(null)}
          >
            {session.username.slice(0, 1).toUpperCase()}
          </span>
          {botonDelMenu('salir', 'Salir', <LogOut aria-hidden="true" size={20} />, () => {
            void signOut()
          })}
        </div>
      </aside>
      {etiqueta !== null && (
        <span className="nav-tooltip" role="tooltip" style={{ top: etiqueta.top }}>
          {etiqueta.texto}
        </span>
      )}
      <div className="app-content">
        <header className="topbar" aria-label="Ubicación">
          <p className="ruta">
            Big Media <span aria-hidden="true">/</span> {seccionActiva?.title}{' '}
            <span aria-hidden="true">/</span> <strong>{paginaActiva?.label}</strong>
          </p>
          <p className="fecha-hoy">{hoy}</p>
        </header>
        <main className="app-main" key={page}>
          <PuedeEditarContext value={session.rol !== 'lectura'}>
            {paginaActiva?.render()}
          </PuedeEditarContext>
        </main>
      </div>
    </div>
  )
}

export default App
