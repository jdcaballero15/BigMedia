// Suma montos con dos decimales en centavos enteros para no arrastrar errores de float.
export function sumarMontos(montos: string[]): string {
  const centavos = montos.reduce((total, monto) => {
    const [enteros, decimales = ''] = monto.split('.')
    return total + Number(enteros) * 100 + Number(decimales.padEnd(2, '0').slice(0, 2))
  }, 0)
  const resto = String(centavos % 100).padStart(2, '0')
  return `${Math.floor(centavos / 100)}.${resto}`
}
