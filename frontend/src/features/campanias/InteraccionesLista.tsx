import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import type { Interaccion } from './types'
import { etiquetaTipoInteraccion } from './types'

type Filtro = { cliente: number } | { campania: number }

type Props = {
  filtro: Filtro
  titulo: string
  /** Oculta la columna que ya se sabe por el contexto (el cliente en su ficha, por ejemplo). */
  ocultar?: 'cliente' | 'campania'
  /** Avisa cuántas interacciones trajo, para el contador de la ficha. */
  onCargadas?: (cantidad: number) => void
}

type Carga = { estado: 'cargando' | 'error' | 'listo'; filas: Interaccion[] }

/** Interacciones de un cliente o de una campaña, de solo lectura (HU-020 criterio 2). */
export default function InteraccionesLista({ filtro, titulo, ocultar, onCargadas }: Props) {
  const [carga, setCarga] = useState<Carga>({ estado: 'cargando', filas: [] })
  const params = new URLSearchParams(
    Object.entries(filtro).map(([clave, valor]) => [clave, String(valor)]),
  ).toString()

  useEffect(() => {
    let active = true
    void apiGet<Interaccion[]>(`/api/campanias/interacciones/?${params}`)
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

  return (
    <section className="card table-wrap section-gap" aria-label={titulo}>
      <h3>{titulo}</h3>
      {carga.estado === 'cargando' ? (
        <p className="empty">Cargando interacciones…</p>
      ) : carga.estado === 'error' ? (
        <p className="error" role="alert">
          No se pudieron cargar las interacciones.
        </p>
      ) : carga.filas.length === 0 ? (
        <p className="empty">Todavía no hay interacciones registradas.</p>
      ) : (
        <TablaInteracciones filas={carga.filas} ocultar={ocultar} />
      )}
    </section>
  )
}

type TablaProps = {
  filas: Interaccion[]
  ocultar?: 'cliente' | 'campania'
  onEditar?: (interaccion: Interaccion) => void
}

export function TablaInteracciones({ filas, ocultar, onEditar }: TablaProps) {
  return (
    <table aria-label="Interacciones">
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Tipo</th>
          <th>Asunto</th>
          {ocultar !== 'cliente' && <th>Cliente</th>}
          <th>Contacto</th>
          {ocultar !== 'campania' && <th>Campaña</th>}
          <th>Notas</th>
          {onEditar && <th>Acciones</th>}
        </tr>
      </thead>
      <tbody>
        {filas.map((fila) => (
          <tr key={fila.id}>
            <td>{fila.fecha}</td>
            <td>{etiquetaTipoInteraccion(fila.tipo)}</td>
            <td className="primary-cell">{fila.asunto}</td>
            {ocultar !== 'cliente' && <td>{fila.cliente_nombre}</td>}
            <td>{fila.contacto_nombre ?? '—'}</td>
            {ocultar !== 'campania' && <td>{fila.campania_nombre ?? '—'}</td>}
            <td>{fila.notas || '—'}</td>
            {onEditar && (
              <td className="row-actions">
                <button className="button-ghost" onClick={() => onEditar(fila)}>
                  Editar
                </button>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
