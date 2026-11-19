import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { vigentes } from '../../shared/opciones'
import type { Cliente } from '../clientes/types'
import CostosDelItem from './CostosDelItem'
import { detalleElegidos, sumaElegidos } from './montos'
import OrdenPublicidadItem from './OrdenPublicidadItem'
import type { CatalogosFacturacion, CostoElegible, ItemFacturacion } from './types'

export type ItemInput = Record<string, string | number | number[] | null>

type Props = {
  item: ItemFacturacion | null
  /** Mes elegido en la lista (`AAAA-MM`): es el mes de un ítem nuevo. */
  mes: string
  clientes: Cliente[]
  catalogos: CatalogosFacturacion
  /** Guarda el ítem con sus costos elegidos y, si se adjuntó, el PDF de la orden de publicidad. */
  onSave: (input: ItemInput, ordenPublicidad: File | null) => Promise<void>
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

/** Lo que viaja a la API: vacío es null en IDs e importes; un ítem nuevo lleva el mes elegido.
 * Con costos elegidos, los costos incluidos y el detalle los calcula el servidor (HU-060). */
function aEntrada(datos: Datos, mesNuevo: string | null, elegidos: CostoElegible[]): ItemInput {
  const entrada: ItemInput = { ...datos }
  for (const campo of CAMPOS_ID) entrada[campo] = datos[campo] ? Number(datos[campo]) : null
  for (const campo of IMPORTES) entrada[campo] = datos[campo].trim() || null
  if (sumaElegidos(elegidos) !== null) {
    delete entrada.costos_incluidos
    delete entrada.detalle_costo
  }
  entrada.costos = elegidos.map((costo) => costo.id)
  if (mesNuevo) entrada.mes = `${mesNuevo}-01`
  return entrada
}

/** Alta y edición de un ítem: los siete datos de la planilla de Administración (HU-060, RN-024),
 * la orden de publicidad (HU-062) y los costos elegidos (HU-063), todo en un solo guardado. Lo
 * demás que ya tenga un ítem no viaja, así que no se pisa al editarlo. */
export default function ItemForm(props: Props) {
  const { item, mes, clientes, catalogos, onSave, onCancel } = props
  const [datos, setDatos] = useState<Datos>(() => datosIniciales(item))
  const [elegidos, setElegidos] = useState<CostoElegible[]>(item?.costos_elegidos ?? [])
  const [ordenPublicidad, setOrdenPublicidad] = useState<File | null>(null)
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
      await onSave(aEntrada(datos, item ? null : mes, elegidos), ordenPublicidad)
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

  // Con costos elegidos, se ven calculados y no se escriben (HU-060).
  const suma = sumaElegidos(elegidos)
  const campoCalculado = (campo: string, etiqueta: string, valor: string) => (
    <label>
      {etiqueta}
      <input value={valor} readOnly aria-label={etiqueta} />
      <small className="muted">Se calcula con los costos elegidos.</small>
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
        {suma === null
          ? campoTexto('costos_incluidos', 'Costos incluidos', { inputMode: 'decimal' })
          : campoCalculado('costos_incluidos', 'Costos incluidos', suma)}
        {suma === null
          ? campoTexto('detalle_costo', 'Detalle costo')
          : campoCalculado('detalle_costo', 'Detalle costo', detalleElegidos(elegidos))}
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
      <OrdenPublicidadItem
        itemId={item?.id ?? null}
        pdf={item?.orden_compra_pdf ?? null}
        archivo={ordenPublicidad}
        onElegir={setOrdenPublicidad}
        errores={errors.orden_publicidad}
      />
      <CostosDelItem elegidos={elegidos} onCambiar={setElegidos} errores={errors.costos} />
      {/* El formulario es largo: guardar queda fijo abajo de la pantalla mientras se completa. */}
      <div className="acciones-fijas">
        {generalError && (
          <p className="error" role="alert">
            {generalError}
          </p>
        )}
        <button type="submit" className="button-primary" disabled={saving}>
          {saving ? 'Guardando…' : 'Guardar ítem'}
        </button>
      </div>
    </form>
  )
}
