import { useEffect, useState } from 'react'
import type { KeyboardEvent } from 'react'
import { apiGet } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import type { Formato } from '../inventario/types'
import AgregarCarteles from '../reservas/AgregarCarteles'
import type { SeleccionAlta } from '../reservas/AgregarCarteles'

/** Línea de formato del alta, todavía sin guardar, con los carteles elegidos (HU-055, HU-056). */
export type LineaAlta = {
  formato: number
  formato_nombre: string
  cantidad: number | null
  seleccion: SeleccionAlta | null
}

type Props = {
  lineas: LineaAlta[]
  onCambio: (lineas: LineaAlta[]) => void
  /** Fechas del formulario: son las que propone "Agregar carteles" para la tanda. */
  fechaInicio: string
  fechaFin: string
}

function elegidos(linea: LineaAlta): number {
  return linea.seleccion?.carteles.length ?? 0
}

/** Posiciones por formato y carteles elegidos en "Nueva campaña", antes de guardarla. */
export default function PosicionesAlta({ lineas, onCambio, fechaInicio, fechaFin }: Props) {
  const [formatos, setFormatos] = useState<Formato[]>([])
  const [error, setError] = useState('')
  const [formato, setFormato] = useState('')
  const [cantidad, setCantidad] = useState('')
  const [errorAlta, setErrorAlta] = useState<string[]>([])
  const [agregando, setAgregando] = useState<number | null>(null)

  useEffect(() => {
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
  }, [])

  const usados = new Set(lineas.map((linea) => linea.formato))
  const disponibles = formatos.filter((item) => item.activo && !usados.has(item.id))
  const lineaAgregando = lineas.find((linea) => linea.formato === agregando)
  const total = lineas.reduce((suma, linea) => suma + elegidos(linea), 0)

  function agregarLinea() {
    const elegido = formatos.find((item) => String(item.id) === formato)
    if (!elegido) {
      setErrorAlta(['Elegí un formato.'])
      return
    }
    const numero = cantidad.trim() === '' ? null : Number(cantidad)
    if (numero !== null && (!Number.isInteger(numero) || numero < 1)) {
      setErrorAlta(['La cantidad tiene que ser un número entero mayor que cero.'])
      return
    }
    onCambio([
      ...lineas,
      { formato: elegido.id, formato_nombre: elegido.nombre, cantidad: numero, seleccion: null },
    ])
    setFormato('')
    setCantidad('')
    setErrorAlta([])
  }

  function cambiarLinea(formatoId: number, cambio: Partial<LineaAlta> | null) {
    onCambio(
      cambio === null
        ? lineas.filter((linea) => linea.formato !== formatoId)
        : lineas.map((linea) => (linea.formato === formatoId ? { ...linea, ...cambio } : linea)),
    )
    if (cambio === null && agregando === formatoId) setAgregando(null)
  }

  // La sección vive dentro del formulario de la campaña: Enter en un filtro no tiene que guardarla.
  function frenarEnter(event: KeyboardEvent<HTMLElement>) {
    if (event.key === 'Enter' && event.target instanceof HTMLInputElement) event.preventDefault()
  }

  return (
    <section
      className="card section-gap"
      aria-label="Posiciones por formato"
      onKeyDown={frenarEnter}
    >
      <h3>Posiciones por formato</h3>
      <p className="muted">
        Se guardan junto con la campaña, con una reserva por cada cartel elegido.
      </p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="form-grid" role="group" aria-label="Agregar línea de formato">
        <label>
          Formato
          <select value={formato} onChange={(event) => setFormato(event.target.value)}>
            <option value="">Elegí un formato</option>
            {disponibles.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
              </option>
            ))}
          </select>
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
        </label>
        <button type="button" className="button-ghost" onClick={agregarLinea}>
          Agregar línea
        </button>
        <FieldErrors messages={errorAlta} />
      </div>
      {lineas.length > 0 && (
        <table aria-label="Líneas de la nueva campaña">
          <thead>
            <tr>
              <th>Formato</th>
              <th>Solicitadas</th>
              <th>Carteles elegidos</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {lineas.map((linea) => (
              <tr key={linea.formato}>
                <td className="primary-cell">{linea.formato_nombre}</td>
                <td>{linea.cantidad ?? '—'}</td>
                <td>{elegidos(linea)}</td>
                <td>
                  <div className="row-actions">
                    <button
                      type="button"
                      className="button-ghost"
                      onClick={() => setAgregando(linea.formato)}
                    >
                      {elegidos(linea) > 0 ? 'Cambiar carteles' : 'Agregar carteles'}
                    </button>
                    <button
                      type="button"
                      className="button-ghost"
                      aria-label={`Quitar ${linea.formato_nombre}`}
                      onClick={() => cambiarLinea(linea.formato, null)}
                    >
                      Quitar
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {lineas.length > 0 && (
        <p className="costos-total">
          <strong>Carteles elegidos: {total}</strong>
        </p>
      )}
      {lineaAgregando && (
        <AgregarCarteles
          key={lineaAgregando.formato}
          campaniaId={null}
          fechaInicio={lineaAgregando.seleccion?.desde ?? fechaInicio}
          fechaFin={lineaAgregando.seleccion?.hasta ?? fechaFin}
          linea={{
            formato: lineaAgregando.formato,
            formato_nombre: lineaAgregando.formato_nombre,
            solicitadas: lineaAgregando.cantidad,
            reservadas: 0,
          }}
          seleccionInicial={lineaAgregando.seleccion?.carteles}
          onCerrar={() => setAgregando(null)}
          onElegir={(seleccion) => {
            cambiarLinea(lineaAgregando.formato, { seleccion })
            setAgregando(null)
          }}
        />
      )}
    </section>
  )
}
