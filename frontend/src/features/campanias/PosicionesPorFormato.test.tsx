import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import PosicionesPorFormato from './PosicionesPorFormato'
import { PuedeEditarContext } from '../../shared/sesion'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const rechazo = (data: unknown) => ({ ok: false, status: 400, json: async () => data })

const granFormato = {
  linea: 1,
  formato: 10,
  formato_nombre: 'Gran Formato',
  solicitadas: 100,
  reservadas: 60,
  faltantes: 40,
  excedente: 0,
}
const ledSinCantidad = {
  linea: 2,
  formato: 11,
  formato_nombre: 'LED',
  solicitadas: null,
  reservadas: 3,
  faltantes: null,
  excedente: null,
}
const sextupleSinLinea = {
  linea: null,
  formato: 12,
  formato_nombre: 'Séxtuple',
  solicitadas: null,
  reservadas: 2,
  faltantes: null,
  excedente: null,
}
const formatos = [
  { id: 10, nombre: 'Gran Formato', activo: true },
  { id: 11, nombre: 'LED', activo: true },
  { id: 13, nombre: 'Medianera', activo: true },
  { id: 14, nombre: 'Banderola', activo: false },
]

function stubFetch(
  filas: unknown[] = [granFormato, ledSinCantidad, sextupleSinLinea],
  overrides?: (input: string, options?: RequestInit) => unknown,
) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const custom = overrides?.(input, options)
    if (custom) return custom
    if (input.includes('/reservas/seguimiento/')) return ok(filas)
    if (input.includes('/inventario/formatos/')) return ok(formatos)
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function llamadas(fetchMock: ReturnType<typeof stubFetch>, metodo: string) {
  return fetchMock.mock.calls
    .filter(([, options]) => options?.method === metodo)
    .map(([url, options]) => [url, JSON.parse(String(options?.body))])
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('muestra solicitadas, reservadas y faltantes por formato', async () => {
  const fetchMock = stubFetch([{ ...granFormato, reservadas: 105, faltantes: 0, excedente: 5 }])
  render(<PosicionesPorFormato campaniaId={5} />)
  const fila = (await screen.findByText('Gran Formato')).closest('tr') as HTMLElement
  const celdas = within(fila).getAllByRole('cell')
  expect(celdas.slice(1, 4).map((celda) => celda.textContent)).toEqual(['100', '105', '0 (+5)'])
  expect(
    fetchMock.mock.calls.some(([url]) => String(url).includes('/seguimiento/?campania=5')),
  ).toBe(true)
})

test('una línea sin cantidad y un formato sin línea muestran solo las reservadas', async () => {
  stubFetch()
  render(<PosicionesPorFormato campaniaId={5} />)
  const led = (await screen.findByText('LED')).closest('tr') as HTMLElement
  expect(within(led).getAllByRole('cell')[3].textContent).toBe('—')
  const sextuple = screen.getByText('Séxtuple').closest('tr') as HTMLElement
  expect(within(sextuple).getByText('(sin línea)')).toBeDefined()
  expect(within(sextuple).queryByRole('button', { name: 'Quitar' })).toBeNull()
})

test('sin filas avisa que no hay posiciones', async () => {
  stubFetch([])
  render(<PosicionesPorFormato campaniaId={5} />)
  expect(await screen.findByText('Todavía no hay posiciones solicitadas.')).toBeDefined()
})

test('si falla la carga muestra el error', async () => {
  stubFetch([], (input) =>
    input.includes('/seguimiento/')
      ? { ok: false, status: 500, json: async () => ({}) }
      : undefined,
  )
  render(<PosicionesPorFormato campaniaId={5} />)
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No se pudieron cargar las posiciones por formato.',
  )
})

test('solo ofrece formatos activos que todavía no tienen línea', async () => {
  stubFetch()
  render(<PosicionesPorFormato campaniaId={5} />)
  await screen.findByText('Gran Formato')
  const form = screen.getByRole('form', { name: 'Agregar línea de formato' })
  await waitFor(() =>
    expect(
      within(form)
        .getAllByRole('option')
        .map((option) => option.textContent),
    ).toEqual(['Elegí un formato', 'Medianera']),
  )
})

test('agrega una línea con cantidad y recarga el seguimiento', async () => {
  const fetchMock = stubFetch(undefined, (input, options) =>
    input.includes('/lineas-formato/') && options?.method === 'POST' ? ok({ id: 9 }) : undefined,
  )
  render(<PosicionesPorFormato campaniaId={5} />)
  const form = screen.getByRole('form', { name: 'Agregar línea de formato' })
  await waitFor(() => expect(within(form).getAllByRole('option')).toHaveLength(2))
  fireEvent.change(within(form).getByLabelText('Formato'), { target: { value: '13' } })
  fireEvent.change(within(form).getByLabelText('Cantidad'), { target: { value: '20' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Agregar línea' }))
  await waitFor(() =>
    expect(llamadas(fetchMock, 'POST')).toEqual([
      ['/api/campanias/lineas-formato/', { campania: 5, formato: 13, cantidad: 20 }],
    ]),
  )
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.filter(([url]) => String(url).includes('/seguimiento/')),
    ).toHaveLength(2),
  )
})

test('agrega una línea sin cantidad', async () => {
  const fetchMock = stubFetch(undefined, (input, options) =>
    input.includes('/lineas-formato/') && options?.method === 'POST' ? ok({ id: 9 }) : undefined,
  )
  render(<PosicionesPorFormato campaniaId={5} />)
  const form = screen.getByRole('form', { name: 'Agregar línea de formato' })
  await waitFor(() => expect(within(form).getAllByRole('option')).toHaveLength(2))
  fireEvent.change(within(form).getByLabelText('Formato'), { target: { value: '13' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Agregar línea' }))
  await waitFor(() =>
    expect(llamadas(fetchMock, 'POST')[0][1]).toEqual({ campania: 5, formato: 13, cantidad: null }),
  )
})

test('pide un formato antes de agregar', async () => {
  const fetchMock = stubFetch()
  render(<PosicionesPorFormato campaniaId={5} />)
  const form = screen.getByRole('form', { name: 'Agregar línea de formato' })
  fireEvent.click(within(form).getByRole('button', { name: 'Agregar línea' }))
  expect(await within(form).findByText('Elegí un formato.')).toBeDefined()
  expect(llamadas(fetchMock, 'POST')).toEqual([])
})

test('muestra el error del servidor cuando el formato está repetido', async () => {
  stubFetch(undefined, (input, options) =>
    input.includes('/lineas-formato/') && options?.method === 'POST'
      ? rechazo({ formato: ['La campaña ya tiene una línea de Medianera.'] })
      : undefined,
  )
  render(<PosicionesPorFormato campaniaId={5} />)
  const form = screen.getByRole('form', { name: 'Agregar línea de formato' })
  await waitFor(() => expect(within(form).getAllByRole('option')).toHaveLength(2))
  fireEvent.change(within(form).getByLabelText('Formato'), { target: { value: '13' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Agregar línea' }))
  expect(await within(form).findByText('La campaña ya tiene una línea de Medianera.')).toBeDefined()
})

test('un error sin campos muestra un mensaje general', async () => {
  stubFetch(undefined, (input, options) =>
    input.includes('/lineas-formato/') && options?.method === 'POST'
      ? { ok: false, status: 500, json: async () => ({}) }
      : undefined,
  )
  render(<PosicionesPorFormato campaniaId={5} />)
  const form = screen.getByRole('form', { name: 'Agregar línea de formato' })
  await waitFor(() => expect(within(form).getAllByRole('option')).toHaveLength(2))
  fireEvent.change(within(form).getByLabelText('Formato'), { target: { value: '13' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Agregar línea' }))
  expect(await within(form).findByText('No se pudo guardar la línea.')).toBeDefined()
})

test('edita la cantidad de una línea', async () => {
  const fetchMock = stubFetch(undefined, (_input, options) =>
    options?.method === 'PATCH' ? ok({ id: 1 }) : undefined,
  )
  render(<PosicionesPorFormato campaniaId={5} />)
  const fila = (await screen.findByText('Gran Formato')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Editar' }))
  const input = within(fila).getByLabelText('Cantidad de Gran Formato') as HTMLInputElement
  expect(input.value).toBe('100')
  fireEvent.change(input, { target: { value: '' } })
  fireEvent.click(within(fila).getByRole('button', { name: 'Guardar' }))
  await waitFor(() =>
    expect(llamadas(fetchMock, 'PATCH')).toEqual([
      ['/api/campanias/lineas-formato/1/', { cantidad: null }],
    ]),
  )
})

test('cancela la edición sin guardar', async () => {
  const fetchMock = stubFetch()
  render(<PosicionesPorFormato campaniaId={5} />)
  const fila = (await screen.findByText('LED')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Editar' }))
  expect((within(fila).getByLabelText('Cantidad de LED') as HTMLInputElement).value).toBe('')
  fireEvent.click(within(fila).getByRole('button', { name: 'Cancelar' }))
  expect(within(fila).queryByLabelText('Cantidad de LED')).toBeNull()
  expect(llamadas(fetchMock, 'PATCH')).toEqual([])
})

test('muestra el error del servidor al editar la cantidad', async () => {
  stubFetch(undefined, (_input, options) =>
    options?.method === 'PATCH'
      ? rechazo({ cantidad: ['Asegúrese de que este valor es mayor o igual a 1.'] })
      : undefined,
  )
  render(<PosicionesPorFormato campaniaId={5} />)
  const fila = (await screen.findByText('Gran Formato')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Editar' }))
  fireEvent.change(within(fila).getByLabelText('Cantidad de Gran Formato'), {
    target: { value: '0' },
  })
  fireEvent.click(within(fila).getByRole('button', { name: 'Guardar' }))
  expect(
    await within(fila).findByText('Asegúrese de que este valor es mayor o igual a 1.'),
  ).toBeDefined()
})

test('quita una línea con una baja lógica', async () => {
  const fetchMock = stubFetch(undefined, (_input, options) =>
    options?.method === 'PATCH' ? ok({ id: 2 }) : undefined,
  )
  render(<PosicionesPorFormato campaniaId={5} />)
  const fila = (await screen.findByText('LED')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Quitar' }))
  await waitFor(() =>
    expect(llamadas(fetchMock, 'PATCH')).toEqual([
      ['/api/campanias/lineas-formato/2/', { activa: false }],
    ]),
  )
})

test('sin permiso de edición solo muestra el seguimiento', async () => {
  const fetchMock = stubFetch()
  render(
    <PuedeEditarContext.Provider value={false}>
      <PosicionesPorFormato campaniaId={5} />
    </PuedeEditarContext.Provider>,
  )
  await screen.findByText('Gran Formato')
  expect(screen.queryByRole('form', { name: 'Agregar línea de formato' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
  expect(screen.queryByRole('columnheader', { name: 'Acciones' })).toBeNull()
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/formatos/'))).toBe(false)
})

test('agregar carteles abre la tanda de esa línea con las fechas de la campaña', async () => {
  const onReservasCreadas = vi.fn()
  const fetchMock = stubFetch(undefined, (input) =>
    input.includes('/inventario/zonas/') ||
    input.includes('/inventario/proveedores/') ||
    input.includes('/carteles-para-tanda/')
      ? ok([])
      : undefined,
  )
  render(
    <PosicionesPorFormato
      campaniaId={5}
      fechaInicio="2026-11-01"
      fechaFin="2026-11-30"
      onReservasCreadas={onReservasCreadas}
    />,
  )
  const fila = (await screen.findByText('Gran Formato')).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Agregar carteles' }))
  const tanda = screen.getByRole('region', { name: 'Agregar carteles' })
  expect(within(tanda).getByText('Agregar carteles · Gran Formato')).toBeDefined()
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(([url]) =>
        String(url).includes('formato=10&desde=2026-11-01&hasta=2026-11-30'),
      ),
    ).toBe(true),
  )
  fireEvent.click(within(tanda).getByRole('button', { name: 'Cerrar' }))
  expect(screen.queryByRole('region', { name: 'Agregar carteles' })).toBeNull()
})
