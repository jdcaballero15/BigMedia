import type { TipoCosto } from '../costos/types'

export type Periodo = { mes: string; etiqueta: string }

export type MarcaFila = {
  marca: number | null
  nombre: string
  total: string
  por_mes: Record<string, string>
}

export type ClienteFila = {
  cliente: number | null
  nombre: string
  total: string
  por_mes: Record<string, string>
  marcas: MarcaFila[]
}

export type ReporteIngresos = {
  periodos: Periodo[]
  clientes: ClienteFila[]
  total: string
}

export type EstadoItem = 'borrador' | 'enviado' | 'facturado' | 'anulado'

export const ESTADOS_ITEM: { value: EstadoItem; label: string }[] = [
  { value: 'borrador', label: 'Borrador' },
  { value: 'enviado', label: 'Enviado a facturar' },
  { value: 'facturado', label: 'Facturado' },
  { value: 'anulado', label: 'Anulado' },
]

export function etiquetaEstadoItem(estado: EstadoItem): string {
  return ESTADOS_ITEM.find((item) => item.value === estado)?.label ?? estado
}

export const TIPOS_SERVICIO = [
  { value: 'alquiler', label: 'Alquiler' },
  { value: 'impresion_colocacion', label: 'Impresión y colocación' },
  { value: 'otro', label: 'Otro' },
]

/** Ítem a facturar del mes (HU-060). Importes como texto decimal, tal como los da la API. */
export type ItemFacturacion = {
  id: number
  mes: string | null
  cliente: number | null
  cliente_nombre: string | null
  cuit_facturacion: string
  marca: number | null
  marca_nombre: string | null
  campania: number | null
  campania_nombre: string | null
  descripcion: string
  periodo_desde: string | null
  periodo_hasta: string | null
  cantidad: string | null
  precio_unitario: string | null
  neto: string | null
  alicuota_iva: string
  iva: string | null
  total: string | null
  costo_total: string
  neto_final: string | null
  tipo_servicio: string
  tipo_soporte: string
  sector: number | null
  sector_nombre: string | null
  tipo_venta: number | null
  tipo_venta_nombre: string | null
  notas: string
  estado: EstadoItem
  numero_factura: string
  orden_compra_numero: string
  orden_compra_fecha: string | null
  orden_compra_pdf: PdfOrdenCompra | null
  grupo: number | null
  grupo_codigo: string | null
  creado_por_nombre: string | null
}

/** PDF de la orden de compra (HU-062): la API informa nombre y tamaño, no el contenido. */
export type PdfOrdenCompra = { nombre: string; tamanio: number }

/** Ítems con el mismo número de OC: el servidor avisa y guarda igual (HU-062, criterio 2). */
export type AvisosItem = { orden_compra: { id: number; descripcion: string }[] }

export type ItemGuardado = ItemFacturacion & { avisos: AvisosItem }

export function urlPdfOrdenCompra(itemId: number): string {
  return `/api/facturacion/items/${itemId}/orden-compra-pdf/`
}

export type TotalesMes = {
  mes: string
  cantidad: number
  neto: string
  iva: string
  total: string
  costos: string
  neto_final: string
}

/** Costo de un ítem (HU-063): propio (sin reserva) o de una reserva de su campaña, vinculado. */
export type CostoDelItem = {
  id: number
  tipo: TipoCosto
  tipo_nombre: string
  proveedor: number | null
  proveedor_nombre: string | null
  destinatario: string
  porcentaje: string | null
  monto: string
  fecha: string
  reserva: number | null
  cartel_nombre: string | null
  anulado: boolean
  motivo_anulacion: string
}

export function urlCostosDelItem(itemId: number): string {
  return `/api/facturacion/items/${itemId}/costos/`
}

export type CatalogosFacturacion = {
  sectores: { id: number; nombre: string }[]
  tipos_venta: { id: number; nombre: string }[]
}

/** Mes actual como "aaaa-mm", el formato del filtro y del campo de mes. */
export function mesActual(hoy: Date = new Date()): string {
  return `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}`
}

/** Envío a facturar de un mes (HU-066). */
export type EnvioFacturacion = {
  id: number
  mes: string
  enviado_por_nombre: string
  enviado_en: string
  items: number[]
  cantidad: number
}

export type ResultadoEnvio = {
  envio: EnvioFacturacion | null
  incompletos: { item: number; descripcion: string; faltan: string[] }[]
}
