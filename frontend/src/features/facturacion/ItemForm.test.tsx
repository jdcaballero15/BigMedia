import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import ItemForm from './ItemForm'
import type { ItemInput } from './ItemForm'
import type { Cliente } from '../clientes/types'
import { ApiError } from '../../shared/api'
import type { CostoElegible, ItemFacturacion } from './types'

const cliente = (id: number, razonSocial: string): Cliente => ({
  id,
  nombre: `Cliente ${id}`,
  razon_social: razonSocial,
  cuit: '',
  tipo: '',
  tipo_nombre: '',
  nombre_visible: `Cliente ${id}`,
  telefono: '',
  correo: '',
  activo: true,
})
const clientes = [cliente(1, 'Uno SA'), cliente(2, '')]
const catalogos = {
  sectores: [{ id: 1, nombre: 'Privado' }],
  tipos_venta: [{ id: 3, nombre: 'F' }],
}

const costo = (id: number, tipo: string, monto: string, extra: Partial<CostoElegible> = {}) =>
  ({
    id,
    tipo: 'impresion',
    tipo_nombre: tipo,
    monto,
    fecha: '2026-11-01',
    anulado: false,
    a_quien: 'Imprenta Andes',
    campania_nombre: 'Verano',
    cartel_nombre: 'San Martín 100',
    propio: false,
    ...extra,
  }) as CostoElegible

let elegibles: CostoElegible[] = []

beforeEach(() => {
  elegibles = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, status: 200, json: async () => elegibles })),
  )
})

function renderizar(
  item: ItemFacturacion | null = null,
  onSave = vi.fn(async (_input: ItemInput, _pdf: File | null) => undefined),
) {
  render(
    <ItemForm
      item={item}
      mes="2026-12"
      clientes={clientes}
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

test('el formulario tiene los siete datos de la planilla y las dos secciones (HU-060)', () => {
  renderizar()
  const form = screen.getByRole('form', { name: 'Formulario de ítem a facturar' })
  const grilla = form.querySelector('.form-grid') as HTMLElement
  const etiquetas = Array.from(grilla.querySelectorAll('label')).map((label) =>
    label.firstChild?.textContent?.trim(),
  )
  const secciones = Array.from(form.querySelectorAll('legend')).map((l) => l.textContent)
  expect(secciones).toEqual(['Orden de publicidad', 'Costos del ítem'])
  expect(etiquetas).toEqual([
    'Cliente (razón social)',
    'Importe neto total',
    'Costos incluidos',
    'Detalle costo',
    'Tipo de venta',
    'Gob/Priv',
    'Tipo',
  ])
})

test('el cliente se elige por su razón social, o por su nombre si no la tiene', () => {
  renderizar()
  expect(screen.getByRole('option', { name: 'Uno SA' })).toBeDefined()
  expect(screen.getByRole('option', { name: 'Cliente 2' })).toBeDefined()
})

test('un ítem nuevo viaja con el mes elegido en la lista y lo vacío como null', async () => {
  const entrada = await guardar(renderizar())
  expect(entrada).toEqual({
    mes: '2026-12-01',
    cliente: null,
    neto: null,
    costos_incluidos: null,
    detalle_costo: '',
    tipo_venta: null,
    sector: null,
    tipo_soporte: '',
    costos: [],
  })
})

test('manda los siete datos cargados', async () => {
  const onSave = renderizar()
  cambiar('Cliente (razón social)', '1')
  cambiar('Importe neto total', '10000')
  cambiar('Costos incluidos', '1500')
  cambiar('Detalle costo', 'Comisión agencia')
  cambiar('Tipo de venta', '3')
  cambiar('Gob/Priv', '1')
  cambiar('Tipo', 'Séxtuples')
  expect(await guardar(onSave)).toEqual({
    mes: '2026-12-01',
    cliente: 1,
    neto: '10000',
    costos_incluidos: '1500',
    detalle_costo: 'Comisión agencia',
    tipo_venta: 3,
    sector: 1,
    tipo_soporte: 'Séxtuples',
    costos: [],
  })
})

test('al editar precarga los datos y no cambia el mes del ítem', async () => {
  const onSave = renderizar({
    id: 3,
    mes: '2026-11-01',
    cliente: 1,
    neto: '10000.00',
    costos_incluidos: '1500.00',
    detalle_costo: 'Comisión agencia',
    tipo_venta: 3,
    sector: 1,
    tipo_soporte: 'Séxtuples',
  } as ItemFacturacion)
  expect(screen.getByRole('heading', { name: 'Editar ítem' })).toBeDefined()
  expect((screen.getByLabelText('Costos incluidos') as HTMLInputElement).value).toBe('1500.00')
  const entrada = await guardar(onSave)
  expect(entrada.mes).toBeUndefined()
  expect(entrada).toMatchObject({ cliente: 1, neto: '10000.00', tipo_soporte: 'Séxtuples' })
})

test('conserva un sector y un tipo de venta inactivos ya elegidos', () => {
  renderizar({
    id: 4,
    sector: 9,
    sector_nombre: 'Mixto',
    tipo_venta: 8,
    tipo_venta_nombre: null,
  } as ItemFacturacion)
  expect(screen.getByRole('option', { name: 'Mixto (inactivo)' })).toBeDefined()
  expect(screen.getByRole('option', { name: '#8 (inactivo)' })).toBeDefined()
})

test('muestra los errores del servidor junto a cada dato', async () => {
  renderizar(
    null,
    vi.fn(async () => {
      throw new ApiError(400, {
        costos_incluidos: ['Asegúrese de que este valor sea mayor o igual a 0.'],
      })
    }),
  )
  fireEvent.click(screen.getByRole('button', { name: 'Guardar ítem' }))
  expect(
    await screen.findByText('Asegúrese de que este valor sea mayor o igual a 0.'),
  ).toBeDefined()
  expect(screen.getByRole('alert')).toBeDefined()
})

test('un error que no es de la API muestra un mensaje general', async () => {
  renderizar(
    null,
    vi.fn(async () => {
      throw 'falla'
    }),
  )
  fireEvent.click(screen.getByRole('button', { name: 'Guardar ítem' }))
  expect((await screen.findByRole('alert')).textContent).toBe('No se pudo guardar el ítem.')
})

// --- HU-060 criterio 11 y HU-063: costos elegidos ---

test('al elegir impresión y fijación suma los costos incluidos y arma el detalle', async () => {
  elegibles = [costo(5, 'Impresión', '50000.00'), costo(6, 'Fijación', '30000.00')]
  const onSave = renderizar()
  const disponibles = await screen.findByRole('table', { name: 'Costos para elegir' })
  fireEvent.click(within(disponibles).getAllByRole('button', { name: 'Elegir' })[0])
  fireEvent.click(screen.getByRole('button', { name: 'Elegir' }))
  const incluidos = screen.getByLabelText('Costos incluidos') as HTMLInputElement
  expect(incluidos.value).toBe('80000.00')
  expect(incluidos.readOnly).toBe(true)
  expect((screen.getByLabelText('Detalle costo') as HTMLInputElement).value).toBe(
    'Impresión + Fijación',
  )
  expect(screen.getByLabelText('Suma de los costos elegidos').textContent).toContain('80.000,00')
  const entrada = await guardar(onSave)
  expect(entrada.costos).toEqual([5, 6])
  expect(entrada).not.toHaveProperty('costos_incluidos')
  expect(entrada).not.toHaveProperty('detalle_costo')
})

test('busca costos con Enter sin mandar el formulario', async () => {
  const onSave = renderizar()
  await screen.findByText('No hay costos para elegir con esa búsqueda.')
  const buscador = screen.getByLabelText('Buscar costos')
  fireEvent.change(buscador, { target: { value: 'san martín' } })
  fireEvent.keyDown(buscador, { key: 'Enter' })
  await waitFor(() =>
    expect(fetch).toHaveBeenLastCalledWith(
      '/api/facturacion/items/costos-elegibles/?q=san%20mart%C3%ADn',
      expect.anything(),
    ),
  )
  fireEvent.keyDown(buscador, { key: 'a' })
  fireEvent.click(screen.getByRole('button', { name: 'Buscar' }))
  expect(onSave).not.toHaveBeenCalled()
})

test('si falla la búsqueda de costos lo avisa', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => {
      throw new Error('sin red')
    }),
  )
  renderizar()
  expect(await screen.findByText('No se pudieron buscar los costos.')).toBeDefined()
})

test('al quitar todos los costos vuelven los valores escritos a mano', async () => {
  const onSave = renderizar({
    id: 3,
    costos_incluidos: '80000.00',
    detalle_costo: 'Impresión',
    costos_elegidos: [costo(5, 'Impresión', '80000.00')],
  } as ItemFacturacion)
  const elegidos = screen.getByRole('table', { name: 'Costos elegidos' })
  fireEvent.click(within(elegidos).getByRole('button', { name: 'Quitar' }))
  const incluidos = screen.getByLabelText('Costos incluidos') as HTMLInputElement
  expect(incluidos.readOnly).toBe(false)
  fireEvent.change(incluidos, { target: { value: '1500' } })
  const entrada = await guardar(onSave)
  expect(entrada).toMatchObject({ costos: [], costos_incluidos: '1500' })
})

test('un costo anulado no suma y uno propio no se quita', () => {
  renderizar({
    id: 3,
    costos_elegidos: [
      costo(5, 'Comisión', '1500.00', { propio: true, campania_nombre: null, a_quien: '' }),
      costo(6, 'Fijación', '999.00', { anulado: true }),
    ],
  } as ItemFacturacion)
  const elegidos = screen.getByRole('table', { name: 'Costos elegidos' })
  expect(within(elegidos).getByText('Propio del ítem')).toBeDefined()
  expect(within(elegidos).getByText('Se anula desde Costos')).toBeDefined()
  expect(within(elegidos).getByText('(anulado)')).toBeDefined()
  expect((screen.getByLabelText('Costos incluidos') as HTMLInputElement).value).toBe('1500.00')
  expect((screen.getByLabelText('Detalle costo') as HTMLInputElement).value).toBe('Comisión')
})

test('la orden de publicidad adjunta viaja al guardar y se puede descartar', async () => {
  const onSave = renderizar()
  const pdf = new File(['%PDF-1.4'], 'op.pdf', { type: 'application/pdf' })
  fireEvent.change(screen.getByLabelText('Adjuntar PDF'), { target: { files: [pdf] } })
  expect(screen.getByText('op.pdf')).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'No adjuntar' }))
  expect(screen.queryByText('op.pdf')).toBeNull()
  fireEvent.change(screen.getByLabelText('Adjuntar PDF'), { target: { files: [pdf] } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar ítem' }))
  await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1))
  expect(onSave.mock.calls[0][1]).toBe(pdf)
})

test('un ítem con orden de publicidad la abre y ofrece reemplazarla', () => {
  renderizar({ id: 3, orden_compra_pdf: { nombre: 'op-vieja.pdf', tamanio: 9 } } as ItemFacturacion)
  const enlace = screen.getByRole('link', { name: 'Abrir op-vieja.pdf' })
  expect(enlace.getAttribute('href')).toBe('/api/facturacion/items/3/orden-compra-pdf/')
  expect(screen.getByLabelText('Reemplazar PDF')).toBeDefined()
})

test('un PDF rechazado muestra el error y conserva lo cargado', async () => {
  renderizar(
    null,
    vi.fn(async () => {
      throw new ApiError(400, { orden_publicidad: ['El archivo tiene que ser un PDF.'] })
    }),
  )
  cambiar('Importe neto total', '10000')
  const pdf = new File(['x'], 'op.txt')
  fireEvent.change(screen.getByLabelText('Adjuntar PDF'), { target: { files: [pdf] } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar ítem' }))
  expect(await screen.findByText('El archivo tiene que ser un PDF.')).toBeDefined()
  expect((screen.getByLabelText('Importe neto total') as HTMLInputElement).value).toBe('10000')
  expect(screen.getByText('op.txt')).toBeDefined()
})

test('el botón de guardar queda en la barra fija de abajo del formulario', () => {
  renderizar()
  const guardar = screen.getByRole('button', { name: 'Guardar ítem' })
  expect(guardar.parentElement?.classList.contains('acciones-fijas')).toBe(true)
})
