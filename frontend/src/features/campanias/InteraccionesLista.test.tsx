import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import InteraccionesLista from './InteraccionesLista'
import type { Cliente } from '../clientes/types'
import type { Interaccion } from './types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const fail = (status: number) => ({ ok: false, status, json: async () => ({}) })

const bodega: Cliente = {
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
}

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
  recordatorio_fecha: null,
  recordatorio_texto: '',
  recordatorio_hecho_en: null,
  recordatorio_hecho_por_nombre: null,
}

type Route = (url: string, options?: RequestInit) => unknown

function mockFetch(route: Route) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    // El formulario pide las opciones del cliente; acá no son el tema del test.
    const response =
      route(input, options) ??
      (input.startsWith('/api/clientes/marcas/') || input.startsWith('/api/campanias/campanias/')
        ? ok([])
        : undefined)
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

test('muestra Sin asunto para una interacción sin título', async () => {
  mockFetch((url) => {
    if (url === '/api/campanias/interacciones/?cliente=2') return ok([{ ...llamada, asunto: '' }])
    return undefined
  })
  render(<InteraccionesLista filtro={{ cliente: 2 }} titulo="Interacciones" />)
  expect(await screen.findByText('Sin asunto')).toBeDefined()
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

test('sin cliente para cargar, la lista no ofrece cargar ni editar', async () => {
  mockFetch((url) => {
    if (url === '/api/campanias/interacciones/?cliente=2') return ok([llamada])
    return undefined
  })
  render(<InteraccionesLista filtro={{ cliente: 2 }} titulo="Interacciones" />)
  await screen.findByText('Renovación de pauta')
  expect(screen.queryByRole('button', { name: 'Nueva interacción' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
})

test('crea una interacción del cliente con POST, recarga la lista y avisa la cantidad', async () => {
  let creada = false
  const fetchMock = mockFetch((url, options) => {
    if (url === '/api/campanias/interacciones/' && options?.method === 'POST') {
      creada = true
      return ok(llamada)
    }
    if (url === '/api/campanias/interacciones/?cliente=2') return ok(creada ? [llamada] : [])
    return undefined
  })
  const onCargadas = vi.fn()
  render(
    <InteraccionesLista
      filtro={{ cliente: 2 }}
      titulo="Interacciones"
      ocultar="cliente"
      clienteParaCargar={bodega}
      onCargadas={onCargadas}
    />,
  )

  fireEvent.click(await screen.findByRole('button', { name: 'Nueva interacción' }))
  const form = screen.getByRole('form', { name: 'Formulario de interacción' })
  expect((within(form).getByLabelText('Cliente') as HTMLInputElement).value).toBe('Bodega Norte')
  fireEvent.change(within(form).getByLabelText('Asunto (opcional)'), {
    target: { value: 'Renovación de pauta' },
  })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar interacción' }))

  expect(await screen.findByText('Renovación de pauta')).toBeDefined()
  expect(screen.queryByRole('form', { name: 'Formulario de interacción' })).toBeNull()
  const post = fetchMock.mock.calls.find(([, options]) => options?.method === 'POST')
  expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({ cliente: 2, tipo: 'llamada' })
  expect(onCargadas).toHaveBeenLastCalledWith(1)
})

test('edita una interacción con PATCH', async () => {
  const fetchMock = mockFetch((url, options) => {
    if (url === '/api/campanias/interacciones/5/' && options?.method === 'PATCH') return ok(llamada)
    if (url === '/api/campanias/interacciones/?cliente=2') return ok([llamada])
    return undefined
  })
  render(
    <InteraccionesLista
      filtro={{ cliente: 2 }}
      titulo="Interacciones"
      clienteParaCargar={bodega}
    />,
  )
  fireEvent.click(await screen.findByRole('button', { name: 'Editar' }))
  const form = screen.getByRole('form', { name: 'Formulario de interacción' })
  expect(within(form).getByRole('heading', { name: 'Editar interacción' })).toBeDefined()
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
  await waitFor(() =>
    expect(screen.queryByRole('form', { name: 'Formulario de interacción' })).toBeNull(),
  )
})

test('cancelar cierra el formulario sin guardar', async () => {
  const fetchMock = mockFetch((url) => {
    if (url === '/api/campanias/interacciones/?cliente=2') return ok([])
    return undefined
  })
  render(
    <InteraccionesLista
      filtro={{ cliente: 2 }}
      titulo="Interacciones"
      clienteParaCargar={bodega}
    />,
  )
  fireEvent.click(await screen.findByRole('button', { name: 'Nueva interacción' }))
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
  expect(screen.queryByRole('form', { name: 'Formulario de interacción' })).toBeNull()
  expect(fetchMock.mock.calls.some(([, options]) => options?.method === 'POST')).toBe(false)
})

test('la columna Recordatorio muestra la fecha, qué hacer y si está pendiente o hecho', async () => {
  mockFetch((url) => {
    if (url === '/api/campanias/interacciones/?cliente=2')
      return ok([
        { ...llamada, recordatorio_fecha: '2026-11-02', recordatorio_texto: 'Enviar presupuesto' },
        {
          ...llamada,
          id: 6,
          recordatorio_fecha: '2026-11-05',
          recordatorio_texto: 'Llamar',
          recordatorio_hecho_en: '2026-11-05T12:00:00-03:00',
          recordatorio_hecho_por_nombre: 'operativo',
        },
        { ...llamada, id: 7 },
      ])
    return undefined
  })
  render(<InteraccionesLista filtro={{ cliente: 2 }} titulo="Interacciones" />)
  const tabla = await screen.findByRole('table', { name: 'Interacciones' })
  expect(within(tabla).getByRole('columnheader', { name: 'Recordatorio' })).toBeDefined()
  const filas = within(tabla).getAllByRole('row').slice(1)
  expect(within(filas[0]).getByText('02/11/2026 · Enviar presupuesto')).toBeDefined()
  expect(within(filas[0]).getByText('Pendiente')).toBeDefined()
  expect(within(filas[1]).getByText('05/11/2026 · Llamar')).toBeDefined()
  expect(within(filas[1]).getByText('Hecho')).toBeDefined()
  expect(within(filas[2]).queryByText('Pendiente')).toBeNull()
})
