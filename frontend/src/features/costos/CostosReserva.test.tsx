import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import CostosReserva from './CostosReserva'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const margen = { ingreso: '1000.00', costo: '600.00', margen: '400.00', porcentaje: 40 }
const costo = {
  id: 1,
  reserva: 5,
  tipo: 'impresion',
  tipo_nombre: 'Impresión',
  proveedor: null,
  proveedor_nombre: null,
  monto: '600.00',
  fecha: '2026-11-01',
  anulado: false,
  motivo_anulacion: '',
}

function stubFetch() {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    if (input.includes('/costos/margen/')) return ok(margen)
    if (input.includes('/costos/costos/') && options?.method === 'POST') return ok({ id: 2 })
    if (input.includes('/costos/costos/')) return ok([costo])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('muestra el margen y los costos de la reserva', async () => {
  stubFetch()
  render(<CostosReserva reservaId={5} />)
  expect(await screen.findByText(/Margen 400.00/)).toBeDefined()
  expect(screen.getByText(/Impresión: 600.00/)).toBeDefined()
})

test('agrega un costo', async () => {
  const fetchMock = stubFetch()
  render(<CostosReserva reservaId={5} />)
  await screen.findByText(/Margen 400.00/)
  const form = screen.getByRole('form', { name: 'Agregar costo' })
  fireEvent.change(screen.getByLabelText('Monto'), { target: { value: '200' } })
  fireEvent.submit(form)
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          String(url) === '/api/costos/costos/' &&
          options?.method === 'POST' &&
          JSON.parse(String(options.body)).reserva === 5,
      ),
    ).toBe(true),
  )
})
