import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import ItemsPage from './ItemsPage'
import { PuedeEditarContext } from '../../shared/sesion'
import { abrirAcciones } from '../../shared/pruebas'
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
    cliente_razon_social: 'Cliente Uno SA',
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
    tipo_soporte: `Ítem ${id}`,
    sector: null,
    sector_nombre: null,
    tipo_venta: null,
    tipo_venta_nombre: null,
    costos_incluidos: null,
    detalle_costo: '',
    costos_calculados: false,
    costos_elegidos: [],
    notas: '',
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
    if (input.includes('/items/costos-elegibles/')) return ok([])
    if (input.includes('/facturacion/items/')) return ok(items)
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function posts(fetchMock: ReturnType<typeof stubFetch>) {
  return fetchMock.mock.calls
    .filter(([, options]) => options?.method === 'POST')
    .map(([url, options]) => [url, options?.body ? JSON.parse(String(options.body)) : undefined])
}

function patches(fetchMock: ReturnType<typeof stubFetch>) {
  return fetchMock.mock.calls
    .filter(([, options]) => options?.method === 'PATCH')
    .map(([url, options]) => [url, JSON.parse(String(options?.body))])
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

/** Abre el menú ⋯ de la fila y elige una acción. */
function elegir(fila: HTMLElement, accion: string) {
  abrirAcciones(fila)
  fireEvent.click(within(fila).getByRole('button', { name: accion }))
}

/** Las acciones que ofrece el menú ⋯ de la fila (lo abre y lo vuelve a cerrar). */
function acciones(fila: HTMLElement): string[] {
  abrirAcciones(fila)
  const lista = fila.querySelector('.menu-fila-lista')
  const etiquetas = Array.from(lista?.querySelectorAll('button') ?? []).map((b) => b.textContent)
  abrirAcciones(fila)
  return etiquetas.filter((etiqueta): etiqueta is string => etiqueta !== null)
}

test('cada fila muestra las siete columnas de la planilla (HU-060, RN-024)', async () => {
  stubFetch([
    item(1, {
      costos_incluidos: '1500.00',
      detalle_costo: 'Comisión agencia',
      tipo_venta_nombre: 'F',
      sector_nombre: 'Privado',
    }),
  ])
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  const celdas = Array.from(fila.querySelectorAll('td')).map((celda) => celda.textContent)
  expect(celdas.slice(1, 8)).toEqual([
    'Cliente Uno SA',
    '$10.000,00',
    '$1.500,00',
    'Comisión agencia',
    'F',
    'Privado',
    'Ítem 1',
  ])
  const titulos = screen.getAllByRole('columnheader').map((titulo) => titulo.textContent)
  expect(titulos.filter(Boolean)).toEqual([
    'Cliente (razón social)',
    'Importe neto total',
    'Costos incluidos',
    'Detalle costo',
    'Tipo de venta',
    'Gob/Priv',
    'Tipo',
  ])
  expect(screen.queryByRole('columnheader', { name: 'Estado' })).toBeNull()
})

test('una fila sin datos muestra guiones y «Sin cliente»', async () => {
  stubFetch([item(1, { cliente: null, cliente_razon_social: null, neto: null, tipo_soporte: '' })])
  render(<ItemsPage />)
  const fila = (await screen.findByText('Sin cliente')).closest('tr') as HTMLElement
  const celdas = Array.from(fila.querySelectorAll('td')).map((celda) => celda.textContent)
  expect(celdas.slice(2, 8)).toEqual(['—', '—', '—', '—', '—', '—'])
})

test('los totales del mes siguen con los costos del módulo (HU-063)', async () => {
  stubFetch([item(1)])
  render(<ItemsPage />)
  await screen.findByText('Ítem 1')
  const suma = screen.getByLabelText('Totales del mes')
  expect(within(suma).getByText('Costos').nextElementSibling?.textContent).toBe('$1.500,00')
  expect(within(suma).getByText('Neto final').nextElementSibling?.textContent).toBe('$8.500,00')
})

test('lista los ítems del mes actual con sus importes y los totales', async () => {
  const fetchMock = stubFetch([item(1), item(2)])
  render(<ItemsPage />)
  expect(await screen.findByText('Ítem 1')).toBeDefined()
  // Dos filas más el neto del mes.
  expect(screen.getAllByText('$10.000,00')).toHaveLength(3)
  const suma = screen.getByLabelText('Totales del mes')
  expect(within(suma).getByText('Ítems').nextElementSibling?.textContent).toBe('2')
  expect(within(suma).getByText('Total').parentElement?.className).toBe('cifra cifra-principal')
  const mes = mesActual()
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes(`items/?mes=${mes}`))).toBe(true)
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes(`totales/?mes=${mes}`))).toBe(
    true,
  )
})

test('filtra por mes y no ofrece filtro de estado', async () => {
  const fetchMock = stubFetch([item(1)])
  render(<ItemsPage />)
  await screen.findByText('Ítem 1')
  expect(screen.queryByLabelText('Estado')).toBeNull()
  fireEvent.change(screen.getByLabelText('Mes'), { target: { value: '2026-12' } })
  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith('items/?mes=2026-12'))).toBe(
      true,
    ),
  )
})

test('no hay recuadro de envíos ni «Enviar a facturar»', async () => {
  const fetchMock = stubFetch([item(1)])
  render(<ItemsPage />)
  await screen.findByText('Ítem 1')
  expect(screen.queryByRole('region', { name: 'Envíos a facturar' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Enviar a facturar' })).toBeNull()
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/envios/'))).toBe(false)
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
  fireEvent.change(within(form).getByLabelText('Importe neto total'), { target: { value: '500' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar ítem' }))
  await waitFor(() =>
    expect(screen.queryByRole('form', { name: 'Formulario de ítem a facturar' })).toBeNull(),
  )
  const [, options] = fetchMock.mock.calls.find(([, o]) => o?.method === 'POST') ?? []
  expect(JSON.parse(String(options?.body)).neto).toBe('500')
})

test('cada ítem ofrece Editar y Dar de baja', async () => {
  stubFetch([item(1)])
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  expect(acciones(fila)).toEqual(['Editar', 'Dar de baja'])
  elegir(fila, 'Editar')
  expect(screen.getByRole('heading', { name: 'Editar ítem' })).toBeDefined()
})

test('guarda la edición de un ítem', async () => {
  const fetchMock = stubFetch([item(1)], (_input, options) =>
    options?.method === 'PATCH' ? guardado(item(1)) : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  elegir(fila, 'Editar')
  const form = screen.getByRole('form', { name: 'Formulario de ítem a facturar' })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar ítem' }))
  await waitFor(() => expect(patches(fetchMock)).toHaveLength(1))
  expect(patches(fetchMock)[0][0]).toBe('/api/facturacion/items/1/')
})

test('da de baja un ítem y recarga la lista', async () => {
  const fetchMock = stubFetch([item(1)], (input, options) =>
    options?.method === 'POST' && input.includes('/dar-de-baja/') ? ok({ id: 1 }) : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  const cargas = () =>
    fetchMock.mock.calls.filter(([url]) => String(url).includes('items/?mes=')).length
  expect(cargas()).toBe(1)
  elegir(fila, 'Dar de baja')
  await waitFor(() =>
    expect(posts(fetchMock)).toEqual([['/api/facturacion/items/1/dar-de-baja/', {}]]),
  )
  await waitFor(() => expect(cargas()).toBe(2))
})

test('un error al dar de baja muestra el motivo del servidor', async () => {
  stubFetch([item(1)], (_input, options) =>
    options?.method === 'POST'
      ? rechazo({ estado: ['No se puede dar de baja este ítem.'] })
      : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  elegir(fila, 'Dar de baja')
  expect(await within(fila).findByText('No se puede dar de baja este ítem.')).toBeDefined()
})

test('un error sin campos muestra un mensaje general', async () => {
  stubFetch([item(1)], (_input, options) =>
    options?.method === 'POST' ? { ok: false, status: 500, json: async () => ({}) } : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  elegir(fila, 'Dar de baja')
  expect(await within(fila).findByText('No se pudo guardar el cambio.')).toBeDefined()
})

test('sin permiso de edición solo lista', async () => {
  stubFetch([item(1)])
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
    await screen.findByText('No se pudieron cargar los clientes o los catálogos.'),
  ).toBeDefined()
})

// --- HU-062: orden de publicidad en el listado y aviso de OC duplicada ---

test('abre la orden de publicidad desde el menú', async () => {
  const abrir = vi.spyOn(window, 'open').mockReturnValue(null)
  stubFetch([item(1, { orden_compra_pdf: { nombre: 'oc.pdf', tamanio: 9 } }), item(2)])
  render(<ItemsPage />)
  const sinPdf = (await screen.findByText('Ítem 2')).closest('tr') as HTMLElement
  expect(acciones(sinPdf)).not.toContain('Abrir orden de publicidad')
  const fila = screen.getByText('Ítem 1').closest('tr') as HTMLElement
  elegir(fila, 'Abrir orden de publicidad')
  expect(abrir).toHaveBeenCalledWith(
    '/api/facturacion/items/1/orden-compra-pdf/',
    '_blank',
    'noreferrer',
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
  elegir(fila, 'Editar')
  fireEvent.click(screen.getByRole('button', { name: 'Guardar ítem' }))
  const aviso = await screen.findByRole('status', { name: 'Aviso de orden de compra' })
  expect(aviso.textContent).toContain(
    'La orden de compra OC-9 ya está cargada en: #4 (Alquiler octubre)',
  )
  fireEvent.click(within(aviso).getByRole('button', { name: 'Entendido' }))
  expect(screen.queryByRole('status', { name: 'Aviso de orden de compra' })).toBeNull()
})

test('con orden de publicidad adjunta guarda el ítem en multipart, con los costos como JSON', async () => {
  const fetchMock = stubFetch([item(1)], (_input, options) =>
    options?.method === 'PATCH' ? guardado(item(1)) : undefined,
  )
  render(<ItemsPage />)
  const fila = (await screen.findByText('Ítem 1')).closest('tr') as HTMLElement
  elegir(fila, 'Editar')
  const pdf = new File(['%PDF-1.4'], 'op.pdf', { type: 'application/pdf' })
  fireEvent.change(screen.getByLabelText('Adjuntar PDF'), { target: { files: [pdf] } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar ítem' }))
  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([, options]) => options?.method === 'PATCH')).toBe(true),
  )
  const [url, options] = fetchMock.mock.calls.find(([, o]) => o?.method === 'PATCH') ?? []
  expect(url).toBe('/api/facturacion/items/1/')
  const cuerpo = options?.body as FormData
  expect(cuerpo).toBeInstanceOf(FormData)
  expect((cuerpo.get('orden_publicidad') as File).name).toBe('op.pdf')
  expect(cuerpo.get('costos')).toBe('[]')
  expect(cuerpo.get('cliente')).toBe('1')
  expect(cuerpo.get('costos_incluidos')).toBe('')
})

// --- HU-064: agrupar y quitar del grupo ---

test('agrupa los ítems seleccionados en una factura', async () => {
  const fetchMock = stubFetch([item(1), item(2), item(3)], (input, options) =>
    options?.method === 'POST' && input.includes('/grupos/')
      ? ok({ id: 5, codigo: 'G-5', mes: '2026-11', items: [1, 2] })
      : undefined,
  )
  render(<ItemsPage />)
  await screen.findByText('Ítem 1')
  const boton = screen.getByRole('button', { name: 'Agrupar en una factura (0)' })
  expect((boton as HTMLButtonElement).disabled).toBe(true)
  expect(screen.getAllByRole('checkbox')).toHaveLength(3)
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

test('quita del grupo solo a un ítem agrupado', async () => {
  const fetchMock = stubFetch(
    [item(1, { grupo: 5, grupo_codigo: 'G-5' }), item(2)],
    (input, options) =>
      options?.method === 'POST' && input.includes('/quitar-del-grupo/') ? ok(item(1)) : undefined,
  )
  render(<ItemsPage />)
  const suelto = (await screen.findByText('Ítem 2')).closest('tr') as HTMLElement
  expect(acciones(suelto)).not.toContain('Quitar del grupo')
  const fila = screen.getByText('Ítem 1').closest('tr') as HTMLElement
  elegir(fila, 'Quitar del grupo')
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
  elegir(fila, 'Quitar del grupo')
  expect(await within(fila).findByText('El ítem no está en un grupo de factura.')).toBeDefined()
})

// --- HU-070: descargar el Excel de la lista ---

test('«Descargar Excel» baja la lista con los filtros actuales', async () => {
  stubFetch([item(1)])
  render(<ItemsPage />)
  await screen.findByText('Ítem 1')
  const enlace = screen.getByRole('link', { name: 'Descargar Excel' })
  expect(enlace.getAttribute('href')).toBe(`/api/facturacion/items/planilla/?mes=${mesActual()}`)
  expect(enlace.hasAttribute('download')).toBe(true)
  fireEvent.change(screen.getByLabelText('Mes'), { target: { value: '2026-12' } })
  expect(enlace.getAttribute('href')).toBe('/api/facturacion/items/planilla/?mes=2026-12')
})

test('sin permiso de edición también se descarga el Excel', async () => {
  stubFetch([item(1)])
  render(
    <PuedeEditarContext.Provider value={false}>
      <ItemsPage />
    </PuedeEditarContext.Provider>,
  )
  await screen.findByText('Ítem 1')
  expect(screen.getByRole('link', { name: 'Descargar Excel' })).toBeDefined()
})

test('la pantalla se llama Facturación', async () => {
  stubFetch([])
  render(<ItemsPage />)
  expect(await screen.findByRole('heading', { name: 'Facturación' })).toBeDefined()
})
