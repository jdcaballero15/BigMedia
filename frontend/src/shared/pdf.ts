import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'

// Las tres líneas del encabezado del PDF: título, filtros aplicados y fecha de generación. Pura.
export function lineasEncabezado(titulo: string, filtros: string, fecha: string): string[] {
  return [titulo, filtros, `Generado el ${fecha}`]
}

// Genera y descarga un PDF con el encabezado y una tabla (para adjuntar en un mail).
export function descargarPdf(
  nombreArchivo: string,
  titulo: string,
  filtros: string,
  columnas: string[],
  filas: string[][],
): void {
  const doc = new jsPDF()
  const fecha = new Date().toLocaleDateString('es-AR')
  const [lineaTitulo, lineaFiltros, lineaFecha] = lineasEncabezado(titulo, filtros, fecha)
  doc.setFontSize(14)
  doc.text(lineaTitulo, 14, 18)
  doc.setFontSize(10)
  doc.text(lineaFiltros, 14, 25)
  doc.text(lineaFecha, 14, 31)
  autoTable(doc, {
    head: [columnas],
    body: filas,
    startY: 36,
    styles: { fontSize: 8 },
    headStyles: { fillColor: [224, 138, 44] },
  })
  doc.save(nombreArchivo)
}
