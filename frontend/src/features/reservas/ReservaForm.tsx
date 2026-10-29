import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../shared/api'
import CampoFecha from '../../shared/CampoFecha'
import { erroresDeFechas } from '../../shared/fechas'
import { FieldErrors } from '../../shared/FieldErrors'
import type { Cartel } from '../inventario/types'
import type { EstadoReserva, Reserva } from './types'
import { ESTADOS_INICIALES, ESTADOS_RESERVA } from './types'

export type ReservaInput = {
  campania: number
  cartel: number | null
  fecha_inicio: string
  fecha_fin: string
  estado: EstadoReserva
  precio_alquiler: string
  precio_impresion: string
  precio_fijacion: string
}

type Props = {
  campaniaId: number
  reserva?: Reserva | null
  carteles: Cartel[]
  onSave: (input: ReservaInput) => Promise<void>
  onCancel: () => void
}

export default function ReservaForm({ campaniaId, reserva, carteles, onSave, onCancel }: Props) {
  const [cartel, setCartel] = useState(String(reserva?.cartel ?? ''))
  const [fechaInicio, setFechaInicio] = useState(reserva?.fecha_inicio ?? '')
  const [fechaFin, setFechaFin] = useState(reserva?.fecha_fin ?? '')
  const [estado, setEstado] = useState<EstadoReserva>(reserva?.estado ?? 'pendiente')
  const [alquiler, setAlquiler] = useState(reserva?.precio_alquiler ?? '')
  const [impresion, setImpresion] = useState(reserva?.precio_impresion ?? '0')
  const [fijacion, setFijacion] = useState(reserva?.precio_fijacion ?? '0')
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [generalError, setGeneralError] = useState('')
  const [saving, setSaving] = useState(false)
  // Una reserva nueva nace Pendiente o Confirmada; al editar, el servidor valida la transición.
  const estadosOfrecidos = reserva
    ? ESTADOS_RESERVA
    : ESTADOS_RESERVA.filter((item) => ESTADOS_INICIALES.includes(item.value))

  function elegirCartel(value: string) {
    setCartel(value)
    // Al elegir el cartel en una reserva nueva, precargar su tarifa de lista (HU-029).
    if (!reserva) {
      const elegido = carteles.find((item) => String(item.id) === value)
      setAlquiler(elegido?.tarifa_lista ?? '')
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setGeneralError('')
    const fechasInvalidas = erroresDeFechas({ fecha_inicio: fechaInicio, fecha_fin: fechaFin })
    setErrors(fechasInvalidas)
    if (Object.keys(fechasInvalidas).length > 0) return
    setSaving(true)
    try {
      await onSave({
        campania: campaniaId,
        cartel: cartel ? Number(cartel) : null,
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        estado,
        precio_alquiler: alquiler || '0',
        precio_impresion: impresion || '0',
        precio_fijacion: fijacion || '0',
      })
    } catch (cause) {
      if (cause instanceof ApiError) {
        setErrors(cause.fields)
        // El conflicto de cupo (HU-032) viene como campo `disponibilidad`: se muestra tal cual.
        const conflicto = cause.fields.disponibilidad?.join(' ')
        setGeneralError(conflicto ?? cause.message)
      } else {
        setGeneralError(cause instanceof Error ? cause.message : 'No se pudo guardar la reserva.')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      className="card edit-form"
      aria-label="Formulario de reserva"
      noValidate
      onSubmit={(event) => void submit(event)}
    >
      <div className="form-heading">
        <h3>{reserva ? 'Editar reserva' : 'Nueva reserva'}</h3>
        <button type="button" className="button-ghost" onClick={onCancel}>
          Cancelar
        </button>
      </div>
      <div className="form-grid">
        <label>
          Cartel
          <select value={cartel} onChange={(event) => elegirCartel(event.target.value)}>
            <option value="">Seleccionar</option>
            {carteles
              .filter((item) => (item.operativo && !item.es_baja) || item.id === reserva?.cartel)
              .map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nombre_visible}
                  {item.es_baja ? ' (de baja)' : !item.operativo ? ' (fuera de servicio)' : ''}
                </option>
              ))}
          </select>
          <FieldErrors messages={errors.cartel} />
        </label>
        <label>
          Estado
          <select
            value={estado}
            onChange={(event) => setEstado(event.target.value as EstadoReserva)}
          >
            {estadosOfrecidos.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.estado} />
        </label>
        <CampoFecha
          label="Fecha de inicio"
          value={fechaInicio}
          onChange={setFechaInicio}
          errores={errors.fecha_inicio}
        />
        <CampoFecha
          label="Fecha de fin"
          value={fechaFin}
          onChange={setFechaFin}
          errores={errors.fecha_fin}
        />
        <label>
          Precio de alquiler
          <input
            type="number"
            min="0"
            step="0.01"
            value={alquiler}
            onChange={(event) => setAlquiler(event.target.value)}
          />
          <FieldErrors messages={errors.precio_alquiler} />
        </label>
        <label>
          Precio de impresión
          <input
            type="number"
            min="0"
            step="0.01"
            value={impresion}
            onChange={(event) => setImpresion(event.target.value)}
          />
          <FieldErrors messages={errors.precio_impresion} />
        </label>
        <label>
          Precio de fijación
          <input
            type="number"
            min="0"
            step="0.01"
            value={fijacion}
            onChange={(event) => setFijacion(event.target.value)}
          />
          <FieldErrors messages={errors.precio_fijacion} />
        </label>
      </div>
      {generalError && (
        <p className="error" role="alert">
          {generalError}
        </p>
      )}
      <button type="submit" className="button-primary" disabled={saving}>
        {saving ? 'Guardando…' : 'Guardar reserva'}
      </button>
    </form>
  )
}
