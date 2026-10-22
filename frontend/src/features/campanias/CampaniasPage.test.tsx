import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import CampaniasPage from './CampaniasPage'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const campania = {
  id: 5,
  nombre: 'Verano 2027',
  marca: 10,
  marca_nombre: 'Axe',
  cliente_facturacion: null,
  cliente_factura: 1,
  cliente_factura_nombre: 'Unilever',
  fecha_inicio: null,
  fecha_fin: null,
  estado: 'cotizada',
}

function stubFetch(overrides?: (input: string, options?: RequestInit) => unknown) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const custom = overrides?.(input, options)
    if (custom) return custom
    if (input.includes('/clientes/marcas/')) return ok([])
    if (input.includes('/clientes/clientes/')) return ok([])
    if (input.includes('/clientes/rubros/')) return ok([])
    if (input.includes('/campanias/campanias/')) return ok([campania])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('lista las campañas cargadas', async () => {
  stubFetch()
  render(<CampaniasPage />)
  expect(await screen.findByText('Verano 2027')).toBeDefined()
  expect(screen.getByText('Unilever')).toBeDefined()
})

test('filtra por estado agregando el parámetro a la consulta', async () => {
  const fetchMock = stubFetch()
  render(<CampaniasPage />)
  await screen.findByText('Verano 2027')
  fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'confirmada' } })
  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('estado=confirmada'))).toBe(
      true,
    ),
  )
})

test('abre el detalle (hub) de una campaña', async () => {
  stubFetch()
  render(<CampaniasPage />)
  await screen.findByText('Verano 2027')
  fireEvent.click(screen.getByRole('button', { name: 'Ver' }))
  expect(await screen.findByRole('heading', { name: 'Reservas' })).toBeDefined()
})

test('crea una campaña desde la pantalla', async () => {
  const fetchMock = stubFetch((input, options) => {
    if (input.includes('/campanias/campanias/') && options?.method === 'POST') return ok({ id: 9 })
    return undefined
  })
  render(<CampaniasPage />)
  await screen.findByText('Verano 2027')
  fireEvent.click(screen.getByRole('button', { name: 'Nueva campaña' }))
  const form = screen.getByRole('form', { name: 'Formulario de campaña' })
  fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'Invierno' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar campaña' }))
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          String(url) === '/api/campanias/campanias/' &&
          options?.method === 'POST' &&
          JSON.parse(String(options.body)).nombre === 'Invierno',
      ),
    ).toBe(true),
  )
})
