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
  estado: 'confirmada',
  ordenes_publicidad: [],
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

test('crea la campaña con su orden de publicidad en un solo pedido multipart', async () => {
  const fetchMock = stubFetch((input, options) => {
    if (input.includes('/campanias/campanias/') && options?.method === 'POST') return ok({ id: 9 })
    return undefined
  })
  render(<CampaniasPage />)
  await screen.findByText('Verano 2027')
  fireEvent.click(screen.getByRole('button', { name: 'Nueva campaña' }))
  const form = screen.getByRole('form', { name: 'Formulario de campaña' })
  fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'Invierno' } })
  const pdf = new File(['%PDF-1.4'], 'op.pdf', { type: 'application/pdf' })
  fireEvent.change(within(form).getByLabelText('Orden de publicidad (PDF)'), {
    target: { files: [pdf] },
  })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar campaña' }))
  await waitFor(() => {
    const llamada = fetchMock.mock.calls.find(
      ([url, options]) => String(url) === '/api/campanias/campanias/' && options?.method === 'POST',
    )
    expect(llamada).toBeDefined()
    const cuerpo = llamada?.[1]?.body as FormData
    expect(cuerpo.get('nombre')).toBe('Invierno')
    expect(cuerpo.get('marca')).toBe('')
    expect(cuerpo.has('estado')).toBe(false)
    expect((cuerpo.getAll('ordenes_publicidad')[0] as File).name).toBe('op.pdf')
  })
})

test('al cambiar las fechas no toca las reservas (HU-058)', async () => {
  const conFechas = { ...campania, fecha_inicio: '2026-11-01', fecha_fin: '2026-11-30' }
  const fetchMock = stubFetch((input, options) => {
    if (input.includes('/campanias/campanias/5/') && options?.method === 'PATCH')
      return ok({ ...conFechas, fecha_inicio: '2026-12-01', fecha_fin: '2026-12-31' })
    if (input.includes('/campanias/campanias/')) return ok([conFechas])
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
  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([, options]) => options?.method === 'PATCH')).toBe(true),
  )
  expect(screen.queryByRole('alertdialog')).toBeNull()
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/reservas/'))).toBe(false)
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

// --- Alta con posiciones y carteles antes de guardar (HU-055 criterio 5, HU-056 criterio 7) ---

const cartelLibre = (id: number) => ({
  id,
  nombre_visible: `Av. Alta ${id} · 8x3`,
  zona_nombre: 'Ciudad',
  proveedor_nombre: null,
  tarifa_lista: '1000.00',
  capacidad: 1,
  ocupados: 0,
  en_campania: false,
})

function stubAlta(fallidas: { cartel: number; motivo: string }[] = []) {
  return stubFetch((input, options) => {
    if (input === '/api/campanias/campanias/' && options?.method === 'POST')
      return ok({ ...campania, id: 9, nombre: 'Invierno' })
    if (input.includes('/inventario/formatos/'))
      return ok([{ id: 10, nombre: 'Gran Formato', activo: true }])
    if (input.includes('/inventario/zonas/') || input.includes('/inventario/proveedores/'))
      return ok([])
    if (input.includes('/carteles-para-tanda/')) return ok([cartelLibre(1), cartelLibre(2)])
    if (input.includes('/lineas-formato/')) return ok({ id: 70 })
    if (input.includes('/en-bloque/')) {
      const ids = (JSON.parse(String(options?.body)) as { carteles: number[] }).carteles
      const fallan = new Set(fallidas.map((item) => item.cartel))
      const creadas = ids.filter((id) => !fallan.has(id)).map((id) => ({ cartel: id, reserva: id }))
      return ok({ creadas, existentes: [], fallidas })
    }
    return undefined
  })
}

async function armarAltaConCarteles() {
  render(<CampaniasPage />)
  await screen.findByText('Verano 2027')
  fireEvent.click(screen.getByRole('button', { name: 'Nueva campaña' }))
  const form = screen.getByRole('form', { name: 'Formulario de campaña' })
  fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'Invierno' } })
  fireEvent.change(within(form).getByLabelText('Fecha de inicio'), {
    target: { value: '01/11/2026' },
  })
  fireEvent.change(within(form).getByLabelText('Fecha de fin'), { target: { value: '30/11/2026' } })
  await within(form).findByRole('option', { name: 'Gran Formato' })
  fireEvent.change(within(form).getByLabelText('Formato'), { target: { value: '10' } })
  fireEvent.change(within(form).getByLabelText('Cantidad'), { target: { value: '2' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Agregar línea' }))
  fireEvent.click(within(form).getByRole('button', { name: 'Agregar carteles' }))
  fireEvent.click(await within(form).findByLabelText('Elegir Av. Alta 1 · 8x3'))
  fireEvent.click(within(form).getByLabelText('Elegir Av. Alta 2 · 8x3'))
  fireEvent.click(within(form).getByRole('button', { name: 'Usar selección' }))
  return form
}

const posts = (fetchMock: ReturnType<typeof stubFetch>) =>
  fetchMock.mock.calls
    .filter(([, options]) => options?.method === 'POST')
    .map(([url, options]) => ({ url: String(url), body: JSON.parse(String(options?.body)) }))

test('el alta muestra posiciones por formato y la edición no', async () => {
  stubAlta()
  render(<CampaniasPage />)
  await screen.findByText('Verano 2027')
  fireEvent.click(screen.getByRole('button', { name: 'Nueva campaña' }))
  expect(screen.getByRole('region', { name: 'Posiciones por formato' })).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
  abrirAcciones(screen.getByText('Verano 2027').closest('tr')!)
  fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
  expect(screen.queryByRole('region', { name: 'Posiciones por formato' })).toBeNull()
})

test('elegir carteles en el alta no guarda nada hasta Guardar campaña', async () => {
  const fetchMock = stubAlta()
  const form = await armarAltaConCarteles()
  expect(within(form).getByText('Carteles elegidos: 2')).toBeDefined()
  expect(posts(fetchMock)).toHaveLength(0)
  fireEvent.click(within(form).getByRole('button', { name: 'Cancelar' }))
  expect(posts(fetchMock)).toHaveLength(0)
})

test('al guardar el alta crea la campaña, su línea y sus reservas en ese orden', async () => {
  const fetchMock = stubAlta()
  const form = await armarAltaConCarteles()
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar campaña' }))
  const resumen = await screen.findByRole('status', { name: 'Resultado del alta' })
  expect(resumen.textContent).toContain('Se creó la campaña «Invierno» con 2 reservas.')
  const enviados = posts(fetchMock)
  expect(enviados.map((post) => post.url)).toEqual([
    '/api/campanias/campanias/',
    '/api/campanias/lineas-formato/',
    '/api/reservas/reservas/en-bloque/',
  ])
  expect(enviados[0]?.body).not.toHaveProperty('lineas')
  expect(enviados[1]?.body).toEqual({ campania: 9, formato: 10, cantidad: 2 })
  expect(enviados[2]?.body).toEqual({
    campania: 9,
    fecha_inicio: '2026-11-01',
    fecha_fin: '2026-11-30',
    carteles: [1, 2],
  })
  expect(screen.queryByRole('form', { name: 'Formulario de campaña' })).toBeNull()
})

test('si un cartel ya no tiene cupo al guardar, el resumen muestra cuál y por qué', async () => {
  stubAlta([{ cartel: 2, motivo: 'El cartel no tiene cupo en esas fechas.' }])
  const form = await armarAltaConCarteles()
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar campaña' }))
  const resumen = await screen.findByRole('status', { name: 'Resultado del alta' })
  expect(resumen.textContent).toContain('con 1 reserva.')
  const fallidos = within(resumen).getByRole('list', { name: 'Carteles fallidos' })
  expect(fallidos.textContent).toContain(
    'Av. Alta 2 · 8x3: El cartel no tiene cupo en esas fechas.',
  )
  fireEvent.click(within(resumen).getByRole('button', { name: 'Cerrar' }))
  expect(screen.queryByRole('status', { name: 'Resultado del alta' })).toBeNull()
})

test('si la línea no se puede guardar, el resumen la muestra con su motivo', async () => {
  const base = stubAlta()
  const original = base.getMockImplementation()!
  base.mockImplementation(async (input: string, options?: RequestInit) =>
    input.includes('/lineas-formato/')
      ? { ok: false, status: 400, json: async () => ({ detail: 'Formato inactivo.' }) }
      : original(input, options),
  )
  const form = await armarAltaConCarteles()
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar campaña' }))
  const resumen = await screen.findByRole('status', { name: 'Resultado del alta' })
  const lineas = within(resumen).getByRole('list', { name: 'Líneas fallidas' })
  expect(lineas.textContent).toContain('Gran Formato:')
  expect(resumen.textContent).toContain('con 2 reservas.')
})
