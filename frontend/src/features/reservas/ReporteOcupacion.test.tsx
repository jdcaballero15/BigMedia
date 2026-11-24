import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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
  formatos: [
    {
      formato: 3,
      nombre: 'Cartelera',
      modalidad: 'fija',
      ocupacion: 75.0,
      por_mes: [
        { periodo: '2026-10', porcentaje: 100.0 },
        { periodo: '2026-11', porcentaje: 50.0 },
      ],
    },
    {
      formato: 4,
      nombre: 'LED',
      modalidad: 'digital',
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
    if (input.includes('/inventario/formatos/'))
      return ok([
        { id: 3, nombre: 'Cartelera' },
        { id: 4, nombre: 'LED' },
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

test('muestra la evolución por formato, un renglón por formato', async () => {
  stubFetch()
  render(<ReporteOcupacionPage />)
  expect(await screen.findByText('Evolución por formato')).toBeDefined()
  const tabla = screen.getByRole('table', { name: 'Ocupación por formato' })
  expect(within(tabla).getByText('Cartelera')).toBeDefined()
  expect(within(tabla).getByText('LED')).toBeDefined()
  expect(screen.queryByText('Evolución por modalidad')).toBeNull()
})

test('no ofrece filtros de departamento ni de modalidad', async () => {
  stubFetch()
  render(<ReporteOcupacionPage />)
  await screen.findByText('Av. San Martín 1234')
  expect(screen.queryByLabelText('Departamento')).toBeNull()
  expect(screen.queryByLabelText('Modalidad')).toBeNull()
  expect(screen.getByLabelText('Formato')).toBeDefined()
})

test('elegir un formato pide el reporte con formato=<id>', async () => {
  const fetchMock = stubFetch()
  render(<ReporteOcupacionPage />)
  await screen.findByText('Av. San Martín 1234')
  await screen.findByRole('option', { name: 'LED' })
  fireEvent.change(screen.getByLabelText('Formato'), { target: { value: '4' } })
  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([u]) => String(u).includes('formato=4'))).toBe(true),
  )
  expect(fetchMock.mock.calls.some(([u]) => /zona=|modalidad=/.test(String(u)))).toBe(false)
})

test('el PDF indica el formato elegido en el texto de filtros', async () => {
  stubFetch()
  render(<ReporteOcupacionPage />)
  await screen.findByText('Av. San Martín 1234')
  await screen.findByRole('option', { name: 'LED' })
  fireEvent.change(screen.getByLabelText('Formato'), { target: { value: '4' } })
  await screen.findByText('Av. San Martín 1234')
  fireEvent.click(screen.getByRole('button', { name: 'Exportar PDF' }))
  const llamadas = vi.mocked(descargarPdf).mock.calls
  const [, , filtros, columnas] = llamadas[llamadas.length - 1]
  expect(filtros).toContain('Formato: LED')
  expect(filtros).not.toContain('Departamento')
  expect(columnas).toContain('Formato')
})

test('cambiar el período vuelve a pedir el reporte', async () => {
  const fetchMock = stubFetch()
  render(<ReporteOcupacionPage />)
  await screen.findByText('Av. San Martín 1234')
  fireEvent.change(screen.getByLabelText('Año desde'), { target: { value: '2026' } })
  fireEvent.change(screen.getByLabelText('Mes desde'), { target: { value: '6' } })
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
  stubFetch({ periodos: [], carteles: [], formatos: [] })
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

test('marca los carteles de baja que tuvieron reservas en el período', async () => {
  const conBaja = {
    ...reporte,
    carteles: [{ ...reporte.carteles[0], de_baja: true }, reporte.carteles[1]],
  }
  stubFetch(conBaja)
  render(<ReporteOcupacionPage />)
  expect(await screen.findByText('Av. San Martín 1234 (de baja)')).toBeDefined()
  expect(screen.getByText('Ruta 40 km 10')).toBeDefined()
})

test('reporteOcupacion_resumen_muestraLaOcupacionDeCadaFormatoYLosCarteles', async () => {
  stubFetch()
  render(<ReporteOcupacionPage />)

  const resumen = await screen.findByLabelText('Resumen del período')
  expect(within(resumen).getByText('Ocupación Cartelera').parentElement?.className).toBe(
    'cifra cifra-principal',
  )
  expect(within(resumen).getByText('Ocupación LED')).toBeDefined()
  expect(within(resumen).getByText('Carteles en el reporte')).toBeDefined()
})
