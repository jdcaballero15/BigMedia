import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import InteraccionesPage from './InteraccionesPage'
import InteraccionesLista from './InteraccionesLista'
import { PuedeEditarContext } from '../../shared/sesion'
import type { Interaccion } from './types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const fail = (status: number) => ({ ok: false, status, json: async () => ({}) })

const clientes = [
  {
    id: 2,
    nombre: 'Bodega Norte',
    razon_social: '',
    cuit: '',
    tipo: 'directo',
    tipo_nombre: 'Directo',
    nombre_visible: 'Bodega Norte',
    telefono: '',
    correo: '',
    activo: true,
  },
]

const llamada: Interaccion = {
  id: 5,
  tipo: 'llamada',
  asunto: 'Renovación de pauta',
  fecha: '2026-10-20',
  notas: 'Pidió cotizar noviembre.',
  cliente: 2,
  cliente_nombre: 'Bodega Norte',
  contacto: null,
  contacto_nombre: null,
  campania: 21,
  campania_nombre: 'Verano 2027',
  marca: 31,
  marca_nombre: 'Marca Sol',
  registrada_por_nombre: 'operativo',
}

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

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('lista las interacciones y filtra por cliente', async () => {
  const fetchMock = mockFetch((url) => {
    if (url.startsWith('/api/clientes/clientes/')) return ok(clientes)
    if (url === '/api/campanias/interacciones/') return ok([llamada])
    if (url === '/api/campanias/interacciones/?cliente=2') return ok([])
    return undefined
  })
  render(<InteraccionesPage />)

  const tabla = await screen.findByRole('table', { name: 'Interacciones' })
  expect(within(tabla).getByText('Renovación de pauta')).toBeDefined()
  expect(within(tabla).getByText('Llamada')).toBeDefined()
  expect(within(tabla).getByText('Verano 2027')).toBeDefined()

  await screen.findByRole('option', { name: 'Bodega Norte' })
  const filtros = screen.getByRole('search', { name: 'Filtros de interacciones' })
  fireEvent.change(within(filtros).getByLabelText('Cliente'), { target: { value: '2' } })
  expect(await screen.findByText('No hay interacciones para este filtro.')).toBeDefined()
  expect(fetchMock).toHaveBeenCalledWith(
    '/api/campanias/interacciones/?cliente=2',
    expect.anything(),
  )
})

test('crea una interacción con POST y vuelve a cargar la lista', async () => {
  let creada = false
  const fetchMock = mockFetch((url, options) => {
    if (url.startsWith('/api/clientes/clientes/')) return ok(clientes)
    if (url.startsWith('/api/campanias/campanias/?cliente=')) return ok([])
    if (url === '/api/campanias/interacciones/' && options?.method === 'POST') {
      creada = true
      return ok(llamada)
    }
    if (url === '/api/campanias/interacciones/') return ok(creada ? [llamada] : [])
    return undefined
  })
  render(<InteraccionesPage />)

  fireEvent.click(await screen.findByRole('button', { name: 'Nueva interacción' }))
  const form = screen.getByRole('form', { name: 'Formulario de interacción' })
  await within(form).findByRole('option', { name: 'Bodega Norte' })
  fireEvent.change(within(form).getByLabelText('Cliente'), { target: { value: '2' } })
  fireEvent.change(within(form).getByLabelText('Asunto'), {
    target: { value: 'Renovación de pauta' },
  })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar interacción' }))

  expect(await screen.findByText('Renovación de pauta')).toBeDefined()
  expect(screen.queryByRole('form', { name: 'Formulario de interacción' })).toBeNull()
  const post = fetchMock.mock.calls.find(([, options]) => options?.method === 'POST')
  expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({ cliente: 2, tipo: 'llamada' })
})

test('edita una interacción con PATCH', async () => {
  const fetchMock = mockFetch((url, options) => {
    if (url.startsWith('/api/clientes/clientes/')) return ok(clientes)
    if (url.startsWith('/api/campanias/campanias/?cliente=')) return ok([])
    if (url === '/api/campanias/interacciones/5/' && options?.method === 'PATCH') return ok(llamada)
    if (url === '/api/campanias/interacciones/') return ok([llamada])
    return undefined
  })
  render(<InteraccionesPage />)
  fireEvent.click(await screen.findByRole('button', { name: 'Editar' }))
  const form = screen.getByRole('form', { name: 'Formulario de interacción' })
  fireEvent.change(within(form).getByLabelText('Notas'), { target: { value: 'Ya cotizado.' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar interacción' }))
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          url === '/api/campanias/interacciones/5/' && options?.method === 'PATCH',
      ),
    ).toBe(true),
  )
})

test('el rol de solo lectura no ve los botones de carga ni de edición', async () => {
  mockFetch((url) => {
    if (url.startsWith('/api/clientes/clientes/')) return ok(clientes)
    if (url === '/api/campanias/interacciones/') return ok([llamada])
    return undefined
  })
  render(
    <PuedeEditarContext.Provider value={false}>
      <InteraccionesPage />
    </PuedeEditarContext.Provider>,
  )
  await screen.findByText('Renovación de pauta')
  expect(screen.queryByRole('button', { name: 'Nueva interacción' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
})

test('avisa si no se pueden cargar las interacciones', async () => {
  mockFetch((url) => {
    if (url.startsWith('/api/clientes/clientes/')) return ok(clientes)
    if (url === '/api/campanias/interacciones/') return fail(500)
    return undefined
  })
  render(<InteraccionesPage />)
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No se pudieron cargar las interacciones.',
  )
})

test('la lista de la ficha filtra por cliente y oculta esa columna', async () => {
  const fetchMock = mockFetch((url) => {
    if (url === '/api/campanias/interacciones/?cliente=2') return ok([llamada])
    return undefined
  })
  render(<InteraccionesLista filtro={{ cliente: 2 }} titulo="Interacciones" ocultar="cliente" />)
  const tabla = await screen.findByRole('table', { name: 'Interacciones' })
  expect(within(tabla).queryByRole('columnheader', { name: 'Cliente' })).toBeNull()
  expect(within(tabla).getByRole('columnheader', { name: 'Campaña' })).toBeDefined()
  expect(within(tabla).getByRole('columnheader', { name: 'Marca' })).toBeDefined()
  expect(within(tabla).getByText('Marca Sol')).toBeDefined()
  expect(within(tabla).getByText('Pidió cotizar noviembre.')).toBeDefined()
  expect(fetchMock).toHaveBeenCalledTimes(1)
})

test('la lista de la campaña muestra el vacío y el error', async () => {
  mockFetch((url) => {
    if (url === '/api/campanias/interacciones/?campania=21') return ok([])
    if (url === '/api/campanias/interacciones/?campania=22') return fail(500)
    return undefined
  })
  render(<InteraccionesLista filtro={{ campania: 21 }} titulo="De la campaña" ocultar="campania" />)
  expect(await screen.findByText('Todavía no hay interacciones registradas.')).toBeDefined()
  cleanup()
  render(<InteraccionesLista filtro={{ campania: 22 }} titulo="De la campaña" />)
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No se pudieron cargar las interacciones.',
  )
})
