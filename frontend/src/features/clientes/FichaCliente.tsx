import { useEffect, useMemo, useState } from 'react'
import { apiGet } from '../../shared/api'
import { useDetalleRuta } from '../../shared/ruta'
import CampaniasLista from '../campanias/CampaniasLista'
import InteraccionesLista from '../campanias/InteraccionesLista'
import ContactosDelCliente from './ContactosDelCliente'
import { iniciales } from './iniciales'
import type { Cliente, Marca } from './types'

export type Ficha = { cliente: Cliente; recienCreado: boolean }
type MarcasCargadas = { estado: 'cargando' | 'error' | 'listo'; marcas: Marca[] }

function MarcasDelCliente({
  ficha,
  revision,
  onCargadas,
}: {
  ficha: Ficha
  revision: number
  onCargadas: (cantidad: number) => void
}) {
  const { cliente, recienCreado } = ficha
  const [carga, setCarga] = useState<MarcasCargadas>({ estado: 'cargando', marcas: [] })

  useEffect(() => {
    let active = true
    void apiGet<Marca[]>(`/api/clientes/marcas/?cliente=${cliente.id}&incluir_inactivos=1`)
      .then((marcas) => {
        if (!active) return
        setCarga({ estado: 'listo', marcas })
        onCargadas(marcas.length)
      })
      .catch(() => {
        if (active) setCarga({ estado: 'error', marcas: [] })
      })
    return () => {
      active = false
    }
  }, [cliente.id, revision, onCargadas])

  const titulo = `Marcas de ${cliente.nombre_visible}`
  return (
    <section className="card table-wrap section-gap" aria-label={titulo}>
      <div className="card-heading">
        <h3>{titulo}</h3>
      </div>
      {/* Un cliente recién creado solo tiene marcas si la API creó su homónima. */}
      {recienCreado && carga.marcas.length > 0 && (
        <p className="notice" role="status">
          Se creó la marca «{carga.marcas[0].nombre}» para este cliente directo.
        </p>
      )}
      {carga.estado === 'cargando' ? (
        <p className="empty">Cargando marcas…</p>
      ) : carga.estado === 'error' ? (
        <p className="error" role="alert">
          No se pudieron cargar las marcas.
        </p>
      ) : carga.marcas.length === 0 ? (
        <p className="empty">Este cliente todavía no tiene marcas.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Marca</th>
              <th>Rubro</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {carga.marcas.map((marca) => (
              <tr key={marca.id}>
                <td className="primary-cell">{marca.nombre}</td>
                <td>{marca.rubro_nombre ?? 'Sin rubro'}</td>
                <td>{marca.activo ? 'Activa' : 'Inactiva'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

type Seccion = 'campanias' | 'marcas' | 'interacciones'
type Cantidades = Record<Seccion | 'contactos', number | null>

const SECCIONES: { id: Seccion; label: string }[] = [
  { id: 'campanias', label: 'Campañas' },
  { id: 'marcas', label: 'Marcas' },
  { id: 'interacciones', label: 'Interacciones' },
]

type Props = {
  ficha: Ficha
  revision: number
  onVolver: () => void
  /** Solo si el rol puede editar. */
  onEditar?: () => void
}

/** Ficha de un cliente como página: encabezado, secciones con contador y contactos (HU-021). */
export default function FichaCliente({ ficha, revision, onVolver, onEditar }: Props) {
  const { cliente } = ficha
  // Recién creado abre en Marcas: ahí se avisa la marca homónima que creó la API.
  const [seccion, setSeccion] = useState<Seccion>(ficha.recienCreado ? 'marcas' : 'campanias')
  const [cantidades, setCantidades] = useState<Cantidades>({
    campanias: null,
    marcas: null,
    interacciones: null,
    contactos: null,
  })
  useDetalleRuta(cliente.nombre_visible, onVolver)
  // Solo el intermediario formal tiene contactos múltiples (HU-068, RN-015).
  const conContactos = cliente.tipo === 'intermediario_formal'

  // Estables: las listas vuelven a cargar si su callback cambia.
  const contar = useMemo(() => {
    const para = (clave: keyof Cantidades) => (cantidad: number) =>
      setCantidades((actual) => ({ ...actual, [clave]: cantidad }))
    return {
      campanias: para('campanias'),
      marcas: para('marcas'),
      interacciones: para('interacciones'),
      contactos: para('contactos'),
    }
  }, [])

  const datos = [cliente.razon_social, cliente.correo, cliente.activo ? 'Activo' : 'Inactivo']
  const resumen: { clave: keyof Cantidades; label: string }[] = [
    { clave: 'marcas', label: 'Marcas' },
    { clave: 'campanias', label: 'Campañas' },
    ...(conContactos ? [{ clave: 'contactos' as const, label: 'Contactos' }] : []),
    { clave: 'interacciones', label: 'Interacciones' },
  ]

  return (
    <section className="ficha" aria-label={`Ficha de ${cliente.nombre_visible}`}>
      <button className="button-ghost ficha-volver" onClick={onVolver}>
        <span aria-hidden="true">←</span> Volver a clientes
      </button>
      <header className="ficha-encabezado">
        <span className="ficha-iniciales" aria-hidden="true">
          {iniciales(cliente.nombre_visible)}
        </span>
        <div className="ficha-titulo">
          <p className="ficha-tipo">{cliente.tipo_nombre || 'Sin tipo'}</p>
          <h2>{cliente.nombre_visible}</h2>
          <p>{datos.filter(Boolean).join(' · ')}</p>
        </div>
        <dl className="ficha-cantidades" aria-label="Cantidades">
          {resumen.map((item) => (
            <div key={item.clave}>
              <dt>{item.label}</dt>
              <dd>{cantidades[item.clave] ?? '—'}</dd>
            </div>
          ))}
        </dl>
        {onEditar && (
          <button className="button-ghost ficha-editar" onClick={onEditar}>
            Editar
          </button>
        )}
      </header>
      <div className={conContactos ? 'ficha-cuerpo con-lateral' : 'ficha-cuerpo'}>
        <aside className="ficha-lateral">
          <nav className="ficha-secciones" aria-label="Secciones de la ficha">
            {SECCIONES.map((item) => (
              <button
                key={item.id}
                className={seccion === item.id ? 'active' : ''}
                aria-pressed={seccion === item.id}
                onClick={() => setSeccion(item.id)}
              >
                {item.label}
                <span className="contador">{cantidades[item.id] ?? '—'}</span>
              </button>
            ))}
          </nav>
          {conContactos && <ContactosDelCliente cliente={cliente} onCargados={contar.contactos} />}
        </aside>
        <div className="ficha-contenido">
          {/* Las tres secciones se cargan juntas para tener los contadores; se ve la elegida. */}
          <div hidden={seccion !== 'campanias'}>
            <CampaniasLista
              filtro={{ cliente: cliente.id }}
              titulo={`Campañas de ${cliente.nombre_visible}`}
              onCargadas={contar.campanias}
            />
          </div>
          <div hidden={seccion !== 'marcas'}>
            <MarcasDelCliente ficha={ficha} revision={revision} onCargadas={contar.marcas} />
          </div>
          <div hidden={seccion !== 'interacciones'}>
            <InteraccionesLista
              filtro={{ cliente: cliente.id }}
              titulo={`Interacciones con ${cliente.nombre_visible}`}
              ocultar="cliente"
              onCargadas={contar.interacciones}
            />
          </div>
        </div>
      </div>
    </section>
  )
}
