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
  cliente_razon_social: string | null
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
  /** Con costos elegidos, la suma y los tipos calculados por el servidor (HU-060). */
  costos_incluidos: string | null
  detalle_costo: string
  costos_calculados: boolean
  costos_elegidos: CostoElegible[]
  notas: string
  orden_compra_numero: string
  orden_compra_fecha: string | null
  orden_compra_pdf: PdfOrdenCompra | null
  grupo: number | null
  grupo_codigo: string | null
  creado_por_nombre: string | null
}

/** PDF del ítem (HU-062), «Orden de publicidad» en pantalla: la API informa nombre y tamaño. */
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

/** Costo que se puede elegir en un ítem, o ya elegido (HU-063), con su campaña y su cartel. */
export type CostoElegible = {
  id: number
  tipo: TipoCosto
  tipo_nombre: string
  monto: string
  fecha: string
  anulado: boolean
  a_quien: string
  campania_nombre: string | null
  cartel_nombre: string | null
  /** Propio del ítem (sin reserva): no se quita, se anula. */
  propio: boolean
}

export const URL_COSTOS_ELEGIBLES = '/api/facturacion/items/costos-elegibles/'

export type CatalogosFacturacion = {
  sectores: { id: number; nombre: string }[]
  tipos_venta: { id: number; nombre: string }[]
}

/** Mes actual como "aaaa-mm", el formato del filtro y del campo de mes. */
export function mesActual(hoy: Date = new Date()): string {
  return `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}`
}
