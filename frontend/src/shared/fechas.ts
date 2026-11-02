// Fechas en pantalla como dd/mm/aaaa; hacia y desde la API siempre aaaa-mm-dd.

/** Valor que emite `CampoFecha` cuando el texto escrito no es una fecha válida. */
export const FECHA_INVALIDA = 'invalida'

export const MENSAJE_FECHA_INVALIDA = 'Fecha inválida. Usá dd/mm/aaaa.'

const ISO = /^(\d{4})-(\d{2})-(\d{2})$/
const DIA_MES_ANIO = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/

function dos(numero: number): string {
  return String(numero).padStart(2, '0')
}

/** "2026-11-01" → "01/11/2026". Un texto que no es ISO se devuelve igual. */
export function formatearFecha(iso: string | null | undefined): string {
  if (!iso) return ''
  const partes = ISO.exec(iso)
  return partes ? `${partes[3]}/${partes[2]}/${partes[1]}` : iso
}

/** "2026-11" → "11/2026". */
export function formatearPeriodo(periodo: string): string {
  const [anio, mes] = periodo.split('-')
  return anio && mes ? `${mes}/${anio}` : periodo
}

/** "01/11/2026" → "2026-11-01"; `null` si está incompleta o el día no existe. */
export function parsearFecha(texto: string): string | null {
  const partes = DIA_MES_ANIO.exec(texto.trim())
  if (!partes) return null
  const [dia, mes, anio] = [Number(partes[1]), Number(partes[2]), Number(partes[3])]
  const fecha = new Date(anio, mes - 1, dia)
  // `Date` corre los días que no existen (31/02 → 03/03): si cambió, la fecha era inválida.
  if (fecha.getFullYear() !== anio || fecha.getMonth() !== mes - 1 || fecha.getDate() !== dia) {
    return null
  }
  return `${anio}-${dos(mes)}-${dos(dia)}`
}

/** Errores por campo de las fechas que quedaron inválidas, para frenar el envío de un formulario. */
export function erroresDeFechas(campos: Record<string, string>): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(campos)
      .filter(([, valor]) => valor === FECHA_INVALIDA)
      .map(([campo]) => [campo, [MENSAJE_FECHA_INVALIDA]]),
  )
}

/** "2026-11-01" → `Date` local de ese día (sin el corrimiento de UTC). */
export function isoADate(iso: string): Date | undefined {
  const partes = ISO.exec(iso)
  if (!partes) return undefined
  return new Date(Number(partes[1]), Number(partes[2]) - 1, Number(partes[3]))
}

/** `Date` local → "aaaa-mm-dd". */
export function dateAIso(fecha: Date): string {
  return `${fecha.getFullYear()}-${dos(fecha.getMonth() + 1)}-${dos(fecha.getDate())}`
}

const DIAS = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
const MESES = [
  'enero',
  'febrero',
  'marzo',
  'abril',
  'mayo',
  'junio',
  'julio',
  'agosto',
  'septiembre',
  'octubre',
  'noviembre',
  'diciembre',
]

/** `Date` local → "Miércoles 28 de octubre de 2026". */
export function fechaLarga(fecha: Date): string {
  const dia = DIAS[fecha.getDay()]
  const mes = MESES[fecha.getMonth()]
  return `${dia} ${fecha.getDate()} de ${mes} de ${fecha.getFullYear()}`
}
