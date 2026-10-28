import { useEffect, useRef, useState } from 'react'
import { Ellipsis } from 'lucide-react'
import { usePuedeEditar } from './sesion'

export type AccionFila = {
  etiqueta: string
  onClick: () => void
  /** Si cambia datos: Lectura no la ve. */
  edicion?: boolean
}

type Props = {
  /** Las condiciones se escriben en línea (`activo && {...}`): los valores falsos se descartan. */
  acciones: (AccionFila | false | null | undefined)[]
}

/** Botón de tres puntos con las acciones secundarias de una fila de tabla. */
export default function MenuFila({ acciones }: Props) {
  const puedeEditar = usePuedeEditar()
  const [posicion, setPosicion] = useState<{ top: number; right: number } | null>(null)
  const contenedor = useRef<HTMLDivElement>(null)
  const visibles = acciones.filter(
    (accion): accion is AccionFila => !!accion && (puedeEditar || !accion.edicion),
  )

  useEffect(() => {
    if (posicion === null) return
    function cerrarAfuera(event: MouseEvent) {
      if (!contenedor.current?.contains(event.target as Node)) setPosicion(null)
    }
    function cerrarConEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setPosicion(null)
    }
    function cerrar() {
      setPosicion(null)
    }
    document.addEventListener('mousedown', cerrarAfuera)
    document.addEventListener('keydown', cerrarConEscape)
    window.addEventListener('scroll', cerrar, true)
    window.addEventListener('resize', cerrar)
    return () => {
      document.removeEventListener('mousedown', cerrarAfuera)
      document.removeEventListener('keydown', cerrarConEscape)
      window.removeEventListener('scroll', cerrar, true)
      window.removeEventListener('resize', cerrar)
    }
  }, [posicion])

  if (visibles.length === 0) return null

  function alternar(boton: HTMLButtonElement) {
    if (posicion !== null) {
      setPosicion(null)
      return
    }
    // Fijo a la ventana: así la tabla con esquinas redondeadas no lo recorta.
    const caja = boton.getBoundingClientRect()
    setPosicion({ top: caja.bottom + 4, right: window.innerWidth - caja.right })
  }

  return (
    <div className="menu-fila" ref={contenedor}>
      <button
        className="menu-fila-boton"
        aria-label="Más acciones"
        aria-haspopup="true"
        aria-expanded={posicion !== null}
        onClick={(event) => alternar(event.currentTarget)}
      >
        <Ellipsis aria-hidden="true" size={18} />
      </button>
      {posicion !== null && (
        <div className="menu-fila-lista" style={posicion}>
          {visibles.map((accion) => (
            <button
              key={accion.etiqueta}
              onClick={() => {
                setPosicion(null)
                accion.onClick()
              }}
            >
              {accion.etiqueta}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
