import { apiWrite } from '../../shared/api'
import type { ResultadoTanda } from './types'

/** Carteles por pedido: la pantalla manda la selección por lotes para mostrar el avance. */
export const TAMANO_LOTE = 25

/** Crea las reservas de a lotes y junta los resúmenes; un lote que falla entero va a fallidas. */
export async function crearPorLotes(
  base: { campania: number; fecha_inicio: string; fecha_fin: string },
  carteles: number[],
  onAvance: (hechos: number) => void,
): Promise<ResultadoTanda> {
  const total: ResultadoTanda = { creadas: [], existentes: [], fallidas: [] }
  for (let desde = 0; desde < carteles.length; desde += TAMANO_LOTE) {
    const lote = carteles.slice(desde, desde + TAMANO_LOTE)
    try {
      const parcial = await apiWrite<ResultadoTanda>('/api/reservas/reservas/en-bloque/', 'POST', {
        ...base,
        carteles: lote,
      })
      total.creadas.push(...parcial.creadas)
      total.existentes.push(...parcial.existentes)
      total.fallidas.push(...parcial.fallidas)
    } catch {
      const motivo = 'No se pudo completar el pedido. Reintentá.'
      total.fallidas.push(...lote.map((cartel) => ({ cartel, motivo })))
    }
    onAvance(desde + lote.length)
  }
  return total
}
