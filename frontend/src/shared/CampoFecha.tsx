import { useEffect, useId, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'
import { CalendarDays } from 'lucide-react'
import { DayPicker } from 'react-day-picker'
import { es } from 'react-day-picker/locale/es'
import 'react-day-picker/style.css'
import { FieldErrors } from './FieldErrors'
import {
  FECHA_INVALIDA,
  MENSAJE_FECHA_INVALIDA,
  dateAIso,
  formatearFecha,
  isoADate,
  parsearFecha,
} from './fechas'

type Props = {
  label: string
  /** "aaaa-mm-dd", "" si está vacío o `FECHA_INVALIDA`. */
  value: string
  onChange: (valor: string) => void
  errores?: string[]
}

// El desplegable de años del calendario: diez años para atrás y diez para adelante.
const ANIO_ACTUAL = new Date().getFullYear()
const PRIMER_MES = new Date(ANIO_ACTUAL - 10, 0)
const ULTIMO_MES = new Date(ANIO_ACTUAL + 10, 11)

/** Lo que el texto escrito vale para la API: ISO, vacío o `FECHA_INVALIDA`. */
function valorDelTexto(texto: string): string {
  if (texto.trim() === '') return ''
  return parsearFecha(texto) ?? FECHA_INVALIDA
}

/** Campo de fecha dd/mm/aaaa con calendario desplegable. Hacia afuera habla en aaaa-mm-dd. */
export default function CampoFecha({ label, value, onChange, errores }: Props) {
  const id = useId()
  const contenedor = useRef<HTMLDivElement>(null)
  const [texto, setTexto] = useState(formatearFecha(value))
  const [valorPrevio, setValorPrevio] = useState(value)
  const [tocado, setTocado] = useState(false)
  const [abierto, setAbierto] = useState(false)

  // Si el padre cambia el valor (no es el eco de lo que se escribió), se muestra el nuevo.
  if (value !== valorPrevio) {
    setValorPrevio(value)
    if (value !== FECHA_INVALIDA && value !== valorDelTexto(texto)) {
      setTexto(formatearFecha(value))
    }
  }

  useEffect(() => {
    if (!abierto) return
    function cerrarSiEsAfuera(event: MouseEvent) {
      if (!contenedor.current?.contains(event.target as Node)) setAbierto(false)
    }
    document.addEventListener('mousedown', cerrarSiEsAfuera)
    return () => document.removeEventListener('mousedown', cerrarSiEsAfuera)
  }, [abierto])

  function escribir(nuevo: string) {
    setTexto(nuevo)
    onChange(valorDelTexto(nuevo))
  }

  function elegir(fecha: Date | undefined) {
    if (!fecha) return
    const iso = dateAIso(fecha)
    setTexto(formatearFecha(iso))
    setTocado(false)
    setAbierto(false)
    onChange(iso)
  }

  function cerrarConEscape(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape') setAbierto(false)
  }

  const invalida = tocado && valorDelTexto(texto) === FECHA_INVALIDA
  const mensajes = [...new Set([...(invalida ? [MENSAJE_FECHA_INVALIDA] : []), ...(errores ?? [])])]
  const seleccionada = isoADate(value)

  return (
    <div className="campo-fecha" ref={contenedor}>
      <label htmlFor={id}>{label}</label>
      <div className="campo-fecha-control">
        <input
          id={id}
          type="text"
          inputMode="numeric"
          autoComplete="off"
          placeholder="dd/mm/aaaa"
          value={texto}
          aria-invalid={invalida || undefined}
          onChange={(event) => escribir(event.target.value)}
          onBlur={() => setTocado(true)}
        />
        <button
          type="button"
          className="campo-fecha-boton"
          aria-label={`Abrir calendario: ${label}`}
          aria-expanded={abierto}
          onClick={() => setAbierto((actual) => !actual)}
        >
          <CalendarDays size={18} aria-hidden="true" />
        </button>
      </div>
      {abierto && (
        <div
          className="campo-fecha-calendario"
          role="dialog"
          aria-label={`Calendario: ${label}`}
          onKeyDown={cerrarConEscape}
        >
          <DayPicker
            mode="single"
            locale={es}
            selected={seleccionada}
            defaultMonth={seleccionada}
            onSelect={elegir}
            captionLayout="dropdown"
            startMonth={PRIMER_MES}
            endMonth={ULTIMO_MES}
            autoFocus
          />
        </div>
      )}
      <FieldErrors messages={mensajes} />
    </div>
  )
}
