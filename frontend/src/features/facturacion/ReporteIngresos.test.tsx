import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import ReporteIngresosPage from './ReporteIngresos'
import { formatearMonto } from './montos'
import { descargarPdf } from '../../shared/pdf'

vi.mock('../../shared/pdf', () => ({ descargarPdf: vi.fn() }))

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const reporte = {
  periodos: [
    { mes: '2026-10', etiqueta: 'Oct 2026' },
    { mes: '2026-11', etiqueta: 'Nov 2026' },
  ],
  clientes: [
    {
      cliente: 1,
      nombre: 'Agencia Centro',
      total: '3000.00',
      por_mes: { '2026-10': '2000.00', '2026-11': '1000.00' },
      marcas: [
        {
          marca: 1,
          nombre: 'Coca-Cola',
          total: '2500.00',
          por_mes: { '2026-10': '1500.00', '2026-11': '1000.00' },
        },
        {
          marca: 2,
          nombre: 'Fanta',
          total: '500.00',
          por_mes: { '2026-10': '500.00', '2026-11': '0.00' },
        },
      ],
    },
    {
      cliente: 2,
      nombre: 'Directo SA',
      total: '1000.00',
      por_mes: { '2026-10': '1000.00', '2026-11': '0.00' },
      marcas: [],
    },
  ],
  total: '4000.00',
}

function stubFetch(data: unknown = reporte) {
  const fetchMock = vi.fn(async (input: string) => {
    if (input.includes('/facturacion/ingresos/')) return ok(data)
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('muestra el ranking de clientes con las columnas de meses y el total global', async () => {
  stubFetch()
  render(<ReporteIngresosPage />)
  expect(await screen.findByText('Agencia Centro')).toBeDefined()
  expect(screen.getByText('Directo SA')).toBeDefined()
  expect(screen.getByText('Oct 2026')).toBeDefined()
  expect(screen.getByText('Nov 2026')).toBeDefined()
  const tabla = screen.getByRole('table', { name: 'Ingresos por cliente y marca' })
  expect(within(tabla).getByText(formatearMonto('4000.00'))).toBeDefined()
  const resumen = screen.getByLabelText('Resumen del período')
  expect(within(resumen).getByText(formatearMonto('4000.00'))).toBeDefined()
  expect(within(resumen).getByText('2')).toBeDefined()
})

test('desplegar un cliente muestra sus marcas', async () => {
  stubFetch()
  render(<ReporteIngresosPage />)
  await screen.findByText('Agencia Centro')
  expect(screen.queryByText('Coca-Cola')).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: /Agencia Centro/ }))
  expect(await screen.findByText('Coca-Cola')).toBeDefined()
  expect(screen.getByText('Fanta')).toBeDefined()
})

test('cambiar el período vuelve a pedir el reporte con el nuevo rango', async () => {
  const fetchMock = stubFetch()
  render(<ReporteIngresosPage />)
  await screen.findByText('Agencia Centro')
  fireEvent.change(screen.getByLabelText('Año desde'), { target: { value: '2026' } })
  fireEvent.change(screen.getByLabelText('Mes desde'), { target: { value: '6' } })
  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('desde=2026-06'))).toBe(true),
  )
})

test('sin ingresos muestra el estado vacío', async () => {
  stubFetch({ periodos: [], clientes: [], total: '0.00' })
  render(<ReporteIngresosPage />)
  expect(await screen.findByText('Sin ingresos en el período.')).toBeDefined()
})

test('exporta el reporte a PDF', async () => {
  stubFetch()
  render(<ReporteIngresosPage />)
  await screen.findByText('Agencia Centro')
  fireEvent.click(screen.getByRole('button', { name: 'Exportar PDF' }))
  expect(descargarPdf).toHaveBeenCalled()
})

test('exporta el reporte a CSV', async () => {
  const crearUrl = vi.fn(() => 'blob:test')
  URL.createObjectURL = crearUrl
  URL.revokeObjectURL = vi.fn()
  stubFetch()
  render(<ReporteIngresosPage />)
  await screen.findByText('Agencia Centro')
  fireEvent.click(screen.getByRole('button', { name: 'Exportar CSV' }))
  expect(crearUrl).toHaveBeenCalled()
})
