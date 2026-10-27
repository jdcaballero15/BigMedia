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
  tipo_servicio: string
  tipo_soporte: string
  sector: number | null
  sector_nombre: string | null
  tipo_venta: number | null
  tipo_venta_nombre: string | null
  notas: string
  estado: EstadoItem
  numero_factura: string
  creado_por_nombre: string | null
}

export type TotalesMes = {
  mes: string
  cantidad: number
  neto: string
  iva: string
  total: string
}

export type CatalogosFacturacion = {
  sectores: { id: number; nombre: string }[]
  tipos_venta: { id: number; nombre: string }[]
}

/** Mes actual como "aaaa-mm", el formato del filtro y del campo de mes. */
export function mesActual(hoy: Date = new Date()): string {
  return `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}`
}
