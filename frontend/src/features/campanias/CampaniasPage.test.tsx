import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import CampaniasPage from './CampaniasPage'
import { abrirAcciones } from '../../shared/pruebas'

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

test('al cambiar las fechas pregunta si mover las Pendientes', async () => {
  const conFechas = { ...campania, fecha_inicio: '2026-11-01', fecha_fin: '2026-11-30' }
  const fetchMock = stubFetch((input, options) => {
    if (input.includes('/campanias/campanias/5/') && options?.method === 'PATCH')
      return ok({ ...conFechas, fecha_inicio: '2026-12-01', fecha_fin: '2026-12-31' })
    if (input.includes('/campanias/campanias/')) return ok([conFechas])
    if (input.includes('/reservas/reservas/?campania=5&estado=pendiente'))
      return ok([{ id: 1, fecha_inicio: '2026-11-01', fecha_fin: '2026-11-30' }])
    if (input.includes('/mover-pendientes/')) return ok({ movidas: [1] })
    return undefined
  })
  render(<CampaniasPage />)
  abrirAcciones((await screen.findByText('Verano 2027')).closest('tr')!)
  fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
  const form = screen.getByRole('form', { name: 'Formulario de campaña' })
  fireEvent.change(within(form).getByLabelText('Fecha de inicio'), {
    target: { value: '01/12/2026' },
  })
  fireEvent.change(within(form).getByLabelText('Fecha de fin'), { target: { value: '31/12/2026' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar campaña' }))
  await screen.findByRole('alertdialog', { name: 'Actualizar reservas Pendientes' })
  fireEvent.click(screen.getByRole('button', { name: 'Actualizar Pendientes' }))
  await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull())
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/mover-pendientes/'))).toBe(
    true,
  )
})

test('guardar sin cambiar las fechas no pregunta', async () => {
  const conFechas = { ...campania, fecha_inicio: '2026-11-01', fecha_fin: '2026-11-30' }
  const fetchMock = stubFetch((input, options) => {
    if (input.includes('/campanias/campanias/5/') && options?.method === 'PATCH')
      return ok(conFechas)
    if (input.includes('/campanias/campanias/')) return ok([conFechas])
    return undefined
  })
  render(<CampaniasPage />)
  abrirAcciones((await screen.findByText('Verano 2027')).closest('tr')!)
  fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
  const form = screen.getByRole('form', { name: 'Formulario de campaña' })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar campaña' }))
  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([, options]) => options?.method === 'PATCH')).toBe(true),
  )
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/reservas/'))).toBe(false)
})
