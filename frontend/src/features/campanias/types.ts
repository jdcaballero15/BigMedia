export type EstadoCampania = 'cotizada' | 'confirmada' | 'cancelada' | 'perdida'

export const ESTADOS_CAMPANIA: { value: EstadoCampania; label: string }[] = [
  { value: 'cotizada', label: 'Cotizada' },
  { value: 'confirmada', label: 'Confirmada' },
  { value: 'cancelada', label: 'Cancelada' },
  { value: 'perdida', label: 'Perdida' },
]

export function etiquetaEstado(estado: EstadoCampania): string {
  return ESTADOS_CAMPANIA.find((item) => item.value === estado)?.label ?? estado
}

export type Campania = {
  id: number
  nombre: string
  marca: number | null
  marca_nombre: string | null
  cliente_facturacion: number | null
  cliente_factura: number | null
  cliente_factura_nombre: string
  fecha_inicio: string | null
  fecha_fin: string | null
  estado: EstadoCampania
}

export type TipoInteraccion = 'reunion' | 'llamada'

export const TIPOS_INTERACCION: { value: TipoInteraccion; label: string }[] = [
  { value: 'llamada', label: 'Llamada' },
  { value: 'reunion', label: 'Reunión' },
]

export function etiquetaTipoInteraccion(tipo: TipoInteraccion): string {
  return TIPOS_INTERACCION.find((item) => item.value === tipo)?.label ?? tipo
}

/** Reunión o llamada comercial con un cliente (HU-020). */
export type Interaccion = {
  id: number
  tipo: TipoInteraccion
  asunto: string
  fecha: string
  notas: string
  cliente: number
  cliente_nombre: string
  contacto: number | null
  contacto_nombre: string | null
  campania: number | null
  campania_nombre: string | null
  registrada_por_nombre: string | null
}
