/** Nace Confirmada y el sistema lleva el estado: no hay Pendientes (HU-035). */
export type EstadoReserva = 'confirmada' | 'finalizada' | 'cancelada'

export const ESTADOS_RESERVA: { value: EstadoReserva; label: string }[] = [
  { value: 'confirmada', label: 'Confirmada' },
  { value: 'finalizada', label: 'Finalizada' },
  { value: 'cancelada', label: 'Cancelada' },
]

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
  /** Finalizada si es Confirmada y ya terminó, calculado por fecha (HU-036). */
  estado_visible: EstadoReserva
  precio_alquiler: string
  precio_impresion: string
  precio_fijacion: string
  total: string
  nombre: string
}

export type ParametrosDisponibilidad = {
  borde_inclusivo: boolean
  permitir_fecha_pasada: boolean
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
/** Resultado de cancelar una campaña con sus reservas (HU-024). */
export type ResultadoCancelacion = {
  campania: number
  estado: 'cancelada'
  canceladas: number[]
  terminadas: number[]
}

/** Reserva que ocupa un casillero en la vista Posiciones (HU-071). */
export type Ocupante = {
  reserva_id: number
  marca_id: number | null
  marca_nombre: string | null
  campania_id: number
  campania_nombre: string
  es_esta_campania: boolean
  estado: string
  fecha_inicio: string
  fecha_fin: string
}

/** Fila de la vista Posiciones: la de la tabla más los casilleros por slot (HU-071). */
export type FilaPosiciones = CartelTanda & {
  direccion: string
  lleno: boolean
  /** Uno por slot; reservas que se suceden comparten casillero. */
  slots: Ocupante[][]
}
