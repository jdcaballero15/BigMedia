export type Catalogo = { id: number; nombre: string; activo?: boolean }
export type Formato = Catalogo & {
  modalidad: 'fija' | 'digital'
  capacidad_predeterminada: number
  ancho: string | null
  alto: string | null
}
export type Estado = Catalogo & { codigo: string; operativo: boolean; es_baja: boolean }
export type Proveedor = Catalogo & { servicio: string }

export type Cartel = {
  id: number
  formato: number
  formato_nombre: string
  zona: number
  zona_nombre: string
  proveedor: number | null
  proveedor_nombre: string | null
  estado: number
  estado_nombre: string
  es_baja: boolean
  operativo: boolean
  direccion: string
  tamano: string
  capacidad: number
  tarifa_lista: string | null
  foto_url: string
  nombre_visible: string
}
