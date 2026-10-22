import { expect, test, vi } from 'vitest'
import { descargarPdf, lineasEncabezado } from './pdf'

const { save, text } = vi.hoisted(() => ({ save: vi.fn(), text: vi.fn() }))
vi.mock('jspdf', () => ({
  jsPDF: vi.fn(function () {
    return { setFontSize: vi.fn(), text, save }
  }),
}))
vi.mock('jspdf-autotable', () => ({ default: vi.fn() }))

test('arma el título, la línea de filtros y la fecha de generación', () => {
  expect(lineasEncabezado('Ingresos', 'Período: 2026-01 a 2026-12', '22/10/2026')).toEqual([
    'Ingresos',
    'Período: 2026-01 a 2026-12',
    'Generado el 22/10/2026',
  ])
})

test('descargarPdf escribe el encabezado y guarda el archivo', () => {
  descargarPdf('ingresos.pdf', 'Ingresos', 'Período: X', ['A'], [['1']])
  expect(text).toHaveBeenCalledWith('Ingresos', 14, 18)
  expect(text).toHaveBeenCalledWith('Período: X', 14, 25)
  expect(save).toHaveBeenCalledWith('ingresos.pdf')
})
