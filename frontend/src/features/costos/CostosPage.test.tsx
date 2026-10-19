import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import CostosPage from './CostosPage'
import { sumarMontos } from './montos'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const costos = [
  {
    id: 1,
    reserva: 5,
    tipo: 'impresion',
    tipo_nombre: 'Impresión',
    proveedor: 3,
    proveedor_nombre: 'Imprenta Uno',
    cartel_nombre: 'San Martín 1234',
    campania: 8,
    campania_nombre: 'Lanzamiento',
    monto: '200.10',
    fecha: '2026-10-19',
    anulado: false,
    motivo_anulacion: '',
  },
  {
    id: 2,
    reserva: 5,
    tipo: 'fijacion',
    tipo_nombre: 'Fijación',
    proveedor: null,
    proveedor_nombre: null,
    cartel_nombre: 'San Martín 1234',
    campania: 8,
    campania_nombre: 'Lanzamiento',
    monto: '99.95',
    fecha: '2026-10-18',
    anulado: false,
    motivo_anulacion: '',
  },
  {
    id: 3,
    reserva: 6,
    tipo: 'otro',
    tipo_nombre: 'Otro',
    proveedor: null,
    proveedor_nombre: null,
    cartel_nombre: 'Belgrano 50',
    campania: 9,
    campania_nombre: 'Campaña #9',
    monto: '500.00',
    fecha: '2026-10-17',
    anulado: true,
    motivo_anulacion: 'Cargado dos veces',
  },
]

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('suma montos sin errores de redondeo', () => {
  expect(sumarMontos(['0.10', '0.20'])).toBe('0.30')
  expect(sumarMontos(['200.10', '99.95', '5'])).toBe('305.05')
  expect(sumarMontos([])).toBe('0.00')
})

test('lista todos los costos con campaña y cartel, y suma solo los vigentes', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input.startsWith('/api/inventario/proveedores/'))
        return ok([{ id: 3, nombre: 'Imprenta Uno', activo: true, servicio: '' }])
      if (input === '/api/costos/costos/') return ok(costos)
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
  render(<CostosPage />)

  expect(await screen.findByText('Campaña #9')).toBeDefined()
  expect(screen.getAllByText('Lanzamiento')).toHaveLength(2)
  expect(screen.getByText('Belgrano 50')).toBeDefined()
  expect(screen.getByText('Anulado')).toBeDefined()
  expect(screen.getByText('Cargado dos veces')).toBeDefined()
  expect(screen.getByText('300.05')).toBeDefined()
})

test('filtra por tipo y proveedor en la consulta', async () => {
  const fetchMock = vi.fn(async (input: string) => {
    if (input.startsWith('/api/inventario/proveedores/'))
      return ok([{ id: 3, nombre: 'Imprenta Uno', activo: true, servicio: '' }])
    if (input.startsWith('/api/costos/costos/')) return ok([])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  render(<CostosPage />)

  expect(await screen.findByText('No hay costos cargados.')).toBeDefined()
  await screen.findByRole('option', { name: 'Imprenta Uno' })
  fireEvent.change(screen.getByLabelText('Tipo'), { target: { value: 'impresion' } })
  fireEvent.change(screen.getByLabelText('Proveedor'), { target: { value: '3' } })

  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url]) => String(url) === '/api/costos/costos/?tipo=impresion&proveedor=3',
      ),
    ).toBe(true),
  )
})

test('avisa cuando no se pueden cargar los costos', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input.startsWith('/api/inventario/proveedores/')) return ok([])
      return { ok: false, status: 500, json: async () => ({}) }
    }),
  )
  render(<CostosPage />)

  expect((await screen.findByRole('alert')).textContent).toBe('No se pudieron cargar los costos.')
})
