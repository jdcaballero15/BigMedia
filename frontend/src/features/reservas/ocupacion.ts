export type PeriodoOcupacion = { clave: string; etiqueta: string }

export type CeldaOcupacion = {
  periodo: string
  porcentaje: number
  dias_ocupados: number
  dias_disponibles: number
}

export type CartelOcupacion = {
  id: number
  nombre_visible: string
  modalidad: string
  zona_nombre: string
  formato_nombre: string
  de_baja: boolean
  ocupacion: number
  celdas: CeldaOcupacion[]
}

export type ModalidadOcupacion = {
  modalidad: string
  etiqueta: string
  ocupacion: number
  por_mes: { periodo: string; porcentaje: number }[]
}

export type ReporteOcupacion = {
  periodos: PeriodoOcupacion[]
  carteles: CartelOcupacion[]
  modalidades: ModalidadOcupacion[]
}

const formateador = new Intl.NumberFormat('es-AR', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})

// Muestra una ocupación como porcentaje con un decimal.
/** Un cartel de baja figura solo si tuvo reservas en el período (HU-006); se marca. */
export function nombreCartel(cartel: CartelOcupacion): string {
  return cartel.de_baja ? `${cartel.nombre_visible} (de baja)` : cartel.nombre_visible
}

export function formatearPorcentaje(valor: number): string {
  return `${formateador.format(valor)} %`
}

// Fondo del mapa de calor: opacidad proporcional a la ocupación sobre el color de acento.
export function colorOcupacion(valor: number): string {
  const opacidad = (Math.min(Math.max(valor, 0), 100) / 100) * 0.85
  return `rgba(224, 138, 44, ${opacidad.toFixed(3)})`
}
