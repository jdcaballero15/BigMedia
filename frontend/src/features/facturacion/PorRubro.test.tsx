import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import PorRubroPage from './PorRubro'
import { formatearMonto } from './montos'
import { descargarPdf } from '../../shared/pdf'

vi.mock('../../shared/pdf', () => ({ descargarPdf: vi.fn() }))

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const reporte = {
  rubros: [
    {
      rubro: 1,
      nombre: 'Gastronomía',
      ingresos: '5000.00',
      dias_cupo: 31,
      porcentaje_ocupacion: 62.0,
    },
    { rubro: 2, nombre: 'Retail', ingresos: '3000.00', dias_cupo: 19, porcentaje_ocupacion: 38.0 },
  ],
  total_ingresos: '8000.00',
  total_dias_cupo: 50,
}

function stubFetch(data: unknown = reporte) {
  const fetchMock = vi.fn(async (input: string) => {
    if (String(input).includes('/facturacion/por-rubro/')) return ok(data)
    throw new Error(`URL inesperada: ${String(input)}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('muestra el ranking de rubros con ingresos, días-cupo y % ocupación', async () => {
  stubFetch()
  render(<PorRubroPage />)
  expect(await screen.findByText('Gastronomía')).toBeDefined()
  expect(screen.getByText('Retail')).toBeDefined()
  expect(screen.getByText(formatearMonto('8000.00'))).toBeDefined()
  expect(screen.getByText('50')).toBeDefined()
})

test('sin datos muestra el estado vacío', async () => {
  stubFetch({ rubros: [], total_ingresos: '0.00', total_dias_cupo: 0 })
  render(<PorRubroPage />)
  expect(await screen.findByText('Sin datos en el período.')).toBeDefined()
})

test('exporta el reporte a PDF', async () => {
  stubFetch()
  render(<PorRubroPage />)
  await screen.findByText('Gastronomía')
  fireEvent.click(screen.getByRole('button', { name: 'Exportar PDF' }))
  expect(descargarPdf).toHaveBeenCalled()
})

test('exporta el reporte a CSV', async () => {
  const crearUrl = vi.fn(() => 'blob:test')
  URL.createObjectURL = crearUrl
  URL.revokeObjectURL = vi.fn()
  stubFetch()
  render(<PorRubroPage />)
  await screen.findByText('Gastronomía')
  fireEvent.click(screen.getByRole('button', { name: 'Exportar CSV' }))
  expect(crearUrl).toHaveBeenCalled()
})
