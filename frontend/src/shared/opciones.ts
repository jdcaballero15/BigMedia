type ConEstado = { id: number; activo?: boolean }

/** Opciones activas más la ya elegida, aunque esté inactiva, para no perderla al editar. */
export function vigentes<T extends ConEstado>(rows: T[], selected: number | null | undefined): T[] {
  return rows.filter((item) => item.activo !== false || item.id === selected)
}
