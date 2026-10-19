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
