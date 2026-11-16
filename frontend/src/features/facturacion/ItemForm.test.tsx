import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import ItemForm from './ItemForm'
import type { ItemInput } from './ItemForm'
import type { Cliente } from '../clientes/types'
import { ApiError } from '../../shared/api'
import type { ItemFacturacion } from './types'

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

function renderizar(
  item: ItemFacturacion | null = null,
  onSave = vi.fn(async (_input: ItemInput) => undefined),
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
})

test('el formulario tiene solo los siete datos de la planilla, en orden (HU-060)', () => {
  renderizar()
  const form = screen.getByRole('form', { name: 'Formulario de ítem a facturar' })
  const etiquetas = Array.from(form.querySelectorAll('label')).map((label) =>
    label.firstChild?.textContent?.trim(),
  )
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
