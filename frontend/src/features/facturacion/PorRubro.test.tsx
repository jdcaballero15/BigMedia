import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
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

const reporteGrupos = {
  grupos: [
    {
      grupo: 4,
      nombre: 'Grupo Cuyo',
      ingresos: '7000.00',
      dias_cupo: 40,
      porcentaje_ocupacion: 80.0,
    },
    {
      grupo: null,
      nombre: 'Sin grupo',
      ingresos: '1000.00',
      dias_cupo: 10,
      porcentaje_ocupacion: 20.0,
    },
  ],
  total_ingresos: '8000.00',
  total_dias_cupo: 50,
}

function stubFetch(data: unknown = reporte, grupos: unknown = reporteGrupos) {
  const fetchMock = vi.fn(async (input: string) => {
    if (String(input).includes('/facturacion/por-rubro/')) return ok(data)
    if (String(input).includes('/facturacion/por-grupo/')) return ok(grupos)
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
  const tabla = screen.getByRole('table')
  expect(within(tabla).getByText(formatearMonto('8000.00'))).toBeDefined()
  expect(within(tabla).getByText('50')).toBeDefined()
  const resumen = screen.getByLabelText('Resumen del período')
  expect(within(resumen).getByText(formatearMonto('8000.00'))).toBeDefined()
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

test('corta por grupo económico y exporta ese corte (HU-050 criterio 2)', async () => {
  const fetchMock = stubFetch()
  render(<PorRubroPage />)
  await screen.findByText('Gastronomía')

  fireEvent.change(screen.getByLabelText('Cortar por'), { target: { value: 'grupo' } })

  const tabla = await screen.findByRole('table', { name: 'Ingresos por grupo económico' })
  expect(within(tabla).getByRole('columnheader', { name: 'Grupo económico' })).toBeDefined()
  expect(within(tabla).getByText('Grupo Cuyo')).toBeDefined()
  expect(within(tabla).getByText('Sin grupo')).toBeDefined()
  expect(within(tabla).queryByText('Gastronomía')).toBeNull()
  expect(
    fetchMock.mock.calls.some(([url]) => String(url).includes('/facturacion/por-grupo/')),
  ).toBe(true)
  fireEvent.click(screen.getByRole('button', { name: 'Exportar PDF' }))
  expect(descargarPdf).toHaveBeenLastCalledWith(
    expect.stringMatching(/^por-grupo-/),
    'Ingresos por grupo económico',
    expect.any(String),
    ['Grupo económico', 'Ingresos', 'Días-cupo', '% Ocupación'],
    expect.any(Array),
  )
})

test('avisa si falla el reporte del corte elegido', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) })),
  )
  render(<PorRubroPage />)
  expect(
    await screen.findByText('No se pudo cargar el reporte de ingresos por rubro.'),
  ).toBeDefined()
})
