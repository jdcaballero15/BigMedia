export type RegistroAuditoria = {
  id: number
  entidad: string
  entidad_id: number
  campo: string
  valor_anterior: string | null
  valor_nuevo: string | null
  usuario: number | null
  usuario_nombre: string
  origen: string
  momento: string
}

export type UsuarioAuditoria = {
  id: number
  nombre: string
}
