export type OcupacionCartel = {
  id: number
  nombre_visible: string
  formato_nombre: string
  zona_nombre: string
  modalidad: 'fija' | 'digital'
  capacidad: number
  ocupados: number
  libre: boolean
}

export type PeriodoCalendario = { clave: string; etiqueta: string }
export type CeldaCalendario = { periodo: string; ocupados: number }
export type FilaCalendario = {
  id: number
  nombre_visible: string
  formato_nombre: string
  zona_nombre: string
  capacidad: number
  celdas: CeldaCalendario[]
}
export type Calendario = { periodos: PeriodoCalendario[]; carteles: FilaCalendario[] }
