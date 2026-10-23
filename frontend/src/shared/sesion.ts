import { createContext, useContext } from 'react'

// El rol lo decide el servidor; la pantalla solo deja de ofrecer lo que el rol no puede hacer.
export type Rol = 'administrador' | 'operativo' | 'lectura'

export const PuedeEditarContext = createContext(true)

export function usePuedeEditar(): boolean {
  return useContext(PuedeEditarContext)
}
