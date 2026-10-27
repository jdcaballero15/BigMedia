import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import ItemForm from './ItemForm'
import type { ItemInput } from './ItemForm'
import type { Campania } from '../campanias/types'
import type { Cliente, Marca } from '../clientes/types'
import { ApiError } from '../../shared/api'
import { mesActual } from './types'
import type { ItemFacturacion } from './types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const cliente = (id: number, cuit: string): Cliente => ({
  id,
  nombre: `Cliente ${id}`,
  razon_social: '',
  cuit,
  tipo: '',
  tipo_nombre: '',
  nombre_visible: `Cliente ${id}`,
  telefono: '',
  correo: '',
  activo: true,
})
const clientes = [cliente(1, '20123456786'), cliente(2, '30500010912')]
const marcas: Marca[] = [
  {
    id: 7,
    nombre: 'Marca Siete',
    cliente: 2,
    cliente_nombre: 'Cliente 2',
    rubro: null,
    rubro_nombre: null,
    activo: true,
  },
]
const campanias: Campania[] = [
  {
    id: 5,
    nombre: 'Verano',
    marca: 7,
    marca_nombre: 'Marca Siete',
    cliente_facturacion: null,
    cliente_factura: 2,
    cliente_factura_nombre: 'Cliente 2',
    fecha_inicio: null,
    fecha_fin: null,
    estado: 'confirmada',
  },
]
const catalogos = {
  sectores: [{ id: 1, nombre: 'Privado' }],
  tipos_venta: [{ id: 3, nombre: 'F' }],
}

function renderizar(item: ItemFacturacion | null = null) {
  const onSave = vi.fn(async (_input: ItemInput) => undefined)
  render(
    <ItemForm
      item={item}
      clientes={clientes}
      marcas={marcas}
      campanias={campanias}
      catalogos={catalogos}
      onSave={onSave}
      onCancel={vi.fn()}
    />,
  )
  return onSave
}

function cambiar(etiqueta: string, valor: string) {
  fireEvent.change(screen.getByLabelText(etiqueta), { target: { value: valor } })
}

async function guardar(onSave: ReturnType<typeof renderizar>): Promise<ItemInput> {
  fireEvent.click(screen.getByRole('button', { name: 'Guardar ítem' }))
  await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1))
  return onSave.mock.calls[0][0]
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('un ítem nuevo arranca en el mes actual y viaja vacío como null', async () => {
  const onSave = renderizar()
  expect((screen.getByLabelText('Mes de facturación') as HTMLInputElement).value).toBe(mesActual())
  const entrada = await guardar(onSave)
  expect(entrada.mes).toBe(`${mesActual()}-01`)
  expect(entrada.cliente).toBeNull()
  expect(entrada.neto).toBeNull()
  expect(entrada.alicuota_iva).toBe('21.00')
})

test('al elegir cliente precarga su CUIT sin pisar uno escrito', async () => {
  const onSave = renderizar()
  cambiar('Cliente que factura', '1')
  expect((screen.getByLabelText('CUIT de facturación') as HTMLInputElement).value).toBe(
    '20123456786',
  )
  cambiar('CUIT de facturación', '30500010912')
  cambiar('Cliente que factura', '2')
  const entrada = await guardar(onSave)
  expect(entrada.cliente).toBe(2)
  expect(entrada.cuit_facturacion).toBe('30500010912')
})

test('al vincular una campaña precarga cliente, CUIT, marca y soporte', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ok([{ formato_nombre: 'Gran Formato' }, { formato_nombre: 'LED' }])),
  )
  const onSave = renderizar()
  cambiar('Campaña', '5')
  await waitFor(() =>
    expect((screen.getByLabelText('Tipo de soporte') as HTMLInputElement).value).toBe(
      'Gran Formato, LED',
    ),
  )
  const entrada = await guardar(onSave)
  expect(entrada).toMatchObject({
    campania: 5,
    cliente: 2,
    cuit_facturacion: '30500010912',
    marca: 7,
    tipo_soporte: 'Gran Formato, LED',
  })
})

test('la campaña no pisa lo ya cargado y tolera que fallen las líneas', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) })),
  )
  const onSave = renderizar()
  cambiar('Cliente que factura', '1')
  cambiar('Tipo de soporte', 'Medianera')
  cambiar('Campaña', '5')
  const entrada = await guardar(onSave)
  expect(entrada).toMatchObject({ cliente: 1, tipo_soporte: 'Medianera', marca: 7 })
})

test('cambiar cantidad o precio vacía el neto para que lo calcule el servidor', async () => {
  const existente = {
    id: 3,
    mes: '2026-11-01',
    cantidad: '10.00',
    precio_unitario: '1000.00',
    neto: '10000.00',
    alicuota_iva: '21.00',
  } as ItemFacturacion
  const onSave = renderizar(existente)
  expect((screen.getByLabelText('Importe neto') as HTMLInputElement).value).toBe('10000.00')
  cambiar('Cantidad', '3')
  expect((screen.getByLabelText('Importe neto') as HTMLInputElement).value).toBe('')
  const entrada = await guardar(onSave)
  expect(entrada).toMatchObject({ mes: '2026-11-01', cantidad: '3', neto: null })
})

test('un neto escrito a mano se respeta aunque cambie el precio', async () => {
  const onSave = renderizar()
  cambiar('Cantidad', '10')
  cambiar('Importe neto', '9500')
  cambiar('Precio unitario', '1000')
  const entrada = await guardar(onSave)
  expect(entrada).toMatchObject({ cantidad: '10', precio_unitario: '1000', neto: '9500' })
})

test('manda catálogos, servicio y período elegidos', async () => {
  const onSave = renderizar()
  cambiar('Gob/Priv', '1')
  cambiar('Tipo de venta', '3')
  cambiar('Tipo de servicio', 'impresion_colocacion')
  cambiar('Marca', '7')
  cambiar('Período desde', '01/11/2026')
  cambiar('Período hasta', '30/11/2026')
  cambiar('Notas para Administración', 'Facturar con la OC anterior')
  const entrada = await guardar(onSave)
  expect(entrada).toMatchObject({
    sector: 1,
    tipo_venta: 3,
    tipo_servicio: 'impresion_colocacion',
    marca: 7,
    periodo_desde: '2026-11-01',
    periodo_hasta: '2026-11-30',
    notas: 'Facturar con la OC anterior',
  })
})

test('una fecha de período inválida no se envía', () => {
  const onSave = renderizar()
  cambiar('Período desde', '45/11/2026')
  fireEvent.click(screen.getByRole('button', { name: 'Guardar ítem' }))
  expect(onSave).not.toHaveBeenCalled()
})

test('conserva un sector inactivo ya elegido', () => {
  renderizar({ id: 4, mes: null, sector: 9, sector_nombre: 'Mixto' } as ItemFacturacion)
  expect(screen.getByRole('option', { name: 'Mixto (inactivo)' })).toBeDefined()
  expect((screen.getByLabelText('Mes de facturación') as HTMLInputElement).value).toBe('')
})

test('muestra los errores del servidor', async () => {
  const onSave = vi.fn(async () => {
    throw new ApiError(400, { cuit_facturacion: ['El CUIT no es válido.'] })
  })
  render(
    <ItemForm
      item={null}
      clientes={clientes}
      marcas={marcas}
      campanias={campanias}
      catalogos={catalogos}
      onSave={onSave}
      onCancel={vi.fn()}
    />,
  )
  fireEvent.click(screen.getByRole('button', { name: 'Guardar ítem' }))
  expect(await screen.findByText('El CUIT no es válido.')).toBeDefined()
})

// --- HU-062: orden de compra ---

test('manda el número y la fecha de la orden de compra', async () => {
  const onSave = renderizar()
  cambiar('Número de orden de compra', 'OC-123')
  cambiar('Fecha de aprobación de la OC', '20/10/2026')
  const entrada = await guardar(onSave)
  expect(entrada).toMatchObject({
    orden_compra_numero: 'OC-123',
    orden_compra_fecha: '2026-10-20',
  })
})

test('sin fecha de OC viaja null y una fecha inválida no se envía', async () => {
  const onSave = renderizar()
  cambiar('Fecha de aprobación de la OC', '99/99/2026')
  fireEvent.click(screen.getByRole('button', { name: 'Guardar ítem' }))
  expect(onSave).not.toHaveBeenCalled()
  cambiar('Fecha de aprobación de la OC', '')
  const entrada = await guardar(onSave)
  expect(entrada.orden_compra_fecha).toBeNull()
})

test('un ítem nuevo pide guardarlo antes de adjuntar el PDF', () => {
  renderizar()
  expect(
    screen.getByText('Guardá el ítem para adjuntar el PDF de la orden de compra.'),
  ).toBeDefined()
  expect(screen.queryByLabelText('PDF de la orden de compra')).toBeNull()
})

test('un ítem guardado muestra su OC y permite adjuntar el PDF', () => {
  renderizar({
    id: 8,
    mes: '2026-11-01',
    orden_compra_numero: 'OC-5',
    orden_compra_fecha: '2026-10-20',
    orden_compra_pdf: { nombre: 'oc.pdf', tamanio: 10 },
  } as ItemFacturacion)
  expect((screen.getByLabelText('Número de orden de compra') as HTMLInputElement).value).toBe(
    'OC-5',
  )
  expect((screen.getByLabelText('Fecha de aprobación de la OC') as HTMLInputElement).value).toBe(
    '20/10/2026',
  )
  expect(screen.getByRole('link', { name: 'Abrir oc.pdf' })).toBeDefined()
})

// --- HU-063: costos del ítem ---

test('un ítem nuevo pide guardarlo antes de cargar costos', () => {
  renderizar()
  expect(screen.getByText('Guardá el ítem para cargar sus costos.')).toBeDefined()
})

test('un ítem guardado muestra sus costos y avisa cuando cambian', async () => {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    if (options?.method === 'POST') return { ok: true, status: 201, json: async () => ({}) }
    return ok(input.includes('/costos/') ? [] : [{ id: 4, nombre: 'Imprenta Cuyo' }])
  })
  vi.stubGlobal('fetch', fetchMock)
  const onCostosCambiados = vi.fn()
  render(
    <ItemForm
      item={{ id: 4, mes: '2026-11-01', campania: null } as ItemFacturacion}
      clientes={clientes}
      marcas={marcas}
      campanias={campanias}
      catalogos={catalogos}
      onSave={vi.fn()}
      onCancel={vi.fn()}
      onCostosCambiados={onCostosCambiados}
    />,
  )
  await screen.findByText('El ítem no tiene costos.')
  fireEvent.change(screen.getByLabelText('Monto fijo'), { target: { value: '100' } })
  fireEvent.click(screen.getByRole('button', { name: 'Agregar costo' }))
  await waitFor(() => expect(onCostosCambiados).toHaveBeenCalledTimes(1))
  expect(fetchMock.mock.calls.some(([url]) => url === '/api/facturacion/items/4/costos/')).toBe(
    true,
  )
})
