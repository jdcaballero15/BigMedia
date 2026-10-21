type Celda = string | number

const BOM = '﻿'

// Una celda de CSV: los números van con coma decimal; el texto, entre comillas y con las comillas
// internas duplicadas (formato pensado para abrir en Excel en es-AR).
function celda(valor: Celda): string {
  if (typeof valor === 'number') return String(valor).replace('.', ',')
  return `"${valor.replace(/"/g, '""')}"`
}

// Arma el contenido CSV (separador `;`, saltos `\r\n`) a partir de encabezados y filas. Función pura.
export function construirCsv(columnas: string[], filas: Celda[][]): string {
  const lineas = [columnas, ...filas].map((fila) => fila.map(celda).join(';'))
  return lineas.join('\r\n')
}

// Descarga el CSV como archivo. Agrega BOM para que Excel muestre bien los acentos.
export function descargarCsv(nombreArchivo: string, columnas: string[], filas: Celda[][]): void {
  const contenido = `${BOM}${construirCsv(columnas, filas)}`
  const blob = new Blob([contenido], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombreArchivo
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  URL.revokeObjectURL(url)
}
