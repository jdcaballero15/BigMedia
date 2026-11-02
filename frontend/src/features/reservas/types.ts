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

/** Cartel con cupo libre para la tanda de "Agregar carteles" (HU-056). */
export type CartelTanda = {
  id: number
  nombre_visible: string
  zona_nombre: string
  proveedor_nombre: string | null
  tarifa_lista: string | null
  capacidad: number
  ocupados: number
  /** Pendientes de otras campañas que no bloquean el cupo (RN-002). */
  tentativas: number
  /** La campaña ya tiene una reserva de este cartel en el rango. */
  en_campania: boolean
}

/** Resumen de la creación en bloque (HU-057). */
export type ResultadoTanda = {
  creadas: { cartel: number; reserva: number }[]
  existentes: { cartel: number; reserva: number }[]
  fallidas: { cartel: number; motivo: string }[]
}

/** Resultado de "Confirmar reservas" (HU-059). */
export type ResultadoConfirmacion = {
  confirmadas: number[]
  conflictos: {
    reserva: number
    nombre: string
    cartel_nombre: string
    fecha_inicio: string
    fecha_fin: string
    ocupada_por: { campania: number; campania_nombre: string }[]
  }[]
}
