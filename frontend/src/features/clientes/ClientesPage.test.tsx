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
  nombre_visible: 'Agencia Andes',
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

test('muestra el nombre visible de un cliente sin nombre ni tipo', async () => {
  const sinNombre: Cliente = {
    ...agencia,
    id: 3,
    nombre: '',
    nombre_visible: 'Cliente sin nombre #3',
    razon_social: '',
    tipo: '',
    tipo_nombre: '',
  }
  mockFetch((url) => {
    if (url === '/api/clientes/clientes/') return ok([sinNombre])
    if (url.startsWith('/api/clientes/marcas/?cliente=3')) return ok([])
    return undefined
  })
  render(<ClientesPage />)

  expect(await screen.findByText('Cliente sin nombre #3')).toBeDefined()
  expect(screen.getByText('Sin tipo')).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Ver marcas' }))
  expect(screen.getByRole('heading', { name: 'Marcas de Cliente sin nombre #3' })).toBeDefined()
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
    nombre_visible: 'Bodega Sol',
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
  fireEvent.change(within(form).getByLabelText('Nombre'), {
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

test('un cliente directo sin nombre no muestra aviso de marca creada', async () => {
  const creado: Cliente = {
    ...agencia,
    id: 4,
    nombre: '',
    nombre_visible: 'Cliente sin nombre #4',
    razon_social: '',
    cuit: '',
    tipo: 'directo',
    tipo_nombre: 'Directo',
  }
  const fetchMock = mockFetch((url, options) => {
    if (url === '/api/clientes/clientes/' && options?.method === 'POST') return ok(creado)
    if (url === '/api/clientes/clientes/') return ok([])
    if (url === '/api/clientes/marcas/?cliente=4&incluir_inactivos=1') return ok([])
    return undefined
  })
  render(<ClientesPage />)

  fireEvent.click(await screen.findByRole('button', { name: 'Nuevo cliente' }))
  const form = screen.getByRole('form', { name: 'Formulario de cliente' })
  fireEvent.change(within(form).getByLabelText('Tipo'), { target: { value: 'directo' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar cliente' }))

  expect(await screen.findByText('Este cliente todavía no tiene marcas.')).toBeDefined()
  expect(screen.getByRole('heading', { name: 'Marcas de Cliente sin nombre #4' })).toBeDefined()
  expect(screen.queryByText(/Se creó la marca/)).toBeNull()
  const post = fetchMock.mock.calls.find(([, options]) => options?.method === 'POST')
  expect(body(post?.[1])).toMatchObject({ nombre: '', tipo: 'directo' })
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
  // Un intermediario común no tiene contactos múltiples (HU-068, criterio 2).
  expect(screen.queryByRole('region', { name: /Contactos de/ })).toBeNull()
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

test('el error al cargar las marcas de la ficha se anuncia como alerta', async () => {
  mockFetch((url) => {
    if (url === '/api/clientes/clientes/') return ok([agencia])
    if (url.startsWith('/api/clientes/marcas/')) return fail(500, {})
    return undefined
  })
  render(<ClientesPage />)

  fireEvent.click(await screen.findByRole('button', { name: 'Ver marcas' }))
  expect((await screen.findByRole('alert')).textContent).toBe('No se pudieron cargar las marcas.')
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

test('la ficha de un intermediario formal muestra sus contactos', async () => {
  const central = { ...agencia, tipo: 'intermediario_formal' as const }
  mockFetch((url) => {
    if (url === '/api/clientes/clientes/') return ok([central])
    if (url === '/api/clientes/marcas/?cliente=1&incluir_inactivos=1') return ok([])
    if (url === '/api/clientes/contactos/?cliente=1&incluir_inactivos=1')
      return ok([
        {
          id: 5,
          cliente: 1,
          nombre: 'Ana',
          cargo: '',
          correo: '',
          telefono: '',
          notas: '',
          principal: true,
          activo: true,
        },
      ])
    return undefined
  })
  render(<ClientesPage />)
  fireEvent.click(await screen.findByRole('button', { name: 'Ver marcas' }))
  const contactos = await screen.findByRole('region', { name: 'Contactos de Agencia Andes' })
  expect(await within(contactos).findByText('Ana')).toBeDefined()
})
