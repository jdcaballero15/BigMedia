import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, apiGet, apiWrite } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import type { Costo, Margen, TipoCosto } from './types'
import { TIPOS_COSTO } from './types'
import { usePuedeEditar } from '../../shared/sesion'

export default function CostosReserva({ reservaId }: { reservaId: number }) {
  const puedeEditar = usePuedeEditar()
  const [costos, setCostos] = useState<Costo[]>([])
  const [margen, setMargen] = useState<Margen | null>(null)
  const [tipo, setTipo] = useState<TipoCosto>('impresion')
  const [monto, setMonto] = useState('')
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let active = true
    void Promise.all([
      apiGet<Costo[]>(`/api/costos/costos/?reserva=${reservaId}`),
      apiGet<Margen>(`/api/costos/margen/?reserva=${reservaId}`),
    ])
      .then(([costosRows, margenData]) => {
        if (active) {
          setCostos(costosRows)
          setMargen(margenData)
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los costos.')
      })
    return () => {
      active = false
    }
  }, [reservaId, revision])

  async function agregar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors({})
    try {
      await apiWrite('/api/costos/costos/', 'POST', {
        reserva: reservaId,
        tipo,
        monto: monto || '0',
      })
      setMonto('')
      setRevision((n) => n + 1)
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
    }
  }

  return (
    <div className="card section-gap">
      <h4>Costos y margen</h4>
      {margen && (
        <p>
          Ingreso {margen.ingreso} · Costo {margen.costo} · Margen {margen.margen}
          {margen.porcentaje !== null ? ` (${margen.porcentaje}%)` : ''}
        </p>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {costos.length > 0 && (
        <ul>
          {costos.map((costo) => (
            <li key={costo.id}>
              {costo.tipo_nombre}: {costo.monto}
              {costo.anulado ? ' (anulado)' : ''}
            </li>
          ))}
        </ul>
      )}
      {puedeEditar && (
        <form aria-label="Agregar costo" onSubmit={(event) => void agregar(event)}>
          <label>
            Tipo
            <select value={tipo} onChange={(event) => setTipo(event.target.value as TipoCosto)}>
              {TIPOS_COSTO.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Monto
            <input
              type="number"
              min="0"
              step="0.01"
              value={monto}
              onChange={(event) => setMonto(event.target.value)}
            />
            <FieldErrors messages={errors.monto} />
          </label>
          <button type="submit" className="button-primary">
            Agregar costo
          </button>
        </form>
      )}
    </div>
  )
}
