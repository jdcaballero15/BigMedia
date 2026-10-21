const formateador = new Intl.NumberFormat('es-AR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

// Muestra un importe con separador de miles y dos decimales, en pesos.
export function formatearMonto(valor: string): string {
  return `$${formateador.format(Number(valor))}`
}

// Suma importes en centavos enteros para no arrastrar errores de float.
export function sumarMontos(montos: string[]): string {
  const centavos = montos.reduce((total, monto) => {
    const [enteros, decimales = ''] = monto.split('.')
    return total + Number(enteros) * 100 + Number(decimales.padEnd(2, '0').slice(0, 2))
  }, 0)
  const resto = String(centavos % 100).padStart(2, '0')
  return `${Math.floor(centavos / 100)}.${resto}`
}
