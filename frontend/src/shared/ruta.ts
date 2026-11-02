import { createContext, useContext, useEffect, useRef } from 'react'

/** Lo que una pantalla abrió adentro suyo (una ficha), para mostrarlo en la ruta de la barra. */
export type DetalleRuta = { texto: string; onVolver: () => void }

export const DetalleRutaContext = createContext<(detalle: DetalleRuta | null) => void>(() => {})

/** Publica en la barra superior el detalle abierto (`null` si no hay) y lo saca al cerrarse. */
export function useDetalleRuta(texto: string | null, onVolver: () => void) {
  const publicar = useContext(DetalleRutaContext)
  const volver = useRef(onVolver)

  useEffect(() => {
    volver.current = onVolver
  })

  useEffect(() => {
    publicar(texto === null ? null : { texto, onVolver: () => volver.current() })
    return () => publicar(null)
  }, [publicar, texto])
}
