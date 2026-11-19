export type TipoCliente = 'directo' | 'intermediario' | 'intermediario_formal'

export const TIPOS_CLIENTE: { value: TipoCliente; label: string }[] = [
  { value: 'directo', label: 'Cliente directo' },
  { value: 'intermediario', label: 'Intermediario (bolsero)' },
  { value: 'intermediario_formal', label: 'Central de medios' },
]

export type Rubro = { id: number; nombre: string; activo: boolean }

/** Grupo económico de marcas (RN-016). */
export type GrupoEconomico = { id: number; nombre: string; activo: boolean }

export type Cliente = {
  id: number
  nombre: string
  razon_social: string
  cuit: string
  /** `""` = sin tipo. */
  tipo: TipoCliente | ''
  tipo_nombre: string
  /** El nombre, o "Cliente sin nombre #<id>" si no tiene. */
  nombre_visible: string
  telefono: string
  correo: string
  activo: boolean
}

export type Marca = {
  id: number
  nombre: string
  cliente: number
  cliente_nombre: string
  rubro: number | null
  rubro_nombre: string | null
  grupo: number | null
  grupo_nombre: string | null
  activo: boolean
}

export type Contacto = {
  id: number
  cliente: number
  nombre: string
  cargo: string
  correo: string
  telefono: string
  notas: string
  rol: 'planificador' | 'asistente'
  planificador: number | null
  principal: boolean
  activo: boolean
}
