import type { Rol } from '../../shared/sesion'

export type Usuario = {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  rol: Rol
  es_gerencia: boolean
  activo: boolean
  tiene_clave: boolean
  last_login: string | null
}

export const ETIQUETAS_ROL: Record<Rol, string> = {
  administrador: 'Administrador',
  operativo: 'Operativo',
  lectura: 'Lectura',
}
