import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import ItemsPage from './ItemsPage'
import { PuedeEditarContext } from '../../shared/sesion'
import { mesActual } from './types'
import type { ItemFacturacion } from './types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const rechazo = (data: unknown) => ({ ok: false, status: 400, json: async () => data })

function item(id: number, extra: Partial<ItemFacturacion> = {}): ItemFacturacion {
  return {
    id,
    mes: '2026-11-01',
    cliente: 1,
    cliente_nombre: 'Cliente Uno',
    cuit_facturacion: '20123456786',
    marca: null,
    marca_nombre: null,
    campania: null,
    campania_nombre: null,
    descripcion: `Ítem ${id}`,
    periodo_desde: null,
    periodo_hasta: null,
    cantidad: '10.00',
    precio_unitario: '1000.00',
    neto: '10000.00',
    alicuota_iva: '21.00',
    iva: '2100.00',
    total: '12100.00',
    tipo_servicio: 'alquiler',
    tipo_soporte: '',
    sector: null,
    sector_nombre: null,
    tipo_venta: null,
    tipo_venta_nombre: null,
    notas: '',
    estado: 'borrador',
    numero_factura: '',
    creado_por_nombre: 'operativo',
    ...extra,
  }
}

const totales = { mes: '2026-11', cantidad: 2, neto: '10000.00', iva: '2100.00', total: '12100.00' }

function stubFetch(
  items: ItemFacturacion[],
  overrides?: (input: string, options?: RequestInit) => unknown,
) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const custom = overrides?.(input, options)
    if (custom) return custom
    if (input.includes('/clientes/clientes/')) return ok([])
    if (input.includes('/clientes/marcas/')) return ok([])
    if (input.includes('/campanias/campanias/')) return ok([])
    if (input.includes('/facturacion/catalogos/')) return ok({ sectores: [], tipos_venta: [] })
    if (input.includes('/items/totales/')) return ok(totales)
    if (input.includes('/facturacion/items/')) return ok(items)
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function patches(fetchMock: ReturnType<typeof stubFetch>) {
  return fetchMock.mock.calls
    .filter(([, options]) => options?.method === 'PATCH')
    .map(([url, options]) => [url, JSON.parse(String(options?.body))])
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('lista los ítems del mes actual con sus importes y los totales sin anulados', async () => {
  const fetchMock = stubFetch([item(1), item(2, { estado: 'anulado' })])
  render(<ItemsPage />)
  expect(await screen.findByText('Ítem 1')).toBeDefined()
  // Dos filas más el total del mes.
  expect(screen.getAllByText('$12.100,00')).toHaveLength(3)
  expect(screen.getByLabelText('Totales del mes').textContent).toContain('2 ítems')
  expect(screen.getByLabelText('Totales del mes').textContent).toContain('(sin anulados)')
  const mes = mesActual()
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes(`items/?mes=${mes}`))).toBe(true)
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes(`totales/?mes=${mes}`))).toBe(
    true,
  )
})

test('filtra por mes y estado', async () => {
  const fetchMock = stubFetch([item(1)])
  render(<ItemsPage />)
  await screen.findByText('Ítem 1')
  fireEvent.change(screen.getByLabelText('Mes'), { target: { value: '2026-12' } })
  fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'enviado' } })
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(([url]) =>
        String(url).includes('items/?mes=2026-12&estado=enviado'),
      ),
    ).toBe(true),
  )
})

test('sin ítems lo avisa', async () => {
  stubFetch([])
  render(<ItemsPage />)
  expect(await screen.findByText('No hay ítems en este mes.')).toBeDefined()
})

test('si falla la carga muestra el error', async () => {
  stubFetch([], (input) =>
    input.includes('/totales/') ? { ok: false, status: 500, json: async () => ({}) } : undefined,
  )
  render(<ItemsPage />)
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No se pudieron cargar los ítems del mes.',
  )
})

test('crea un ítem nuevo y recarga', async () => {
  const fetchMock = stubFetch([], (_input, options) =>
    options?.method === 'POST' ? ok(item(9)) : undefined,
  )
  render(<ItemsPage />)
  await screen.findByText('No hay ítems en este mes.')
  fireEvent.click(screen.getByRole('button', { name: 'Nuevo ítem' }))
  const form = screen.getByRole('form', { name: 'Formulario de ítem a facturar' })
  fireEvent.change(within(form).getByLabelText('Importe neto'), { target: { value: '500' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar ítem' }))
  await waitFor(() =>
    expect(screen.queryByRole('form', { name: 'Formulario de ítem a facturar' })).toBeNull(),
  )
  const [, options] = fetchMock.mock.calls.find(([, o]) => o?.method === 'POST') ?? []
  expect(JSON.parse(String(options?.body)).neto).toBe('500')
})

test('solo los ítems en Borrador se editan', async () => {
  stubFetch([item(1), item(2, { estado: 'enviado' })])
  render(<ItemsPage />)
  const enviado = (await screen.findByText('Ítem 2')).closest('tr') as HTMLElement
  expect(within(enviado).queryByRole('button', { name: 'Editar' })).toBeNull()
  const borrador = screen.getByText('Ítem 1').closest('tr') as HTMLElement
  fireEvent.click(within(borrador).getByRole('button', { name: 'Editar' }))
  expect(screen.getByRole('heading', { name: 'Editar ítem' })).toBeDefined()
})

test('guarda la edición de un ítem', async () => {
  const fetchMock = stubFetch([item(1)], (_input, options) =>
    options?.method === 'PATCH' ? ok(item(1)) : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Editar' }))
  const form = screen.getByRole('form', { name: 'Formulario de ítem a facturar' })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar ítem' }))
  await waitFor(() => expect(patches(fetchMock)).toHaveLength(1))
  expect(patches(fetchMock)[0][0]).toBe('/api/facturacion/items/1/')
})

test('anula un ítem', async () => {
  const fetchMock = stubFetch([item(1)], (_input, options) =>
    options?.method === 'PATCH' ? ok(item(1, { estado: 'anulado' })) : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Anular' }))
  await waitFor(() =>
    expect(patches(fetchMock)).toEqual([['/api/facturacion/items/1/', { estado: 'anulado' }]]),
  )
})

test('marca facturado con el número de factura', async () => {
  const fetchMock = stubFetch([item(1, { estado: 'enviado' })], (_input, options) =>
    options?.method === 'PATCH' ? ok(item(1, { estado: 'facturado' })) : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Marcar facturado' }))
  fireEvent.change(within(fila).getByLabelText('Número de factura'), {
    target: { value: 'A-0001-00000123' },
  })
  fireEvent.click(within(fila).getByRole('button', { name: 'Confirmar' }))
  await waitFor(() =>
    expect(patches(fetchMock)).toEqual([
      ['/api/facturacion/items/1/', { estado: 'facturado', numero_factura: 'A-0001-00000123' }],
    ]),
  )
})

test('muestra el error del servidor al facturar sin número', async () => {
  stubFetch([item(1, { estado: 'enviado' })], (_input, options) =>
    options?.method === 'PATCH'
      ? rechazo({ numero_factura: ['Cargá el número de factura para pasar el ítem a Facturado.'] })
      : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Marcar facturado' }))
  fireEvent.click(within(fila).getByRole('button', { name: 'Confirmar' }))
  expect(
    await within(fila).findByText('Cargá el número de factura para pasar el ítem a Facturado.'),
  ).toBeDefined()
})

test('un error sin campos muestra un mensaje general', async () => {
  stubFetch([item(1)], (_input, options) =>
    options?.method === 'PATCH' ? { ok: false, status: 500, json: async () => ({}) } : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Anular' }))
  expect(await within(fila).findByText('No se pudo cambiar el estado.')).toBeDefined()
})

test('sin permiso de edición solo lista', async () => {
  stubFetch([item(1, { estado: 'enviado', numero_factura: '' })])
  render(
    <PuedeEditarContext.Provider value={false}>
      <ItemsPage />
    </PuedeEditarContext.Provider>,
  )
  await screen.findByText('Ítem 1')
  expect(screen.queryByRole('button', { name: 'Nuevo ítem' })).toBeNull()
  expect(screen.queryByRole('columnheader', { name: 'Acciones' })).toBeNull()
})

test('si fallan las referencias lo avisa', async () => {
  stubFetch([item(1)], (input) =>
    input.includes('/facturacion/catalogos/')
      ? { ok: false, status: 500, json: async () => ({}) }
      : undefined,
  )
  render(<ItemsPage />)
  expect(
    await screen.findByText('No se pudieron cargar clientes, marcas o campañas.'),
  ).toBeDefined()
})
