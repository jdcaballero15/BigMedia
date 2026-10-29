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
    costo_total: '0.00',
    neto_final: '10000.00',
    tipo_servicio: 'alquiler',
    tipo_soporte: '',
    sector: null,
    sector_nombre: null,
    tipo_venta: null,
    tipo_venta_nombre: null,
    notas: '',
    estado: 'borrador',
    numero_factura: '',
    reabierto_en: null,
    reabierto_por_nombre: null,
    motivo_reapertura: '',
    reenviado: false,
    anulado_en: null,
    anulado_por_nombre: null,
    motivo_anulacion: '',
    orden_compra_numero: '',
    orden_compra_fecha: null,
    orden_compra_pdf: null,
    grupo: null,
    grupo_codigo: null,
    creado_por_nombre: 'operativo',
    ...extra,
  }
}

/** Respuesta de alta o edición: el ítem con los avisos de OC duplicada (HU-062). */
function guardado(base: ItemFacturacion, coincidentes: { id: number; descripcion: string }[] = []) {
  return ok({ ...base, avisos: { orden_compra: coincidentes } })
}

const totales = {
  mes: '2026-11',
  cantidad: 2,
  neto: '10000.00',
  iva: '2100.00',
  total: '12100.00',
  costos: '1500.00',
  neto_final: '8500.00',
}

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
    if (input.includes('/facturacion/envios/')) return ok([])
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

test('muestra el costo total y el neto final de cada ítem y del mes (HU-063)', async () => {
  stubFetch([item(1, { costo_total: '1500.00', neto_final: '8500.00' })])
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  expect(within(fila).getByText('$1.500,00')).toBeDefined()
  expect(within(fila).getByText('$8.500,00')).toBeDefined()
  const suma = screen.getByLabelText('Totales del mes')
  expect(within(suma).getByText('Costos').nextElementSibling?.textContent).toBe('$1.500,00')
  expect(within(suma).getByText('Neto final').nextElementSibling?.textContent).toBe('$8.500,00')
})

test('lista los ítems del mes actual con sus importes y los totales sin anulados', async () => {
  const fetchMock = stubFetch([item(1), item(2, { estado: 'anulado' })])
  render(<ItemsPage />)
  expect(await screen.findByText('Ítem 1')).toBeDefined()
  // Dos filas más el total del mes.
  expect(screen.getAllByText('$12.100,00')).toHaveLength(3)
  const suma = screen.getByLabelText('Totales del mes')
  expect(within(suma).getByText('Ítems').nextElementSibling?.textContent).toBe('2sin anulados')
  expect(within(suma).getByText('Total').parentElement?.className).toBe('cifra cifra-principal')
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
    options?.method === 'POST' ? guardado(item(9)) : undefined,
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
    options?.method === 'PATCH' ? guardado(item(1)) : undefined,
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
  expect(await within(fila).findByText('No se pudo guardar el cambio.')).toBeDefined()
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
  expect(screen.queryByRole('button', { name: /Agrupar en una factura/ })).toBeNull()
  expect(screen.queryByRole('checkbox')).toBeNull()
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

// --- HU-062: orden de compra en el listado y aviso de duplicado ---

test('muestra la orden de compra y el enlace al PDF', async () => {
  stubFetch([
    item(1, { orden_compra_numero: 'OC-77', orden_compra_pdf: { nombre: 'oc.pdf', tamanio: 9 } }),
  ])
  render(<ItemsPage />)
  const fila = (await screen.findByText(/Ítem 1/)).closest('tr') as HTMLElement
  expect(fila.textContent).toContain('OC OC-77')
  expect(within(fila).getByRole('link', { name: 'PDF' }).getAttribute('href')).toBe(
    '/api/facturacion/items/1/orden-compra-pdf/',
  )
})

test('al guardar con una OC repetida avisa con el ítem coincidente', async () => {
  stubFetch([item(1)], (_input, options) =>
    options?.method === 'PATCH'
      ? guardado(item(1, { orden_compra_numero: 'OC-9' }), [
          { id: 4, descripcion: 'Alquiler octubre' },
        ])
      : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Editar' }))
  fireEvent.click(screen.getByRole('button', { name: 'Guardar ítem' }))
  const aviso = await screen.findByRole('status', { name: 'Aviso de orden de compra' })
  expect(aviso.textContent).toContain(
    'La orden de compra OC-9 ya está cargada en: #4 (Alquiler octubre)',
  )
  fireEvent.click(within(aviso).getByRole('button', { name: 'Entendido' }))
  expect(screen.queryByRole('status', { name: 'Aviso de orden de compra' })).toBeNull()
})

// --- HU-064: agrupar y quitar del grupo ---

function posts(fetchMock: ReturnType<typeof stubFetch>) {
  return fetchMock.mock.calls
    .filter(([, options]) => options?.method === 'POST')
    .map(([url, options]) => [url, JSON.parse(String(options?.body))])
}

test('agrupa los ítems seleccionados en una factura', async () => {
  const fetchMock = stubFetch(
    [item(1), item(2), item(3, { estado: 'enviado' })],
    (input, options) =>
      options?.method === 'POST' && input.includes('/grupos/')
        ? ok({ id: 5, codigo: 'G-5', mes: '2026-11', items: [1, 2] })
        : undefined,
  )
  render(<ItemsPage />)
  await screen.findByText('Ítem 1')
  const boton = screen.getByRole('button', { name: 'Agrupar en una factura (0)' })
  expect((boton as HTMLButtonElement).disabled).toBe(true)
  expect(screen.queryByRole('checkbox', { name: 'Seleccionar ítem 3' })).toBeNull()
  fireEvent.click(screen.getByRole('checkbox', { name: 'Seleccionar ítem 1' }))
  fireEvent.click(screen.getByRole('checkbox', { name: 'Seleccionar ítem 2' }))
  fireEvent.click(screen.getByRole('checkbox', { name: 'Seleccionar ítem 2' }))
  fireEvent.click(screen.getByRole('checkbox', { name: 'Seleccionar ítem 2' }))
  fireEvent.click(screen.getByRole('button', { name: 'Agrupar en una factura (2)' }))
  await waitFor(() =>
    expect(posts(fetchMock)).toEqual([['/api/facturacion/grupos/', { items: [1, 2] }]]),
  )
  // Recarga y limpia la selección.
  expect(await screen.findByRole('button', { name: 'Agrupar en una factura (0)' })).toBeDefined()
})

test('si no se pueden agrupar muestra el motivo', async () => {
  stubFetch([item(1), item(2)], (input, options) =>
    options?.method === 'POST' && input.includes('/grupos/')
      ? rechazo({ items: ['Los ítems de un grupo tienen que ser del mismo mes.'] })
      : undefined,
  )
  render(<ItemsPage />)
  await screen.findByText('Ítem 1')
  fireEvent.click(screen.getByRole('checkbox', { name: 'Seleccionar ítem 1' }))
  fireEvent.click(screen.getByRole('checkbox', { name: 'Seleccionar ítem 2' }))
  fireEvent.click(screen.getByRole('button', { name: 'Agrupar en una factura (2)' }))
  expect((await screen.findByRole('alert')).textContent).toBe(
    'Los ítems de un grupo tienen que ser del mismo mes.',
  )
})

test('un error sin motivo al agrupar muestra un mensaje general', async () => {
  stubFetch([item(1), item(2)], (input, options) =>
    options?.method === 'POST' && input.includes('/grupos/')
      ? { ok: false, status: 500, json: async () => ({}) }
      : undefined,
  )
  render(<ItemsPage />)
  await screen.findByText('Ítem 1')
  fireEvent.click(screen.getByRole('checkbox', { name: 'Seleccionar ítem 1' }))
  fireEvent.click(screen.getByRole('checkbox', { name: 'Seleccionar ítem 2' }))
  fireEvent.click(screen.getByRole('button', { name: 'Agrupar en una factura (2)' }))
  expect((await screen.findByRole('alert')).textContent).toBe('No se pudieron agrupar los ítems.')
})

test('muestra el grupo y lo quita de un ítem en Borrador', async () => {
  const fetchMock = stubFetch(
    [
      item(1, { grupo: 5, grupo_codigo: 'G-5' }),
      item(2, { grupo: 5, grupo_codigo: 'G-5', estado: 'enviado' }),
    ],
    (input, options) =>
      options?.method === 'POST' && input.includes('/quitar-del-grupo/') ? ok(item(1)) : undefined,
  )
  render(<ItemsPage />)
  const enviado = (await screen.findByText('Ítem 2')).closest('tr') as HTMLElement
  expect(enviado.textContent).toContain('G-5')
  expect(within(enviado).queryByRole('button', { name: 'Quitar del grupo' })).toBeNull()
  const fila = screen.getByText('Ítem 1').closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Quitar del grupo' }))
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          url === '/api/facturacion/items/1/quitar-del-grupo/' && options?.method === 'POST',
      ),
    ).toBe(true),
  )
})

test('muestra el error al quitar del grupo', async () => {
  stubFetch([item(1, { grupo: 5, grupo_codigo: 'G-5' })], (input, options) =>
    options?.method === 'POST' && input.includes('/quitar-del-grupo/')
      ? rechazo({ grupo: ['El ítem no está en un grupo de factura.'] })
      : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Quitar del grupo' }))
  expect(await within(fila).findByText('El ítem no está en un grupo de factura.')).toBeDefined()
})

// --- HU-067: reabrir un ítem enviado ---

test('reabre un ítem enviado con motivo', async () => {
  const fetchMock = stubFetch([item(1, { estado: 'enviado' })], (_input, options) =>
    options?.method === 'POST' ? ok(item(1)) : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  expect(within(fila).queryByRole('button', { name: 'Editar' })).toBeNull()
  fireEvent.click(within(fila).getByRole('button', { name: 'Reabrir' }))
  fireEvent.change(within(fila).getByLabelText('Motivo de la reapertura'), {
    target: { value: 'Cambió el neto' },
  })
  fireEvent.click(within(fila).getByRole('button', { name: 'Confirmar reapertura' }))
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          url === '/api/facturacion/items/1/reabrir/' &&
          JSON.parse(String(options?.body)).motivo === 'Cambió el neto',
      ),
    ).toBe(true),
  )
})

test('una reapertura rechazada muestra el motivo del servidor', async () => {
  stubFetch([item(1, { estado: 'enviado' })], (_input, options) =>
    options?.method === 'POST'
      ? rechazo({ motivo: ['Indicá el motivo de la reapertura.'] })
      : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Reabrir' }))
  fireEvent.click(within(fila).getByRole('button', { name: 'Confirmar reapertura' }))
  expect(await within(fila).findByText('Indicá el motivo de la reapertura.')).toBeDefined()
})

test('marca los reenviados y los reabiertos con su motivo', async () => {
  stubFetch([
    item(1, { estado: 'enviado', reenviado: true }),
    item(2, { reabierto_en: '2026-11-03T10:00:00Z', motivo_reapertura: 'Cambió el neto' }),
  ])
  render(<ItemsPage />)
  const reenviado = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  expect(reenviado.textContent).toContain('Reenviado')
  const reabierto = screen.getByText('Ítem 2').closest('tr') as HTMLElement
  expect(reabierto.textContent).toContain('Reabierto: Cambió el neto')
})

// --- RN-026: anular un ítem facturado ---

test('anula un ítem facturado con motivo y no le ofrece reabrir (RN-026)', async () => {
  const fetchMock = stubFetch(
    [item(1, { estado: 'facturado', numero_factura: 'A-1' })],
    (_input, options) => (options?.method === 'POST' ? ok(item(1)) : undefined),
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  expect(within(fila).queryByRole('button', { name: 'Reabrir' })).toBeNull()
  fireEvent.click(within(fila).getByRole('button', { name: 'Anular' }))
  fireEvent.change(within(fila).getByLabelText('Motivo de la anulación'), {
    target: { value: 'Nota de crédito NC-7' },
  })
  fireEvent.click(within(fila).getByRole('button', { name: 'Confirmar anulación' }))
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          url === '/api/facturacion/items/1/anular-facturado/' &&
          JSON.parse(String(options?.body)).motivo === 'Nota de crédito NC-7',
      ),
    ).toBe(true),
  )
})

test('una anulación rechazada muestra el motivo del servidor (RN-026)', async () => {
  stubFetch([item(1, { estado: 'facturado', numero_factura: 'A-1' })], (_input, options) =>
    options?.method === 'POST'
      ? rechazo({ motivo: ['Indicá el motivo de la anulación.'] })
      : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Anular' }))
  fireEvent.click(within(fila).getByRole('button', { name: 'Confirmar anulación' }))
  expect(await within(fila).findByText('Indicá el motivo de la anulación.')).toBeDefined()
})

test('un facturado anulado muestra su motivo (RN-026)', async () => {
  stubFetch([
    item(1, {
      estado: 'anulado',
      numero_factura: 'A-1',
      anulado_en: '2026-11-20T10:00:00Z',
      motivo_anulacion: 'Nota de crédito NC-7',
    }),
  ])
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  expect(fila.textContent).toContain('A-1')
  expect(fila.textContent).toContain('Anulado: Nota de crédito NC-7')
})
