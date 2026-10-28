import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import { formatearFecha } from '../../shared/fechas'
import type { Campania } from './types'
import { etiquetaEstado } from './types'

type Filtro = { cliente: number } | { marca: number }

type Props = {
  filtro: Filtro
  titulo: string
  /** Oculta la columna que ya se sabe por el contexto (la marca en su ficha). */
  ocultar?: 'marca'
}

type Carga = { estado: 'cargando' | 'error' | 'listo'; filas: Campania[] }

function periodo(campania: Campania): string {
  return campania.fecha_inicio && campania.fecha_fin
    ? `${formatearFecha(campania.fecha_inicio)} → ${formatearFecha(campania.fecha_fin)}`
    : 'Sin fechas'
}

/** Campañas de un cliente o de una marca, de solo lectura (HU-021 y HU-022). */
export default function CampaniasLista({ filtro, titulo, ocultar }: Props) {
  const [carga, setCarga] = useState<Carga>({ estado: 'cargando', filas: [] })
  const params = new URLSearchParams(
    Object.entries(filtro).map(([clave, valor]) => [clave, String(valor)]),
  ).toString()

  useEffect(() => {
    let active = true
    void apiGet<Campania[]>(`/api/campanias/campanias/?${params}`)
      .then((filas) => {
        if (active) setCarga({ estado: 'listo', filas })
      })
      .catch(() => {
        if (active) setCarga({ estado: 'error', filas: [] })
      })
    return () => {
      active = false
    }
  }, [params])

  return (
    <section className="card table-wrap section-gap" aria-label={titulo}>
      <h3>{titulo}</h3>
      {carga.estado === 'cargando' ? (
        <p className="empty">Cargando campañas…</p>
      ) : carga.estado === 'error' ? (
        <p className="error" role="alert">
          No se pudieron cargar las campañas.
        </p>
      ) : carga.filas.length === 0 ? (
        <p className="empty">Todavía no hay campañas.</p>
      ) : (
        <table aria-label="Campañas">
          <thead>
            <tr>
              <th>Campaña</th>
              {ocultar !== 'marca' && <th>Marca</th>}
              <th>Cliente que factura</th>
              <th>Período</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {carga.filas.map((fila) => (
              <tr key={fila.id}>
                <td className="primary-cell">{fila.nombre || `Campaña #${fila.id}`}</td>
                {ocultar !== 'marca' && <td>{fila.marca_nombre ?? '—'}</td>}
                <td>{fila.cliente_factura_nombre || '—'}</td>
                <td>{periodo(fila)}</td>
                <td>{etiquetaEstado(fila.estado)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
