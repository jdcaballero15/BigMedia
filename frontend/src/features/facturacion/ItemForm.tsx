import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { vigentes } from '../../shared/opciones'
import type { Cliente } from '../clientes/types'
import type { CatalogosFacturacion, ItemFacturacion } from './types'

export type ItemInput = Record<string, string | number | null>

type Props = {
  item: ItemFacturacion | null
  /** Mes elegido en la lista (`AAAA-MM`): es el mes de un ítem nuevo. */
  mes: string
  clientes: Cliente[]
  catalogos: CatalogosFacturacion
  onSave: (input: ItemInput) => Promise<void>
  onCancel: () => void
}

type Datos = Record<string, string>

const CAMPOS_ID = ['cliente', 'sector', 'tipo_venta']
const IMPORTES = ['neto', 'costos_incluidos']

function datosIniciales(item: ItemFacturacion | null): Datos {
  const texto = (valor: string | number | null | undefined) =>
    valor === null || valor === undefined ? '' : String(valor)
  return {
    cliente: texto(item?.cliente),
    neto: texto(item?.neto),
    costos_incluidos: texto(item?.costos_incluidos),
    detalle_costo: item?.detalle_costo ?? '',
    tipo_venta: texto(item?.tipo_venta),
    sector: texto(item?.sector),
    tipo_soporte: item?.tipo_soporte ?? '',
  }
}

type Opcion = { id: number; nombre: string }

/** Opciones activas más la ya elegida aunque se haya inactivado, para no perderla al guardar. */
function conElegida(opciones: Opcion[], id: number | null | undefined, nombre?: string | null) {
  if (!id || opciones.some((opcion) => opcion.id === id)) return opciones
  return [...opciones, { id, nombre: `${nombre ?? `#${id}`} (inactivo)` }]
}

/** Lo que viaja a la API: vacío es null en IDs e importes; un ítem nuevo lleva el mes elegido. */
function aEntrada(datos: Datos, mesNuevo: string | null): ItemInput {
  const entrada: ItemInput = { ...datos }
  for (const campo of CAMPOS_ID) entrada[campo] = datos[campo] ? Number(datos[campo]) : null
  for (const campo of IMPORTES) entrada[campo] = datos[campo].trim() || null
  if (mesNuevo) entrada.mes = `${mesNuevo}-01`
  return entrada
}

/** Alta y edición de un ítem: solo los siete datos de la planilla de Administración (HU-060,
 * RN-024). Lo demás que ya tenga un ítem no viaja, así que no se pisa al editarlo. */
export default function ItemForm(props: Props) {
  const { item, mes, clientes, catalogos, onSave, onCancel } = props
  const [datos, setDatos] = useState<Datos>(() => datosIniciales(item))
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [generalError, setGeneralError] = useState('')
  const [saving, setSaving] = useState(false)

  const cambiar = (campo: string, valor: string) =>
    setDatos((actuales) => ({ ...actuales, [campo]: valor }))

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setGeneralError('')
    setErrors({})
    setSaving(true)
    try {
      await onSave(aEntrada(datos, item ? null : mes))
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
      setGeneralError(cause instanceof Error ? cause.message : 'No se pudo guardar el ítem.')
    } finally {
      setSaving(false)
    }
  }

  const campoTexto = (campo: string, etiqueta: string, extra: Record<string, unknown> = {}) => (
    <label>
      {etiqueta}
      <input
        value={datos[campo]}
        onChange={(event) => cambiar(campo, event.target.value)}
        {...extra}
      />
      <FieldErrors messages={errors[campo]} />
    </label>
  )

  const opciones = (lista: Opcion[]) =>
    lista.map((opcion) => (
      <option key={opcion.id} value={opcion.id}>
        {opcion.nombre}
      </option>
    ))

  return (
    <form
      className="card edit-form section-gap"
      aria-label="Formulario de ítem a facturar"
      noValidate
      onSubmit={(event) => void submit(event)}
    >
      <div className="form-heading">
        <h3>{item ? 'Editar ítem' : 'Nuevo ítem a facturar'}</h3>
        <button type="button" className="button-ghost" onClick={onCancel}>
          Cancelar
        </button>
      </div>
      <div className="form-grid">
        <label>
          Cliente (razón social)
          <select
            value={datos.cliente}
            onChange={(event) => cambiar('cliente', event.target.value)}
          >
            <option value="">Sin cliente</option>
            {vigentes(clientes, item?.cliente).map((c) => (
              <option key={c.id} value={c.id}>
                {c.razon_social || c.nombre_visible}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.cliente} />
        </label>
        {campoTexto('neto', 'Importe neto total', { inputMode: 'decimal' })}
        {campoTexto('costos_incluidos', 'Costos incluidos', { inputMode: 'decimal' })}
        {campoTexto('detalle_costo', 'Detalle costo')}
        <label>
          Tipo de venta
          <select
            value={datos.tipo_venta}
            onChange={(event) => cambiar('tipo_venta', event.target.value)}
          >
            <option value="">Sin definir</option>
            {opciones(conElegida(catalogos.tipos_venta, item?.tipo_venta, item?.tipo_venta_nombre))}
          </select>
          <FieldErrors messages={errors.tipo_venta} />
        </label>
        <label>
          Gob/Priv
          <select value={datos.sector} onChange={(event) => cambiar('sector', event.target.value)}>
            <option value="">Sin definir</option>
            {opciones(conElegida(catalogos.sectores, item?.sector, item?.sector_nombre))}
          </select>
          <FieldErrors messages={errors.sector} />
        </label>
        {campoTexto('tipo_soporte', 'Tipo')}
      </div>
      {generalError && (
        <p className="error" role="alert">
          {generalError}
        </p>
      )}
      <button type="submit" className="button-primary" disabled={saving}>
        {saving ? 'Guardando…' : 'Guardar ítem'}
      </button>
    </form>
  )
}
