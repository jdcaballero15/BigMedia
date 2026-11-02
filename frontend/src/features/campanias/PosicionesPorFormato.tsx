import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, apiGet, apiWrite } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { usePuedeEditar } from '../../shared/sesion'
import type { Formato } from '../inventario/types'
import AgregarCarteles from '../reservas/AgregarCarteles'
import type { FilaSeguimiento } from './types'

const LINEAS = '/api/campanias/lineas-formato/'

type Errores = Record<string, string[]>

function erroresDe(error: unknown): Errores {
  if (error instanceof ApiError && Object.keys(error.fields).length > 0) return error.fields
  return { general: ['No se pudo guardar la línea.'] }
}

/** Cantidad del input: vacío es "sin cantidad" (HU-055 criterio 2). */
function cantidadDe(valor: string): number | null {
  return valor.trim() === '' ? null : Number(valor)
}

function faltantesTexto(fila: FilaSeguimiento): string {
  if (fila.faltantes === null) return '—'
  return fila.excedente ? `${fila.faltantes} (+${fila.excedente})` : String(fila.faltantes)
}

type Props = {
  campaniaId: number
  fechaInicio?: string | null
  fechaFin?: string | null
  /** Cambia cuando se tocan las reservas de la campaña desde otra sección. */
  revisionReservas?: number
  onReservasCreadas?: () => void
}

/** Posiciones solicitadas por formato y su seguimiento (HU-055, HU-058 criterios 1 y 2). */
export default function PosicionesPorFormato(props: Props) {
  const { campaniaId, revisionReservas = 0, onReservasCreadas } = props
  const puedeEditar = usePuedeEditar()
  const [agregando, setAgregando] = useState<number | null>(null)
  const [filas, setFilas] = useState<FilaSeguimiento[] | null>(null)
  const [formatos, setFormatos] = useState<Formato[]>([])
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let active = true
    void apiGet<FilaSeguimiento[]>(`/api/reservas/seguimiento/?campania=${campaniaId}`)
      .then((rows) => {
        if (active) {
          setFilas(rows)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar las posiciones por formato.')
      })
    return () => {
      active = false
    }
  }, [campaniaId, revision, revisionReservas])

  useEffect(() => {
    if (!puedeEditar) return
    let active = true
    void apiGet<Formato[]>('/api/inventario/formatos/')
      .then((rows) => {
        if (active) setFormatos(rows)
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los formatos.')
      })
    return () => {
      active = false
    }
  }, [puedeEditar])

  const recargar = () => setRevision((current) => current + 1)
  const usados = new Set(filas?.filter((fila) => fila.linea !== null).map((fila) => fila.formato))
  const disponibles = formatos.filter((formato) => formato.activo && !usados.has(formato.id))
  const lineaAgregando = filas?.find((fila) => fila.linea !== null && fila.formato === agregando)

  return (
    <section className="card table-wrap section-gap" aria-label="Posiciones por formato">
      <h3>Posiciones por formato</h3>
      {puedeEditar && (
        <AltaLinea campaniaId={campaniaId} formatos={disponibles} onGuardada={recargar} />
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {filas === null ? (
        !error && <p className="empty">Cargando posiciones…</p>
      ) : filas.length === 0 ? (
        <p className="empty">Todavía no hay posiciones solicitadas.</p>
      ) : (
        <table aria-label="Seguimiento por formato">
          <thead>
            <tr>
              <th>Formato</th>
              <th>Solicitadas</th>
              <th>Reservadas</th>
              <th>Faltantes</th>
              {puedeEditar && <th>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {filas.map((fila) => (
              <Fila
                key={`${fila.linea ?? 'sin-linea'}-${fila.formato}`}
                fila={fila}
                puedeEditar={puedeEditar}
                onCambio={recargar}
                onAgregar={() => setAgregando(fila.formato)}
              />
            ))}
          </tbody>
        </table>
      )}
      {lineaAgregando && (
        <AgregarCarteles
          key={lineaAgregando.formato}
          campaniaId={campaniaId}
          fechaInicio={props.fechaInicio ?? ''}
          fechaFin={props.fechaFin ?? ''}
          linea={lineaAgregando}
          onCerrar={() => setAgregando(null)}
          onCreadas={() => {
            recargar()
            onReservasCreadas?.()
          }}
        />
      )}
    </section>
  )
}

type AltaProps = { campaniaId: number; formatos: Formato[]; onGuardada: () => void }

function AltaLinea({ campaniaId, formatos, onGuardada }: AltaProps) {
  const [formato, setFormato] = useState('')
  const [cantidad, setCantidad] = useState('')
  const [errores, setErrores] = useState<Errores>({})

  async function guardar(event: FormEvent) {
    event.preventDefault()
    if (!formato) {
      setErrores({ formato: ['Elegí un formato.'] })
      return
    }
    try {
      await apiWrite(LINEAS, 'POST', {
        campania: campaniaId,
        formato: Number(formato),
        cantidad: cantidadDe(cantidad),
      })
      setFormato('')
      setCantidad('')
      setErrores({})
      onGuardada()
    } catch (error) {
      setErrores(erroresDe(error))
    }
  }

  return (
    <form className="form-grid" aria-label="Agregar línea de formato" onSubmit={guardar}>
      <label>
        Formato
        <select value={formato} onChange={(event) => setFormato(event.target.value)}>
          <option value="">Elegí un formato</option>
          {formatos.map((item) => (
            <option key={item.id} value={item.id}>
              {item.nombre}
            </option>
          ))}
        </select>
        <FieldErrors messages={errores.formato} />
      </label>
      <label>
        Cantidad
        <input
          type="number"
          min={1}
          value={cantidad}
          placeholder="Sin cantidad"
          onChange={(event) => setCantidad(event.target.value)}
        />
        <FieldErrors messages={errores.cantidad} />
      </label>
      <button className="button-primary" type="submit">
        Agregar línea
      </button>
      <FieldErrors messages={errores.general} />
    </form>
  )
}

type FilaProps = {
  fila: FilaSeguimiento
  puedeEditar: boolean
  onCambio: () => void
  onAgregar: () => void
}

function Fila({ fila, puedeEditar, onCambio, onAgregar }: FilaProps) {
  const [editando, setEditando] = useState(false)
  const [cantidad, setCantidad] = useState('')
  const [errores, setErrores] = useState<Errores>({})

  async function patch(datos: Record<string, unknown>) {
    try {
      await apiWrite(`${LINEAS}${fila.linea}/`, 'PATCH', datos)
      setEditando(false)
      setErrores({})
      onCambio()
    } catch (error) {
      setErrores(erroresDe(error))
    }
  }

  function empezarEdicion() {
    setCantidad(fila.solicitadas === null ? '' : String(fila.solicitadas))
    setEditando(true)
  }

  return (
    <tr>
      <td className="primary-cell">
        {fila.formato_nombre}
        {fila.linea === null && <small className="muted"> (sin línea)</small>}
      </td>
      <td>
        {editando ? (
          <input
            type="number"
            min={1}
            aria-label={`Cantidad de ${fila.formato_nombre}`}
            value={cantidad}
            placeholder="Sin cantidad"
            onChange={(event) => setCantidad(event.target.value)}
          />
        ) : (
          (fila.solicitadas ?? '—')
        )}
        <FieldErrors messages={errores.cantidad ?? errores.general ?? errores.formato} />
      </td>
      <td>{fila.reservadas}</td>
      <td>{faltantesTexto(fila)}</td>
      {puedeEditar && (
        <td className="row-actions">
          {fila.linea !== null &&
            (editando ? (
              <>
                <button
                  className="button-primary"
                  onClick={() => void patch({ cantidad: cantidadDe(cantidad) })}
                >
                  Guardar
                </button>
                <button className="button-ghost" onClick={() => setEditando(false)}>
                  Cancelar
                </button>
              </>
            ) : (
              <>
                <button className="button-primary" onClick={onAgregar}>
                  Agregar carteles
                </button>
                <button className="button-ghost" onClick={empezarEdicion}>
                  Editar
                </button>
                <button className="button-ghost" onClick={() => void patch({ activa: false })}>
                  Quitar
                </button>
              </>
            ))}
        </td>
      )}
    </tr>
  )
}
