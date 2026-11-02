import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import { formatearFecha } from '../../shared/fechas'
import type { Campania, EstadoCampania } from './types'
import { ESTADOS_CAMPANIA, etiquetaEstado } from './types'

type Filtro = { cliente: number } | { marca: number }

type Props = {
  filtro: Filtro
  titulo: string
  /** Oculta la columna que ya se sabe por el contexto (la marca en su ficha). */
  ocultar?: 'marca'
  /** Avisa cuántas campañas trajo, para el contador de la ficha. */
  onCargadas?: (cantidad: number) => void
}

type Carga = { estado: 'cargando' | 'error' | 'listo'; filas: Campania[] }

function periodo(campania: Campania): string {
  return campania.fecha_inicio && campania.fecha_fin
    ? `${formatearFecha(campania.fecha_inicio)} → ${formatearFecha(campania.fecha_fin)}`
    : 'Sin fechas'
}

/** Campañas de un cliente o de una marca, de solo lectura (HU-021 y HU-022). */
export default function CampaniasLista({ filtro, titulo, ocultar, onCargadas }: Props) {
  const [carga, setCarga] = useState<Carga>({ estado: 'cargando', filas: [] })
  const [estado, setEstado] = useState<EstadoCampania | ''>('')
  const params = new URLSearchParams(
    Object.entries(filtro).map(([clave, valor]) => [clave, String(valor)]),
  ).toString()

  useEffect(() => {
    let active = true
    void apiGet<Campania[]>(`/api/campanias/campanias/?${params}`)
      .then((filas) => {
        if (!active) return
        setCarga({ estado: 'listo', filas })
        onCargadas?.(filas.length)
      })
      .catch(() => {
        if (active) setCarga({ estado: 'error', filas: [] })
      })
    return () => {
      active = false
    }
  }, [params, onCargadas])

  const visibles = carga.filas.filter((fila) => estado === '' || fila.estado === estado)
  return (
    <section className="card section-gap" aria-label={titulo}>
      <div className="card-heading">
        <h3>{titulo}</h3>
        {carga.filas.length > 0 && (
          <div className="pildoras" role="group" aria-label="Filtrar por estado">
            {[{ value: '' as const, label: 'Todas' }, ...ESTADOS_CAMPANIA].map((opcion) => (
              <button
                key={opcion.value}
                className={estado === opcion.value ? 'active' : ''}
                aria-pressed={estado === opcion.value}
                onClick={() => setEstado(opcion.value)}
              >
                {opcion.label}
              </button>
            ))}
          </div>
        )}
      </div>
      {carga.estado === 'cargando' ? (
        <p className="empty">Cargando campañas…</p>
      ) : carga.estado === 'error' ? (
        <p className="error" role="alert">
          No se pudieron cargar las campañas.
        </p>
      ) : carga.filas.length === 0 ? (
        <p className="empty">Todavía no hay campañas.</p>
      ) : visibles.length === 0 ? (
        <p className="empty">No hay campañas en ese estado.</p>
      ) : (
        <ul className="tarjetas" aria-label="Campañas">
          {visibles.map((fila) => (
            <li key={fila.id} className="tarjeta">
              <strong>{fila.nombre || `Campaña #${fila.id}`}</strong>
              {ocultar !== 'marca' && <span>{fila.marca_nombre ?? 'Sin marca'}</span>}
              <span>
                <small>Factura</small> <span>{fila.cliente_factura_nombre || '—'}</span>
              </span>
              <span>{periodo(fila)}</span>
              <span className="etiqueta">{etiquetaEstado(fila.estado)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
