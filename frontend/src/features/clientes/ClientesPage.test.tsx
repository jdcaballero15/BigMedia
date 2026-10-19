import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import ClientesPage from './ClientesPage'
import type { Cliente, Marca } from './types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const fail = (status: number, data: unknown) => ({ ok: false, status, json: async () => data })

const agencia: Cliente = {
  id: 1,
  nombre: 'Agencia Andes',
  razon_social: 'Andes Medios SA',
  cuit: '30712345678',
  tipo: 'intermediario',
  tipo_nombre: 'Intermediario',
  telefono: '261 400 0000',
  correo: '',
  activo: true,
}
const marcasAgencia: Marca[] = [
  {
    id: 7,
    nombre: 'Agua Cumbre',
    cliente: 1,
    cliente_nombre: 'Agencia Andes',
    rubro: 3,
    rubro_nombre: 'Bebidas',
    activo: true,
  },
  {
    id: 8,
    nombre: 'Vino Alto',
    cliente: 1,
    cliente_nombre: 'Agencia Andes',
    rubro: null,
    rubro_nombre: null,
    activo: false,
  },
]

type Route = (url: string, options?: RequestInit) => unknown

function mockFetch(route: Route) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const response = route(input, options)
    if (response === undefined) throw new Error(`URL inesperada: ${input}`)
    return response
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const called = (fetchMock: ReturnType<typeof mockFetch>, check: (url: string) => boolean) =>
  fetchMock.mock.calls.some(([url]) => check(String(url)))

const body = (options?: RequestInit) => JSON.parse(String(options?.body)) as Record<string, unknown>

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('busca clientes por parte del nombre o la razón social', async () => {
  const fetchMock = mockFetch((url) => {
    if (url === '/api/clientes/clientes/') return ok([agencia])
    if (url === '/api/clientes/clientes/?q=andes') return ok([agencia])
    return undefined
  })
  render(<ClientesPage />)

  expect(await screen.findByText('Agencia Andes')).toBeDefined()
  expect(screen.getByText('Andes Medios SA')).toBeDefined()
  fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: ' andes ' } })
  await waitFor(() =>
    expect(called(fetchMock, (url) => url === '/api/clientes/clientes/?q=andes')).toBe(true),
  )
  expect(await screen.findByText('Agencia Andes')).toBeDefined()
})

test('combina el filtro por tipo con los inactivos y avisa si no hay resultados', async () => {
  const fetchMock = mockFetch((url) =>
    url.startsWith('/api/clientes/clientes/') ? ok([]) : undefined,
  )
  render(<ClientesPage />)

  expect(await screen.findByText('No hay clientes para estos filtros.')).toBeDefined()
  fireEvent.change(screen.getByLabelText('Tipo de cliente'), {
    target: { value: 'intermediario_formal' },
  })
  fireEvent.click(screen.getByLabelText('Incluir inactivos'))
  await waitFor(() =>
    expect(
      called(
        fetchMock,
        (url) => url === '/api/clientes/clientes/?tipo=intermediario_formal&incluir_inactivos=1',
      ),
    ).toBe(true),
  )
})

test('muestra un error si no se pueden cargar los clientes', async () => {
  mockFetch(() => fail(500, {}))
  render(<ClientesPage />)
  expect((await screen.findByRole('alert')).textContent).toBe('No se pudieron cargar los clientes.')
})

test('al crear un cliente directo muestra la marca que creó la API', async () => {
  const creado: Cliente = {
    ...agencia,
    id: 2,
    nombre: 'Bodega Sol',
    razon_social: 'Bodega Sol SA',
    cuit: '',
    tipo: 'directo',
    tipo_nombre: 'Directo',
  }
  const fetchMock = mockFetch((url, options) => {
    if (url === '/api/clientes/clientes/' && options?.method === 'POST') return ok(creado)
    if (url === '/api/clientes/clientes/') return ok([])
    if (url === '/api/clientes/marcas/?cliente=2&incluir_inactivos=1')
      return ok([{ ...marcasAgencia[0], id: 11, nombre: 'Bodega Sol', cliente: 2, rubro: null }])
    return undefined
  })
  render(<ClientesPage />)

  fireEvent.click(await screen.findByRole('button', { name: 'Nuevo cliente' }))
  const form = screen.getByRole('form', { name: 'Formulario de cliente' })
  fireEvent.change(within(form).getByLabelText('Nombre de fantasía'), {
    target: { value: 'Bodega Sol' },
  })
  fireEvent.change(within(form).getByLabelText('Razón social'), {
    target: { value: 'Bodega Sol SA' },
  })
  fireEvent.change(within(form).getByLabelText('Tipo'), { target: { value: 'directo' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar cliente' }))

  expect(
    await screen.findByText('Se creó la marca «Bodega Sol» para este cliente directo.'),
  ).toBeDefined()
  expect(screen.queryByRole('form', { name: 'Formulario de cliente' })).toBeNull()
  const post = fetchMock.mock.calls.find(([, options]) => options?.method === 'POST')
  expect(body(post?.[1])).toMatchObject({ nombre: 'Bodega Sol', tipo: 'directo' })
})

test('la ficha de un intermediario lista todas sus marcas', async () => {
  mockFetch((url) => {
    if (url === '/api/clientes/clientes/') return ok([agencia])
    if (url === '/api/clientes/marcas/?cliente=1&incluir_inactivos=1') return ok(marcasAgencia)
    return undefined
  })
  render(<ClientesPage />)

  fireEvent.click(await screen.findByRole('button', { name: 'Ver marcas' }))
  const ficha = screen.getByRole('region', { name: 'Marcas de Agencia Andes' })
  expect(await within(ficha).findByText('Agua Cumbre')).toBeDefined()
  expect(within(ficha).getByText('Vino Alto')).toBeDefined()
  expect(within(ficha).getByText('Bebidas')).toBeDefined()
  expect(within(ficha).getByText('Inactiva')).toBeDefined()
  expect(screen.queryByText(/Se creó la marca/)).toBeNull()
  fireEvent.click(within(ficha).getByRole('button', { name: 'Cerrar' }))
  expect(screen.queryByRole('region', { name: 'Marcas de Agencia Andes' })).toBeNull()
})

test.each([
  [ok([]), 'Este cliente todavía no tiene marcas.'],
  [fail(500, {}), 'No se pudieron cargar las marcas.'],
])('la ficha avisa cuando no hay marcas o fallan', async (respuesta, mensaje) => {
  mockFetch((url) => {
    if (url === '/api/clientes/clientes/') return ok([agencia])
    if (url.startsWith('/api/clientes/marcas/')) return respuesta
    return undefined
  })
  render(<ClientesPage />)

  fireEvent.click(await screen.findByRole('button', { name: 'Ver marcas' }))
  expect(await screen.findByText(mensaje)).toBeDefined()
})

test('edita un cliente con PATCH y muestra su ficha mientras se edita', async () => {
  const fetchMock = mockFetch((url, options) => {
    if (url === '/api/clientes/clientes/1/' && options?.method === 'PATCH')
      return ok({ ...agencia, telefono: '261 999' })
    if (url === '/api/clientes/clientes/') return ok([agencia])
    if (url.startsWith('/api/clientes/marcas/?cliente=1')) return ok(marcasAgencia)
    return undefined
  })
  render(<ClientesPage />)

  fireEvent.click(await screen.findByRole('button', { name: 'Editar' }))
  const form = screen.getByRole('form', { name: 'Formulario de cliente' })
  expect(await screen.findByText('Agua Cumbre')).toBeDefined()
  fireEvent.change(within(form).getByLabelText('Teléfono'), { target: { value: '261 999' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar cliente' }))

  await waitFor(() =>
    expect(screen.queryByRole('form', { name: 'Formulario de cliente' })).toBeNull(),
  )
  const patch = fetchMock.mock.calls.find(([, options]) => options?.method === 'PATCH')
  expect(body(patch?.[1])).toMatchObject({ telefono: '261 999', tipo: 'intermediario' })
})

test('inactiva un cliente sin borrarlo', async () => {
  const fetchMock = mockFetch((url, options) => {
    if (url === '/api/clientes/clientes/1/' && options?.method === 'PATCH')
      return ok({ ...agencia, activo: false })
    if (url === '/api/clientes/clientes/') return ok([agencia])
    return undefined
  })
  vi.stubGlobal('confirm', () => true)
  render(<ClientesPage />)

  fireEvent.click(await screen.findByRole('button', { name: 'Inactivar' }))
  await waitFor(() => {
    const patch = fetchMock.mock.calls.find(([, options]) => options?.method === 'PATCH')
    expect(body(patch?.[1])).toEqual({ activo: false })
  })
})

test('informa el error de la API al inactivar', async () => {
  mockFetch((url, options) => {
    if (options?.method === 'PATCH') return fail(403, { detail: 'No tenés permiso.' })
    if (url === '/api/clientes/clientes/') return ok([agencia])
    return undefined
  })
  vi.stubGlobal('confirm', () => true)
  render(<ClientesPage />)

  fireEvent.click(await screen.findByRole('button', { name: 'Inactivar' }))
  expect((await screen.findByRole('alert')).textContent).toBe('No tenés permiso.')
})
