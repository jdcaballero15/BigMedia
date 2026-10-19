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
