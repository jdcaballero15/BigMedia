export type EstadoReserva = 'pendiente' | 'confirmada' | 'finalizada' | 'cancelada'

export const ESTADOS_RESERVA: { value: EstadoReserva; label: string }[] = [
  { value: 'pendiente', label: 'Pendiente' },
  { value: 'confirmada', label: 'Confirmada' },
  { value: 'finalizada', label: 'Finalizada' },
  { value: 'cancelada', label: 'Cancelada' },
]

/** Estados con los que puede nacer una reserva (HU-035). */
export const ESTADOS_INICIALES: EstadoReserva[] = ['pendiente', 'confirmada']

export function etiquetaEstadoReserva(estado: EstadoReserva): string {
  return ESTADOS_RESERVA.find((item) => item.value === estado)?.label ?? estado
}

export type Reserva = {
  id: number
  campania: number
  campania_nombre: string
  cartel: number
  cartel_nombre: string
  fecha_inicio: string
  fecha_fin: string
  estado: EstadoReserva
  precio_alquiler: string
  precio_impresion: string
  precio_fijacion: string
  total: string
  nombre: string
}

export type ParametrosDisponibilidad = {
  borde_inclusivo: boolean
  tentativa_bloquea: boolean
}
