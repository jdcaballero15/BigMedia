import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import ReporteOcupacionPage from './ReporteOcupacion'
import { formatearPorcentaje } from './ocupacion'
import { descargarPdf } from '../../shared/pdf'

vi.mock('../../shared/pdf', () => ({ descargarPdf: vi.fn() }))

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const reporte = {
  periodos: [
    { clave: '2026-10', etiqueta: 'Oct 2026' },
    { clave: '2026-11', etiqueta: 'Nov 2026' },
  ],
  carteles: [
    {
      id: 7,
      nombre_visible: 'Av. San Martín 1234',
      modalidad: 'fija',
      zona_nombre: 'Ciudad',
      formato_nombre: 'Cartelera',
      ocupacion: 75.0,
      celdas: [
        { periodo: '2026-10', porcentaje: 100.0, dias_ocupados: 31, dias_disponibles: 31 },
        { periodo: '2026-11', porcentaje: 50.0, dias_ocupados: 15, dias_disponibles: 30 },
      ],
    },
    {
      id: 9,
      nombre_visible: 'Ruta 40 km 10',
      modalidad: 'digital',
      zona_nombre: 'Maipú',
      formato_nombre: 'LED',
      ocupacion: 25.0,
      celdas: [
        { periodo: '2026-10', porcentaje: 25.0, dias_ocupados: 155, dias_disponibles: 620 },
        { periodo: '2026-11', porcentaje: 25.0, dias_ocupados: 150, dias_disponibles: 600 },
      ],
    },
  ],
  modalidades: [
    {
      modalidad: 'fija',
      etiqueta: 'Fija',
      ocupacion: 75.0,
      por_mes: [
        { periodo: '2026-10', porcentaje: 100.0 },
        { periodo: '2026-11', porcentaje: 50.0 },
      ],
    },
    {
      modalidad: 'digital',
      etiqueta: 'Digital',
      ocupacion: 25.0,
      por_mes: [
        { periodo: '2026-10', porcentaje: 25.0 },
        { periodo: '2026-11', porcentaje: 25.0 },
      ],
    },
  ],
}

function stubFetch(data: unknown = reporte) {
  const fetchMock = vi.fn(async (input: string) => {
    if (input.includes('/inventario/zonas/'))
      return ok([
        { id: 1, nombre: 'Ciudad' },
        { id: 2, nombre: 'Maipú' },
      ])
    if (input.includes('/reservas/reporte-ocupacion/')) return ok(data)
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('muestra el mapa de calor con los carteles en orden y las columnas de meses', async () => {
  stubFetch()
  render(<ReporteOcupacionPage />)
  expect(await screen.findByText('Av. San Martín 1234')).toBeDefined()
  expect(screen.getByText('Ruta 40 km 10')).toBeDefined()
  expect(screen.getAllByText('Oct 2026').length).toBeGreaterThan(0)
  expect(screen.getAllByText(formatearPorcentaje(75)).length).toBeGreaterThan(0)
})

test('muestra la evolución por modalidad', async () => {
  stubFetch()
  render(<ReporteOcupacionPage />)
  expect(await screen.findByText('Evolución por modalidad')).toBeDefined()
  expect(screen.getByRole('table', { name: 'Ocupación por modalidad' })).toBeDefined()
})

test('cambiar el período vuelve a pedir el reporte', async () => {
  const fetchMock = stubFetch()
  render(<ReporteOcupacionPage />)
  await screen.findByText('Av. San Martín 1234')
  fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-06' } })
  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([u]) => String(u).includes('desde=2026-06'))).toBe(true),
  )
})

test('exporta el reporte a PDF', async () => {
  stubFetch()
  render(<ReporteOcupacionPage />)
  await screen.findByText('Av. San Martín 1234')
  fireEvent.click(screen.getByRole('button', { name: 'Exportar PDF' }))
  expect(descargarPdf).toHaveBeenCalled()
})

test('sin carteles muestra el estado vacío', async () => {
  stubFetch({ periodos: [], carteles: [], modalidades: [] })
  render(<ReporteOcupacionPage />)
  expect(await screen.findByText('No hay carteles para estos filtros.')).toBeDefined()
})

test('exporta el reporte a CSV', async () => {
  const crearUrl = vi.fn(() => 'blob:test')
  URL.createObjectURL = crearUrl
  URL.revokeObjectURL = vi.fn()
  stubFetch()
  render(<ReporteOcupacionPage />)
  await screen.findByText('Av. San Martín 1234')
  fireEvent.click(screen.getByRole('button', { name: 'Exportar CSV' }))
  expect(crearUrl).toHaveBeenCalled()
})
