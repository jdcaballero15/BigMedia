import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import CostosDelItem from './CostosDelItem'
import type { CostoDelItem } from './types'

const URL = '/api/facturacion/items/8/costos/'
const ok = (data: unknown, status = 200) => ({ ok: true, status, json: async () => data })
const rechazo = (data: unknown) => ({ ok: false, status: 400, json: async () => data })

function costo(id: number, extra: Partial<CostoDelItem> = {}): CostoDelItem {
  return {
    id,
    tipo: 'comision',
    tipo_nombre: 'Comisión',
    proveedor: null,
    proveedor_nombre: null,
    destinatario: 'Agencia Sur',
    porcentaje: '15.00',
    monto: '1500.00',
    fecha: '2026-11-01',
    reserva: null,
    cartel_nombre: null,
    anulado: false,
    motivo_anulacion: '',
    ...extra,
  }
}

const proveedores = [{ id: 4, nombre: 'Imprenta Cuyo', servicio: '', activo: true }]

function stubFetch(
  costos: CostoDelItem[],
  vinculables: CostoDelItem[] = [],
  overrides?: (input: string, options?: RequestInit) => unknown,
) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const custom = overrides?.(input, options)
    if (custom) return custom
    if (input.includes('/inventario/proveedores/')) return ok(proveedores)
    if (input.endsWith('vinculables/')) return ok(vinculables)
    if (input === URL) return ok(costos)
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function posts(fetchMock: ReturnType<typeof stubFetch>) {
  return fetchMock.mock.calls
    .filter(([, options]) => options?.method === 'POST')
    .map(([url, options]) => [url, JSON.parse(String(options?.body))])
}

function cambiar(etiqueta: string, valor: string) {
  fireEvent.change(screen.getByLabelText(etiqueta), { target: { value: valor } })
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('sin guardar el ítem pide guardarlo primero', () => {
  render(<CostosDelItem itemId={null} campania={null} onCambio={vi.fn()} />)
  expect(screen.getByText('Guardá el ítem para cargar sus costos.')).toBeDefined()
})

test('lista los costos con a quién se le paga, el porcentaje y el costo total sin anulados', async () => {
  stubFetch([
    costo(1),
    costo(2, {
      tipo: 'impresion',
      tipo_nombre: 'Impresión',
      proveedor: 4,
      proveedor_nombre: 'Imprenta Cuyo',
      destinatario: '',
      porcentaje: null,
      monto: '200.00',
      reserva: 30,
      cartel_nombre: 'LED Centro',
    }),
    costo(3, { monto: '999.00', anulado: true, motivo_anulacion: 'Duplicado' }),
  ])
  render(<CostosDelItem itemId={8} campania={null} onCambio={vi.fn()} />)
  const tabla = await screen.findByRole('table', { name: 'Costos del ítem' })
  const filas = within(tabla).getAllByRole('row')
  expect(filas[1].textContent).toContain('Agencia Sur')
  expect(filas[1].textContent).toContain('15.00 %')
  expect(filas[2].textContent).toContain('Imprenta Cuyo')
  expect(filas[2].textContent).toContain('Reserva · LED Centro')
  expect(filas[3].textContent).toContain('Anulado: Duplicado')
  expect(screen.getByLabelText('Costo total del ítem').textContent).toContain('$1.700,00')
})

test('carga un costo en porcentaje del neto y avisa el cambio', async () => {
  const fetchMock = stubFetch([], [], (_input, options) =>
    options?.method === 'POST' ? ok(costo(9), 201) : undefined,
  )
  const onCambio = vi.fn()
  render(<CostosDelItem itemId={8} campania={null} onCambio={onCambio} />)
  await screen.findByText('El ítem no tiene costos.')
  cambiar('Tipo de costo', 'comision')
  cambiar('Cómo se calcula', 'porcentaje')
  cambiar('Porcentaje del neto', '15')
  cambiar('A quién se le paga', ' Agencia Sur ')
  fireEvent.click(screen.getByRole('button', { name: 'Agregar costo' }))
  await waitFor(() => expect(onCambio).toHaveBeenCalledTimes(1))
  expect(posts(fetchMock)).toEqual([
    [URL, { tipo: 'comision', porcentaje: '15', proveedor: null, destinatario: 'Agencia Sur' }],
  ])
})

test('carga un costo fijo con proveedor', async () => {
  const fetchMock = stubFetch([], [], (_input, options) =>
    options?.method === 'POST' ? ok(costo(9), 201) : undefined,
  )
  render(<CostosDelItem itemId={8} campania={null} onCambio={vi.fn()} />)
  await screen.findByRole('option', { name: 'Imprenta Cuyo' })
  cambiar('Tipo de costo', 'impresion')
  cambiar('Monto fijo', '1234.56')
  cambiar('Proveedor', '4')
  fireEvent.click(screen.getByRole('button', { name: 'Agregar costo' }))
  await waitFor(() => expect(posts(fetchMock)).toHaveLength(1))
  expect(posts(fetchMock)[0][1]).toEqual({
    tipo: 'impresion',
    monto: '1234.56',
    proveedor: 4,
    destinatario: '',
  })
})

test('un alta rechazada muestra los errores del servidor', async () => {
  stubFetch([], [], (_input, options) =>
    options?.method === 'POST' ? rechazo({ monto: ['Cargá un monto fijo.'] }) : undefined,
  )
  const onCambio = vi.fn()
  render(<CostosDelItem itemId={8} campania={null} onCambio={onCambio} />)
  await screen.findByText('El ítem no tiene costos.')
  fireEvent.click(screen.getByRole('button', { name: 'Agregar costo' }))
  expect(await screen.findByText('Cargá un monto fijo.')).toBeDefined()
  expect(onCambio).not.toHaveBeenCalled()
})

test('vincula un costo de una reserva de la campaña', async () => {
  const deReserva = costo(30, {
    tipo: 'impresion',
    tipo_nombre: 'Impresión',
    porcentaje: null,
    monto: '300.00',
    reserva: 12,
    cartel_nombre: 'LED Centro',
  })
  const fetchMock = stubFetch([], [deReserva], (_input, options) =>
    options?.method === 'POST' ? ok(deReserva, 201) : undefined,
  )
  const onCambio = vi.fn()
  render(<CostosDelItem itemId={8} campania={5} onCambio={onCambio} />)
  await screen.findByRole('option', { name: 'LED Centro · Impresión · $300,00' })
  cambiar('Costo de una reserva de la campaña', '30')
  fireEvent.click(screen.getByRole('button', { name: 'Vincular' }))
  await waitFor(() => expect(onCambio).toHaveBeenCalledTimes(1))
  expect(posts(fetchMock)).toEqual([[`${URL}vincular/`, { costo: 30 }]])
})

test('sin campaña no ofrece vincular costos de reserva', async () => {
  const fetchMock = stubFetch([])
  render(<CostosDelItem itemId={8} campania={null} onCambio={vi.fn()} />)
  await screen.findByText('El ítem no tiene costos.')
  expect(screen.queryByLabelText('Costo de una reserva de la campaña')).toBeNull()
  expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith('vinculables/'))).toBe(false)
})

test('anula un costo propio con motivo; los de reserva se anulan desde Costos', async () => {
  const fetchMock = stubFetch(
    [costo(1), costo(2, { reserva: 12, cartel_nombre: 'LED Centro', porcentaje: null })],
    [],
    (_input, options) => (options?.method === 'POST' ? ok(costo(1, { anulado: true })) : undefined),
  )
  const onCambio = vi.fn()
  render(<CostosDelItem itemId={8} campania={null} onCambio={onCambio} />)
  const tabla = await screen.findByRole('table', { name: 'Costos del ítem' })
  expect(within(tabla).getAllByRole('button', { name: 'Anular' })).toHaveLength(1)
  expect(tabla.textContent).toContain('Se anula desde Costos')
  fireEvent.click(within(tabla).getByRole('button', { name: 'Anular' }))
  cambiar('Motivo de la anulación', 'Carga duplicada')
  fireEvent.click(screen.getByRole('button', { name: 'Confirmar anulación' }))
  await waitFor(() => expect(onCambio).toHaveBeenCalledTimes(1))
  expect(posts(fetchMock)).toEqual([[`${URL}1/anular/`, { motivo: 'Carga duplicada' }]])
})

test('una anulación rechazada muestra el motivo y se puede cancelar', async () => {
  stubFetch([costo(1)], [], (_input, options) =>
    options?.method === 'POST' ? rechazo({ motivo: ['Indicá el motivo.'] }) : undefined,
  )
  render(<CostosDelItem itemId={8} campania={null} onCambio={vi.fn()} />)
  fireEvent.click(await screen.findByRole('button', { name: 'Anular' }))
  fireEvent.click(screen.getByRole('button', { name: 'Confirmar anulación' }))
  expect(await screen.findByText('Indicá el motivo.')).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar anulación' }))
  expect(screen.queryByLabelText('Motivo de la anulación')).toBeNull()
})

test('si no se pueden cargar los costos lo avisa', async () => {
  stubFetch([], [], (input) =>
    input === URL ? { ok: false, status: 500, json: async () => ({}) } : undefined,
  )
  render(<CostosDelItem itemId={8} campania={null} onCambio={vi.fn()} />)
  expect(await screen.findByText('No se pudieron cargar los costos del ítem.')).toBeDefined()
})
