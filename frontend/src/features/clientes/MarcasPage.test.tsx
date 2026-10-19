import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import MarcasPage from './MarcasPage'
import type { Cliente, Marca, Rubro } from './types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const fail = (status: number, data: unknown) => ({ ok: false, status, json: async () => data })

const base = { razon_social: '', cuit: '', tipo_nombre: 'Intermediario', telefono: '', correo: '' }
const clientes: Cliente[] = [
  {
    ...base,
    id: 1,
    nombre: 'Agencia Andes',
    nombre_visible: 'Agencia Andes',
    tipo: 'intermediario',
    activo: true,
  },
  { ...base, id: 6, nombre: '', nombre_visible: 'Cliente sin nombre #6', tipo: '', activo: true },
  {
    ...base,
    id: 2,
    nombre: 'Agencia Cerrada',
    nombre_visible: 'Agencia Cerrada',
    tipo: 'intermediario',
    activo: false,
  },
]
const rubros: Rubro[] = [
  { id: 3, nombre: 'Bebidas', activo: true },
  { id: 4, nombre: 'Viejo rubro', activo: false },
]
const marca: Marca = {
  id: 7,
  nombre: 'Agua Cumbre',
  cliente: 1,
  cliente_nombre: 'Agencia Andes',
  rubro: 3,
  rubro_nombre: 'Bebidas',
  activo: true,
}

type Route = (url: string, options?: RequestInit) => unknown

function mockFetch(route: Route) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const response = route(input, options)
    if (response !== undefined) return response
    if (input === '/api/clientes/clientes/?incluir_inactivos=1') return ok(clientes)
    if (input === '/api/clientes/rubros/?incluir_inactivos=1') return ok(rubros)
    if (input.startsWith('/api/clientes/marcas/')) return ok([marca])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const writes = (fetchMock: ReturnType<typeof mockFetch>, method: string) =>
  fetchMock.mock.calls
    .filter(([, options]) => options?.method === method)
    .map(([url, options]) => [String(url), JSON.parse(String(options?.body))] as const)

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('lista las marcas y filtra por cliente, rubro y nombre', async () => {
  const fetchMock = mockFetch(() => undefined)
  render(<MarcasPage />)

  const tabla = await screen.findByRole('table', { name: 'Marcas' })
  expect(await within(tabla).findByText('Agua Cumbre')).toBeDefined()
  expect(within(tabla).getByText('Agencia Andes')).toBeDefined()
  const filtros = screen.getByRole('search', { name: 'Filtros de marcas' })
  await within(filtros).findByRole('option', { name: 'Agencia Andes' })
  expect(within(filtros).getByRole('option', { name: 'Cliente sin nombre #6' })).toBeDefined()
  fireEvent.change(within(filtros).getByLabelText('Cliente'), { target: { value: '1' } })
  fireEvent.change(within(filtros).getByLabelText('Rubro'), { target: { value: '3' } })
  fireEvent.change(within(filtros).getByLabelText('Buscar'), { target: { value: 'agua' } })
  fireEvent.click(within(filtros).getByLabelText('Incluir inactivas'))
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url]) =>
          String(url) === '/api/clientes/marcas/?cliente=1&rubro=3&q=agua&incluir_inactivos=1',
      ),
    ).toBe(true),
  )
})

test('avisa cuando no hay marcas y cuando falla la carga', async () => {
  let fallar = false
  mockFetch((url) => {
    if (url.startsWith('/api/clientes/marcas/')) return fallar ? fail(500, {}) : ok([])
    return undefined
  })
  render(<MarcasPage />)

  expect(await screen.findByText('No hay marcas para estos filtros.')).toBeDefined()
  fallar = true
  fireEvent.click(screen.getByLabelText('Incluir inactivas'))
  expect(await screen.findByText('No se pudieron cargar las marcas.')).toBeDefined()
})

test('una carga correcta de marcas no borra el error de clientes o rubros', async () => {
  mockFetch((url) =>
    url === '/api/clientes/clientes/?incluir_inactivos=1' ? fail(500, {}) : undefined,
  )
  render(<MarcasPage />)

  expect(await screen.findByText('Agua Cumbre')).toBeDefined()
  fireEvent.click(screen.getByLabelText('Incluir inactivas'))
  await waitFor(() => expect(screen.getAllByText('Agua Cumbre')).toHaveLength(1))
  expect(screen.getByText('No se pudieron cargar los clientes.')).toBeDefined()
})

test('al recargar los rubros con éxito se limpia solo el error de rubros', async () => {
  let rubrosFallan = true
  mockFetch((url, options) => {
    if (url === '/api/clientes/rubros/' && options?.method === 'POST') {
      rubrosFallan = false
      return ok({ id: 5 })
    }
    if (url === '/api/clientes/rubros/?incluir_inactivos=1' && rubrosFallan) return fail(500, {})
    return undefined
  })
  render(<MarcasPage />)

  expect(await screen.findByText('No se pudieron cargar los rubros.')).toBeDefined()
  const seccion = screen.getByRole('region', { name: 'Rubros' })
  fireEvent.click(within(seccion).getByRole('button', { name: 'Nuevo rubro' }))
  fireEvent.change(within(seccion).getByLabelText('Nombre del rubro'), {
    target: { value: 'Turismo' },
  })
  fireEvent.click(within(seccion).getByRole('button', { name: 'Guardar rubro' }))
  expect(await within(seccion).findByText('Bebidas')).toBeDefined()
  expect(screen.queryByText('No se pudieron cargar los rubros.')).toBeNull()
})

test('crea una marca ofreciendo solo clientes activos', async () => {
  const fetchMock = mockFetch((url, options) =>
    url === '/api/clientes/marcas/' && options?.method === 'POST' ? ok({ id: 9 }) : undefined,
  )
  render(<MarcasPage />)

  await screen.findByText('Agua Cumbre')
  fireEvent.click(screen.getByRole('button', { name: 'Nueva marca' }))
  const form = screen.getByRole('form', { name: 'Formulario de marca' })
  expect(within(form).queryByRole('option', { name: /Agencia Cerrada/ })).toBeNull()
  fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'Vino Alto' } })
  fireEvent.change(within(form).getByLabelText('Cliente'), { target: { value: '1' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar marca' }))

  await waitFor(() =>
    expect(screen.queryByRole('form', { name: 'Formulario de marca' })).toBeNull(),
  )
  expect(writes(fetchMock, 'POST')).toEqual([
    ['/api/clientes/marcas/', { nombre: 'Vino Alto', cliente: 1, rubro: null, activo: true }],
  ])
})

test('edita e inactiva una marca con PATCH', async () => {
  const fetchMock = mockFetch((url, options) =>
    url === '/api/clientes/marcas/7/' && options?.method === 'PATCH' ? ok(marca) : undefined,
  )
  vi.stubGlobal('confirm', () => true)
  render(<MarcasPage />)

  const tabla = await screen.findByRole('table', { name: 'Marcas' })
  await within(tabla).findByText('Agua Cumbre')
  fireEvent.click(within(tabla).getByRole('button', { name: 'Editar' }))
  const form = screen.getByRole('form', { name: 'Formulario de marca' })
  fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'Agua Cumbre Sur' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar marca' }))
  await waitFor(() =>
    expect(screen.queryByRole('form', { name: 'Formulario de marca' })).toBeNull(),
  )
  fireEvent.click(within(tabla).getByRole('button', { name: 'Inactivar' }))

  await waitFor(() =>
    expect(writes(fetchMock, 'PATCH')).toEqual([
      [
        '/api/clientes/marcas/7/',
        { nombre: 'Agua Cumbre Sur', cliente: 1, rubro: 3, activo: true },
      ],
      ['/api/clientes/marcas/7/', { activo: false }],
    ]),
  )
})

test('informa el error de la API al inactivar una marca', async () => {
  mockFetch((_url, options) =>
    options?.method === 'PATCH' ? fail(403, { detail: 'No tenés permiso.' }) : undefined,
  )
  vi.stubGlobal('confirm', () => true)
  render(<MarcasPage />)

  const tabla = await screen.findByRole('table', { name: 'Marcas' })
  await within(tabla).findByText('Agua Cumbre')
  fireEvent.click(within(tabla).getByRole('button', { name: 'Inactivar' }))
  expect((await screen.findByRole('alert')).textContent).toBe('No tenés permiso.')
})

test('administra rubros: alta, cambio de nombre e inactivación', async () => {
  const fetchMock = mockFetch((url, options) => {
    if (url === '/api/clientes/rubros/' && options?.method === 'POST') return ok({ id: 5 })
    if (url === '/api/clientes/rubros/3/' && options?.method === 'PATCH') return ok({ id: 3 })
    return undefined
  })
  vi.stubGlobal('confirm', () => true)
  render(<MarcasPage />)

  const seccion = screen.getByRole('region', { name: 'Rubros' })
  expect(await within(seccion).findByText('Viejo rubro')).toBeDefined()
  expect(within(seccion).getByText('Inactivo')).toBeDefined()

  fireEvent.click(within(seccion).getByRole('button', { name: 'Nuevo rubro' }))
  let form = within(seccion).getByRole('form', { name: 'Formulario de rubro' })
  fireEvent.change(within(form).getByLabelText('Nombre del rubro'), {
    target: { value: ' Gastronomía ' },
  })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar rubro' }))
  await waitFor(() =>
    expect(within(seccion).queryByRole('form', { name: 'Formulario de rubro' })).toBeNull(),
  )

  fireEvent.click(within(seccion).getAllByRole('button', { name: 'Renombrar' })[0])
  form = within(seccion).getByRole('form', { name: 'Formulario de rubro' })
  expect((within(form).getByLabelText('Nombre del rubro') as HTMLInputElement).value).toBe(
    'Bebidas',
  )
  fireEvent.change(within(form).getByLabelText('Nombre del rubro'), {
    target: { value: 'Bebidas y jugos' },
  })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar rubro' }))
  await waitFor(() =>
    expect(within(seccion).queryByRole('form', { name: 'Formulario de rubro' })).toBeNull(),
  )
  fireEvent.click(within(seccion).getByRole('button', { name: 'Inactivar' }))

  await waitFor(() =>
    expect(writes(fetchMock, 'PATCH')).toEqual([
      ['/api/clientes/rubros/3/', { nombre: 'Bebidas y jugos' }],
      ['/api/clientes/rubros/3/', { activo: false }],
    ]),
  )
  expect(writes(fetchMock, 'POST')).toEqual([['/api/clientes/rubros/', { nombre: 'Gastronomía' }]])
})

test('muestra el error de la API al guardar un rubro repetido', async () => {
  mockFetch((url, options) =>
    url === '/api/clientes/rubros/' && options?.method === 'POST'
      ? fail(400, { nombre: ['Ya existe un rubro con ese nombre.'] })
      : undefined,
  )
  render(<MarcasPage />)

  const seccion = screen.getByRole('region', { name: 'Rubros' })
  await within(seccion).findByText('Bebidas')
  fireEvent.click(within(seccion).getByRole('button', { name: 'Nuevo rubro' }))
  const form = within(seccion).getByRole('form', { name: 'Formulario de rubro' })
  fireEvent.change(within(form).getByLabelText('Nombre del rubro'), {
    target: { value: 'bebidas' },
  })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar rubro' }))
  expect(await within(form).findByText('Ya existe un rubro con ese nombre.')).toBeDefined()
  fireEvent.click(within(form).getByRole('button', { name: 'Cancelar' }))
  expect(within(seccion).queryByRole('form', { name: 'Formulario de rubro' })).toBeNull()
})
