const MESES = [
  'Enero',
  'Febrero',
  'Marzo',
  'Abril',
  'Mayo',
  'Junio',
  'Julio',
  'Agosto',
  'Septiembre',
  'Octubre',
  'Noviembre',
  'Diciembre',
]

type Props = {
  /** "AAAA-MM". */
  desde: string
  /** "AAAA-MM"; nunca anterior a `desde`. */
  hasta: string
  onCambiar: (desde: string, hasta: string) => void
}

function partes(periodo: string): [number, number] {
  const [anio, mes] = periodo.split('-').map(Number)
  return [anio, mes]
}

function periodo(anio: number, mes: number): string {
  return `${anio}-${String(mes).padStart(2, '0')}`
}

/** Años ofrecidos: de cinco antes del actual a uno después, ampliado si el período cae afuera. */
function anios(desde: number, hasta: number): number[] {
  const actual = new Date().getFullYear()
  const primero = Math.min(actual - 5, desde)
  const ultimo = Math.max(actual + 1, hasta)
  return Array.from({ length: ultimo - primero + 1 }, (_, indice) => primero + indice)
}

/**
 * Período de un reporte con mes y año escritos («Enero 2026»), en lugar del selector de mes del
 * navegador. Si el inicio pasa al fin, el fin lo acompaña; el fin no ofrece meses anteriores.
 */
export default function SelectorPeriodo({ desde, hasta, onCambiar }: Props) {
  const [anioDesde, mesDesde] = partes(desde)
  const [anioHasta, mesHasta] = partes(hasta)
  const opcionesAnio = anios(anioDesde, anioHasta)

  function cambiarDesde(nuevo: string) {
    onCambiar(nuevo, nuevo > hasta ? nuevo : hasta)
  }

  function cambiarHasta(nuevo: string) {
    onCambiar(desde, nuevo < desde ? desde : nuevo)
  }

  return (
    <div className="selector-periodo">
      <fieldset>
        <legend>Desde</legend>
        <select
          aria-label="Mes desde"
          value={mesDesde}
          onChange={(event) => cambiarDesde(periodo(anioDesde, Number(event.target.value)))}
        >
          {MESES.map((nombre, indice) => (
            <option key={nombre} value={indice + 1}>
              {nombre}
            </option>
          ))}
        </select>
        <select
          aria-label="Año desde"
          value={anioDesde}
          onChange={(event) => cambiarDesde(periodo(Number(event.target.value), mesDesde))}
        >
          {opcionesAnio.map((anio) => (
            <option key={anio} value={anio}>
              {anio}
            </option>
          ))}
        </select>
      </fieldset>
      <fieldset>
        <legend>Hasta</legend>
        <select
          aria-label="Mes hasta"
          value={mesHasta}
          onChange={(event) => cambiarHasta(periodo(anioHasta, Number(event.target.value)))}
        >
          {MESES.map((nombre, indice) => (
            <option
              key={nombre}
              value={indice + 1}
              disabled={periodo(anioHasta, indice + 1) < desde}
            >
              {nombre}
            </option>
          ))}
        </select>
        <select
          aria-label="Año hasta"
          value={anioHasta}
          onChange={(event) => cambiarHasta(periodo(Number(event.target.value), mesHasta))}
        >
          {opcionesAnio.map((anio) => (
            <option key={anio} value={anio} disabled={anio < anioDesde}>
              {anio}
            </option>
          ))}
        </select>
      </fieldset>
    </div>
  )
}
