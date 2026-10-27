import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, apiGet } from '../../shared/api'
import CampoFecha from '../../shared/CampoFecha'
import { erroresDeFechas } from '../../shared/fechas'
import { FieldErrors } from '../../shared/FieldErrors'
import { vigentes } from '../../shared/opciones'
import type { Campania } from '../campanias/types'
import type { Cliente, Marca } from '../clientes/types'
import type { CatalogosFacturacion, ItemFacturacion } from './types'
import { TIPOS_SERVICIO, mesActual } from './types'

export type ItemInput = Record<string, string | number | null>

type Props = {
  item: ItemFacturacion | null
  clientes: Cliente[]
  marcas: Marca[]
  campanias: Campania[]
  catalogos: CatalogosFacturacion
  onSave: (input: ItemInput) => Promise<void>
  onCancel: () => void
}

type Datos = Record<string, string>

const CAMPOS_ID = ['cliente', 'marca', 'campania', 'sector', 'tipo_venta']
const CAMPOS_NULLABLES = ['cantidad', 'precio_unitario', 'neto', 'periodo_desde', 'periodo_hasta']

function datosIniciales(item: ItemFacturacion | null): Datos {
  const texto = (valor: string | number | null | undefined) =>
    valor === null || valor === undefined ? '' : String(valor)
  return {
    mes: item ? texto(item.mes).slice(0, 7) : mesActual(),
    cliente: texto(item?.cliente),
    cuit_facturacion: item?.cuit_facturacion ?? '',
    marca: texto(item?.marca),
    campania: texto(item?.campania),
    descripcion: item?.descripcion ?? '',
    periodo_desde: texto(item?.periodo_desde),
    periodo_hasta: texto(item?.periodo_hasta),
    cantidad: texto(item?.cantidad),
    precio_unitario: texto(item?.precio_unitario),
    neto: texto(item?.neto),
    alicuota_iva: item?.alicuota_iva ?? '21.00',
    tipo_servicio: item?.tipo_servicio ?? '',
    tipo_soporte: item?.tipo_soporte ?? '',
    sector: texto(item?.sector),
    tipo_venta: texto(item?.tipo_venta),
    notas: item?.notas ?? '',
  }
}

type Opcion = { id: number; nombre: string }

/** Opciones activas más la ya elegida aunque se haya inactivado, para no perderla al guardar. */
function conElegida(opciones: Opcion[], id: number | null | undefined, nombre?: string | null) {
  if (!id || opciones.some((opcion) => opcion.id === id)) return opciones
  return [...opciones, { id, nombre: `${nombre ?? `#${id}`} (inactivo)` }]
}

/** Lo que viaja a la API: vacío es null en IDs, importes y fechas; el mes, su primer día. */
function aEntrada(datos: Datos): ItemInput {
  const entrada: ItemInput = { ...datos, mes: datos.mes ? `${datos.mes}-01` : null }
  for (const campo of CAMPOS_ID) entrada[campo] = datos[campo] ? Number(datos[campo]) : null
  for (const campo of CAMPOS_NULLABLES) entrada[campo] = datos[campo].trim() || null
  return entrada
}

/** Alta y edición de un ítem a facturar, con las precargas de HU-060 (criterios 3 y 4). */
export default function ItemForm(props: Props) {
  const { item, clientes, marcas, campanias, catalogos, onSave, onCancel } = props
  const [datos, setDatos] = useState<Datos>(() => datosIniciales(item))
  const [netoTocado, setNetoTocado] = useState(false)
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [generalError, setGeneralError] = useState('')
  const [saving, setSaving] = useState(false)

  const cambiar = (campo: string, valor: string) =>
    setDatos((actuales) => ({ ...actuales, [campo]: valor }))

  /** Cambiar cantidad o precio vacía el neto que no se cargó a mano: lo recalcula el servidor. */
  function cambiarBase(campo: string, valor: string) {
    setDatos((actuales) => ({ ...actuales, [campo]: valor, ...(netoTocado ? {} : { neto: '' }) }))
  }

  /** Precarga el CUIT del cliente si el ítem todavía no tiene uno (criterio 3). */
  function elegirCliente(valor: string) {
    const cuit = clientes.find((c) => String(c.id) === valor)?.cuit ?? ''
    setDatos((actuales) => ({
      ...actuales,
      cliente: valor,
      cuit_facturacion: actuales.cuit_facturacion || cuit,
    }))
  }

  /** Precarga cliente, marca y soporte de la campaña sin pisar lo ya cargado (criterio 4). */
  async function elegirCampania(valor: string) {
    cambiar('campania', valor)
    const campania = campanias.find((c) => String(c.id) === valor)
    if (!campania) return
    const cliente = clientes.find((c) => c.id === campania.cliente_factura)
    setDatos((actuales) => ({
      ...actuales,
      cliente: actuales.cliente || String(campania.cliente_factura ?? ''),
      cuit_facturacion: actuales.cuit_facturacion || (cliente?.cuit ?? ''),
      marca: actuales.marca || String(campania.marca ?? ''),
    }))
    const lineas = await apiGet<{ formato_nombre: string }[]>(
      `/api/campanias/lineas-formato/?campania=${campania.id}`,
    ).catch(() => [])
    const soporte = lineas.map((linea) => linea.formato_nombre).join(', ')
    setDatos((actuales) => ({ ...actuales, tipo_soporte: actuales.tipo_soporte || soporte }))
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setGeneralError('')
    const fechasInvalidas = erroresDeFechas({
      periodo_desde: datos.periodo_desde,
      periodo_hasta: datos.periodo_hasta,
    })
    setErrors(fechasInvalidas)
    if (Object.keys(fechasInvalidas).length > 0) return
    setSaving(true)
    try {
      await onSave(aEntrada(datos))
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
        {campoTexto('mes', 'Mes de facturación', { type: 'month' })}
        <label>
          Campaña
          <select
            value={datos.campania}
            onChange={(event) => void elegirCampania(event.target.value)}
          >
            <option value="">Sin campaña</option>
            {campanias.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre || `Campaña #${c.id}`}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.campania} />
        </label>
        <label>
          Cliente que factura
          <select value={datos.cliente} onChange={(event) => elegirCliente(event.target.value)}>
            <option value="">Sin cliente</option>
            {vigentes(clientes, item?.cliente).map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre_visible}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.cliente} />
        </label>
        {campoTexto('cuit_facturacion', 'CUIT de facturación')}
        <label>
          Marca
          <select value={datos.marca} onChange={(event) => cambiar('marca', event.target.value)}>
            <option value="">Sin marca</option>
            {vigentes(marcas, item?.marca).map((m) => (
              <option key={m.id} value={m.id}>
                {m.nombre}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.marca} />
        </label>
        <label>
          Tipo de servicio
          <select
            value={datos.tipo_servicio}
            onChange={(event) => cambiar('tipo_servicio', event.target.value)}
          >
            <option value="">Sin definir</option>
            {TIPOS_SERVICIO.map((tipo) => (
              <option key={tipo.value} value={tipo.value}>
                {tipo.label}
              </option>
            ))}
          </select>
        </label>
        {campoTexto('descripcion', 'Descripción del servicio')}
        <CampoFecha
          label="Período desde"
          value={datos.periodo_desde}
          onChange={(valor) => cambiar('periodo_desde', valor)}
          errores={errors.periodo_desde}
        />
        <CampoFecha
          label="Período hasta"
          value={datos.periodo_hasta}
          onChange={(valor) => cambiar('periodo_hasta', valor)}
          errores={errors.periodo_hasta}
        />
        <label>
          Cantidad
          <input
            inputMode="decimal"
            value={datos.cantidad}
            onChange={(event) => cambiarBase('cantidad', event.target.value)}
          />
          <FieldErrors messages={errors.cantidad} />
        </label>
        <label>
          Precio unitario
          <input
            inputMode="decimal"
            value={datos.precio_unitario}
            onChange={(event) => cambiarBase('precio_unitario', event.target.value)}
          />
          <FieldErrors messages={errors.precio_unitario} />
        </label>
        <label>
          Importe neto
          <input
            inputMode="decimal"
            aria-label="Importe neto"
            value={datos.neto}
            placeholder="Cantidad × precio"
            onChange={(event) => {
              setNetoTocado(true)
              cambiar('neto', event.target.value)
            }}
          />
          <small className="muted">Vacío: se calcula como cantidad × precio unitario.</small>
          <FieldErrors messages={errors.neto} />
        </label>
        {campoTexto('alicuota_iva', 'Alícuota de IVA (%)', { inputMode: 'decimal' })}
        {campoTexto('tipo_soporte', 'Tipo de soporte')}
        <label>
          Gob/Priv
          <select value={datos.sector} onChange={(event) => cambiar('sector', event.target.value)}>
            <option value="">Sin definir</option>
            {conElegida(catalogos.sectores, item?.sector, item?.sector_nombre).map((s) => (
              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.sector} />
        </label>
        <label>
          Tipo de venta
          <select
            value={datos.tipo_venta}
            onChange={(event) => cambiar('tipo_venta', event.target.value)}
          >
            <option value="">Sin definir</option>
            {conElegida(catalogos.tipos_venta, item?.tipo_venta, item?.tipo_venta_nombre).map(
              (t) => (
                <option key={t.id} value={t.id}>
                  {t.nombre}
                </option>
              ),
            )}
          </select>
          <FieldErrors messages={errors.tipo_venta} />
        </label>
        <label className="wide">
          Notas para Administración
          <textarea
            value={datos.notas}
            onChange={(event) => cambiar('notas', event.target.value)}
          />
        </label>
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
