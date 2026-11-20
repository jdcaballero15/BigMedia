import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import { formatearFecha } from '../../shared/fechas'
import type { Cliente } from '../clientes/types'
import InteraccionForm from './InteraccionForm'
import type { InteraccionInput } from './InteraccionForm'
import type { Interaccion } from './types'
import { etiquetaTipoInteraccion } from './types'

type Filtro = { cliente: number } | { campania: number } | { marca: number }
type Columna = 'cliente' | 'campania' | 'marca'

type Props = {
  filtro: Filtro
  titulo: string
  /** Oculta la columna que ya se sabe por el contexto (el cliente en su ficha, por ejemplo). */
  ocultar?: Columna
  /** Avisa cuántas interacciones trajo, para el contador de la ficha. */
  onCargadas?: (cantidad: number) => void
  /** Con el cliente de la ficha, se cargan y editan interacciones; sin él, es de solo lectura. */
  clienteParaCargar?: Cliente
}

const URL = '/api/campanias/interacciones/'

type Carga = { estado: 'cargando' | 'error' | 'listo'; filas: Interaccion[] }

/** Interacciones de un cliente, una campaña o una marca (HU-020, RN-018). */
export default function InteraccionesLista({
  filtro,
  titulo,
  ocultar,
  onCargadas,
  clienteParaCargar,
}: Props) {
  const [carga, setCarga] = useState<Carga>({ estado: 'cargando', filas: [] })
  const [editing, setEditing] = useState<Interaccion | 'new' | null>(null)
  const [revision, setRevision] = useState(0)
  const params = new URLSearchParams(
    Object.entries(filtro).map(([clave, valor]) => [clave, String(valor)]),
  ).toString()

  useEffect(() => {
    let active = true
    void apiGet<Interaccion[]>(`${URL}?${params}`)
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
  }, [params, onCargadas, revision])

  async function guardar(input: InteraccionInput) {
    if (editing === null) return
    if (editing === 'new') await apiWrite(URL, 'POST', input)
    else await apiWrite(`${URL}${editing.id}/`, 'PATCH', input)
    setEditing(null)
    setRevision((current) => current + 1)
  }

  return (
    <section className="card table-wrap section-gap" aria-label={titulo}>
      <div className="card-heading">
        <h3>{titulo}</h3>
        {clienteParaCargar && (
          <button className="button-primary" onClick={() => setEditing('new')}>
            Nueva interacción
          </button>
        )}
      </div>
      {clienteParaCargar && editing !== null && (
        <InteraccionForm
          key={editing === 'new' ? 'nueva' : editing.id}
          interaccion={editing === 'new' ? null : editing}
          cliente={clienteParaCargar}
          onSave={guardar}
          onCancel={() => setEditing(null)}
        />
      )}
      {carga.estado === 'cargando' ? (
        <p className="empty">Cargando interacciones…</p>
      ) : carga.estado === 'error' ? (
        <p className="error" role="alert">
          No se pudieron cargar las interacciones.
        </p>
      ) : carga.filas.length === 0 ? (
        <p className="empty">Todavía no hay interacciones registradas.</p>
      ) : (
        <TablaInteracciones
          filas={carga.filas}
          ocultar={ocultar}
          onEditar={clienteParaCargar ? (fila) => setEditing(fila) : undefined}
        />
      )}
    </section>
  )
}

type TablaProps = {
  filas: Interaccion[]
  ocultar?: Columna
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
          {ocultar !== 'marca' && <th>Marca</th>}
          <th>Notas</th>
          <th>Recordatorio</th>
          {onEditar && <th>Acciones</th>}
        </tr>
      </thead>
      <tbody>
        {filas.map((fila) => (
          <tr key={fila.id}>
            <td>{fila.fecha}</td>
            <td>{etiquetaTipoInteraccion(fila.tipo)}</td>
            <td className="primary-cell">{fila.asunto || 'Sin asunto'}</td>
            {ocultar !== 'cliente' && <td>{fila.cliente_nombre}</td>}
            <td>{fila.contacto_nombre ?? '—'}</td>
            {ocultar !== 'campania' && <td>{fila.campania_nombre ?? '—'}</td>}
            {ocultar !== 'marca' && <td>{fila.marca_nombre ?? '—'}</td>}
            <td>{fila.notas || '—'}</td>
            <td>
              {fila.recordatorio_fecha ? (
                <>
                  {formatearFecha(fila.recordatorio_fecha)} · {fila.recordatorio_texto}{' '}
                  <span
                    className={fila.recordatorio_hecho_en ? 'etiqueta-azul' : 'etiqueta-alerta'}
                  >
                    {fila.recordatorio_hecho_en ? 'Hecho' : 'Pendiente'}
                  </span>
                </>
              ) : (
                '—'
              )}
            </td>
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
