import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { vigentes } from '../../shared/opciones'
import type { Cartel, Catalogo, Estado, Formato, Proveedor } from './types'

export type CartelInput = {
  formato: number
  zona: number
  proveedor: number | null
  estado: number
  direccion: string
  tamano: string
  capacidad: number
  tarifa_lista: string | null
  foto_url: string
}

type Props = {
  cartel?: Cartel | null
  formatos: Formato[]
  zonas: Catalogo[]
  proveedores: Proveedor[]
  estados: Estado[]
  onSave: (input: CartelInput) => Promise<void>
  onCancel: () => void
}

export default function CartelForm({
  cartel,
  formatos,
  zonas,
  proveedores,
  estados,
  onSave,
  onCancel,
}: Props) {
  const [formato, setFormato] = useState(String(cartel?.formato ?? ''))
  const [zona, setZona] = useState(String(cartel?.zona ?? ''))
  const [proveedor, setProveedor] = useState(String(cartel?.proveedor ?? ''))
  const [estado, setEstado] = useState(
    String(
      cartel?.estado ??
        estados.find((item) => item.codigo === 'activo' && item.activo !== false)?.id ??
        '',
    ),
  )
  const [direccion, setDireccion] = useState(cartel?.direccion ?? '')
  const [tamano, setTamano] = useState(cartel?.tamano ?? '')
  const [capacidad, setCapacidad] = useState(String(cartel?.capacidad ?? ''))
  const [tarifa, setTarifa] = useState(cartel?.tarifa_lista ?? '')
  const [fotoUrl, setFotoUrl] = useState(cartel?.foto_url ?? '')
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [generalError, setGeneralError] = useState('')
  const [saving, setSaving] = useState(false)

  function changeFormato(value: string) {
    setFormato(value)
    if (!cartel) {
      const selected = formatos.find((item) => String(item.id) === value)
      setCapacidad(selected ? String(selected.capacidad_predeterminada) : '')
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors({})
    setGeneralError('')
    setSaving(true)
    try {
      await onSave({
        formato: Number(formato),
        zona: Number(zona),
        proveedor: proveedor ? Number(proveedor) : null,
        estado: Number(estado),
        direccion: direccion.trim(),
        tamano: tamano.trim(),
        capacidad: Number(capacidad),
        tarifa_lista: tarifa.trim() || null,
        foto_url: fotoUrl.trim(),
      })
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
      setGeneralError(cause instanceof Error ? cause.message : 'No se pudo guardar el cartel.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      className="card edit-form"
      aria-label="Formulario de cartel"
      onSubmit={(event) => void submit(event)}
    >
      <div className="form-heading">
        <h3>{cartel ? 'Editar cartel' : 'Nuevo cartel'}</h3>
        <button type="button" className="button-ghost" onClick={onCancel}>
          Cancelar
        </button>
      </div>
      <div className="form-grid">
        <label>
          Formato
          <select value={formato} onChange={(event) => changeFormato(event.target.value)} required>
            <option value="">Seleccionar</option>
            {vigentes(formatos, cartel?.formato).map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
                {item.activo === false ? ' (inactivo)' : ''}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.formato} />
        </label>
        <label>
          Zona
          <select value={zona} onChange={(event) => setZona(event.target.value)} required>
            <option value="">Seleccionar</option>
            {vigentes(zonas, cartel?.zona).map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
                {item.activo === false ? ' (inactivo)' : ''}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.zona} />
        </label>
        <label>
          Dirección
          <input
            value={direccion}
            onChange={(event) => setDireccion(event.target.value)}
            required
          />
          <FieldErrors messages={errors.direccion} />
        </label>
        <label>
          Tamaño
          <input
            value={tamano}
            onChange={(event) => setTamano(event.target.value)}
            placeholder="Ej. 6 x 3 m"
          />
          <FieldErrors messages={errors.tamano} />
        </label>
        <label>
          Capacidad
          <input
            type="number"
            min="1"
            value={capacidad}
            onChange={(event) => setCapacidad(event.target.value)}
            required
          />
          <FieldErrors messages={errors.capacidad} />
        </label>
        <label>
          Tarifa de lista
          <input
            type="number"
            min="0"
            step="0.01"
            value={tarifa}
            onChange={(event) => setTarifa(event.target.value)}
            placeholder="Sin definir"
          />
          <FieldErrors messages={errors.tarifa_lista} />
        </label>
        <label>
          Proveedor
          <select value={proveedor} onChange={(event) => setProveedor(event.target.value)}>
            <option value="">Sin proveedor</option>
            {vigentes(proveedores, cartel?.proveedor).map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
                {item.activo === false ? ' (inactivo)' : ''}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.proveedor} />
        </label>
        <label>
          Estado
          <select value={estado} onChange={(event) => setEstado(event.target.value)} required>
            <option value="">Seleccionar</option>
            {vigentes(estados, cartel?.estado).map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
                {item.activo === false ? ' (inactivo)' : ''}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.estado} />
        </label>
        <label className="wide">
          Enlace de foto
          <input
            type="url"
            value={fotoUrl}
            onChange={(event) => setFotoUrl(event.target.value)}
            placeholder="https://…"
          />
          <FieldErrors messages={errors.foto_url} />
        </label>
      </div>
      {generalError && (
        <p className="error" role="alert">
          {generalError}
        </p>
      )}
      <button type="submit" className="button-primary" disabled={saving}>
        {saving ? 'Guardando…' : 'Guardar cartel'}
      </button>
    </form>
  )
}
