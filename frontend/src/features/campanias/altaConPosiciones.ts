import { apiWrite } from '../../shared/api'
import { crearPorLotes } from '../reservas/tandas'
import type { LineaAlta } from './PosicionesAlta'

/** Lo que pasó al guardar las líneas y los carteles de una campaña nueva (HU-056 criterio 7). */
export type ResultadoAlta = {
  campania: string
  reservasCreadas: number
  lineasFallidas: { formato: string; motivo: string }[]
  cartelesFallidos: { cartel: string; motivo: string }[]
}

function motivoDe(error: unknown): string {
  return error instanceof Error ? error.message : 'No se pudo guardar.'
}

/** Crea las líneas y las reservas de la campaña recién creada; lo que falla queda en el resumen. */
export async function crearLineasYReservas(
  campania: { id: number; nombre: string },
  lineas: LineaAlta[],
): Promise<ResultadoAlta> {
  const resultado: ResultadoAlta = {
    campania: campania.nombre,
    reservasCreadas: 0,
    lineasFallidas: [],
    cartelesFallidos: [],
  }
  for (const linea of lineas) {
    try {
      await apiWrite('/api/campanias/lineas-formato/', 'POST', {
        campania: campania.id,
        formato: linea.formato,
        cantidad: linea.cantidad,
      })
    } catch (error) {
      resultado.lineasFallidas.push({ formato: linea.formato_nombre, motivo: motivoDe(error) })
    }
    if (!linea.seleccion || linea.seleccion.carteles.length === 0) continue
    const { carteles, desde, hasta } = linea.seleccion
    const nombres = new Map(carteles.map((cartel) => [cartel.id, cartel.nombre_visible]))
    const tanda = await crearPorLotes(
      { campania: campania.id, fecha_inicio: desde, fecha_fin: hasta },
      carteles.map((cartel) => cartel.id),
      () => undefined,
    )
    resultado.reservasCreadas += tanda.creadas.length + tanda.existentes.length
    for (const fallida of tanda.fallidas) {
      const cartel = nombres.get(fallida.cartel) ?? `Cartel #${fallida.cartel}`
      resultado.cartelesFallidos.push({ cartel, motivo: fallida.motivo })
    }
  }
  return resultado
}
