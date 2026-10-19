import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { vigentes } from '../../shared/opciones'
import MarcaForm from '../clientes/MarcaForm'
import type { MarcaInput } from '../clientes/MarcaForm'
import type { Cliente, Marca, Rubro } from '../clientes/types'
import type { Campania, EstadoCampania } from './types'
import { ESTADOS_CAMPANIA } from './types'

export type CampaniaInput = {
  nombre: string
  marca: number | null
  cliente_facturacion: number | null
  fecha_inicio: string | null
  fecha_fin: string | null
  estado: EstadoCampania
}

type Props = {
  campania?: Campania | null
  marcas: Marca[]
  clientes: Cliente[]
  rubros: Rubro[]
  onSave: (input: CampaniaInput) => Promise<void>
  onCrearMarca: (input: MarcaInput) => Promise<Marca>
  onCancel: () => void
}

export default function CampaniaForm({
  campania,
  marcas,
  clientes,
  rubros,
  onSave,
  onCrearMarca,
  onCancel,
}: Props) {
  const [nombre, setNombre] = useState(campania?.nombre ?? '')
  const [marca, setMarca] = useState(String(campania?.marca ?? ''))
  const [clienteFacturacion, setClienteFacturacion] = useState(
    String(campania?.cliente_facturacion ?? ''),
  )
  const [fechaInicio, setFechaInicio] = useState(campania?.fecha_inicio ?? '')
  const [fechaFin, setFechaFin] = useState(campania?.fecha_fin ?? '')
  const [estado, setEstado] = useState<EstadoCampania>(campania?.estado ?? 'cotizada')
  const [marcasLocales, setMarcasLocales] = useState<Marca[]>([])
  const [creandoMarca, setCreandoMarca] = useState(false)

  // Las marcas creadas al vuelo se muestran aunque el padre todavía no refrescó su lista.
  const opcionesMarca = [...marcas, ...marcasLocales].filter(
    (item, indice, todas) => todas.findIndex((otra) => otra.id === item.id) === indice,
  )
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [generalError, setGeneralError] = useState('')
  const [saving, setSaving] = useState(false)

  async function crearMarca(input: MarcaInput) {
    const creada = await onCrearMarca(input)
    setMarcasLocales((actuales) => [...actuales, creada])
    setMarca(String(creada.id))
    setCreandoMarca(false)
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors({})
    setGeneralError('')
    setSaving(true)
    try {
      await onSave({
        nombre: nombre.trim(),
        marca: marca ? Number(marca) : null,
        cliente_facturacion: clienteFacturacion ? Number(clienteFacturacion) : null,
        fecha_inicio: fechaInicio || null,
        fecha_fin: fechaFin || null,
        estado,
      })
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
      setGeneralError(cause instanceof Error ? cause.message : 'No se pudo guardar la campaña.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      className="card edit-form"
      aria-label="Formulario de campaña"
      noValidate
      onSubmit={(event) => void submit(event)}
    >
      <div className="form-heading">
        <h3>{campania ? 'Editar campaña' : 'Nueva campaña'}</h3>
        <button type="button" className="button-ghost" onClick={onCancel}>
          Cancelar
        </button>
      </div>
      <div className="form-grid">
        <label>
          Nombre
          <input value={nombre} onChange={(event) => setNombre(event.target.value)} />
          <FieldErrors messages={errors.nombre} />
        </label>
        <label>
          Marca
          <select value={marca} onChange={(event) => setMarca(event.target.value)}>
            <option value="">Sin marca</option>
            {vigentes(opcionesMarca, campania?.marca).map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
                {item.activo ? '' : ' (inactiva)'}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.marca} />
        </label>
        <label>
          Cliente que factura (propio)
          <select
            value={clienteFacturacion}
            onChange={(event) => setClienteFacturacion(event.target.value)}
          >
            <option value="">Según la marca</option>
            {vigentes(clientes, campania?.cliente_facturacion).map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre_visible}
                {item.activo ? '' : ' (inactivo)'}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.cliente_facturacion} />
        </label>
        <label>
          Estado
          <select
            value={estado}
            onChange={(event) => setEstado(event.target.value as EstadoCampania)}
          >
            {ESTADOS_CAMPANIA.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.estado} />
        </label>
        <label>
          Fecha de inicio
          <input
            type="date"
            value={fechaInicio}
            onChange={(event) => setFechaInicio(event.target.value)}
          />
          <FieldErrors messages={errors.fecha_inicio} />
        </label>
        <label>
          Fecha de fin
          <input
            type="date"
            value={fechaFin}
            onChange={(event) => setFechaFin(event.target.value)}
          />
          <FieldErrors messages={errors.fecha_fin} />
        </label>
      </div>
      {creandoMarca ? (
        <MarcaForm
          clientes={clientes}
          rubros={rubros}
          onSave={crearMarca}
          onCancel={() => setCreandoMarca(false)}
        />
      ) : (
        <button type="button" className="button-ghost" onClick={() => setCreandoMarca(true)}>
          Nueva marca
        </button>
      )}
      {generalError && (
        <p className="error" role="alert">
          {generalError}
        </p>
      )}
      <button type="submit" className="button-primary" disabled={saving}>
        {saving ? 'Guardando…' : 'Guardar campaña'}
      </button>
    </form>
  )
}
