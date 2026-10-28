import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import CampaniasLista from './CampaniasLista'
import type { Campania } from './types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const fail = (status: number, data: unknown) => ({ ok: false, status, json: async () => data })

const campanias: Campania[] = [
  {
    id: 11,
    nombre: 'Verano 2027',
    marca: 7,
    marca_nombre: 'Agua Cumbre',
    cliente_facturacion: null,
    cliente_factura: 1,
    cliente_factura_nombre: 'Agencia Andes',
    fecha_inicio: '2027-01-01',
    fecha_fin: '2027-01-31',
    estado: 'confirmada',
  },
  {
    id: 12,
    nombre: '',
    marca: 7,
    marca_nombre: 'Agua Cumbre',
    cliente_facturacion: 2,
    cliente_factura: 2,
    cliente_factura_nombre: 'Medios del Sur',
    fecha_inicio: null,
    fecha_fin: null,
    estado: 'cancelada',
  },
]

function mockFetch(response: unknown) {
  const fetchMock = vi.fn(async (_input: string) => response)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('pide las campañas del cliente y las muestra con su estado y quién factura', async () => {
  const fetchMock = mockFetch(ok(campanias))
  render(<CampaniasLista filtro={{ cliente: 1 }} titulo="Campañas de Agencia Andes" />)

  const seccion = screen.getByRole('region', { name: 'Campañas de Agencia Andes' })
  expect(within(seccion).getByText('Cargando campañas…')).toBeDefined()
  expect(await within(seccion).findByText('Verano 2027')).toBeDefined()
  expect(String(fetchMock.mock.calls[0][0])).toBe('/api/campanias/campanias/?cliente=1')
  const lista = within(seccion).getByRole('list', { name: 'Campañas' })
  expect(within(lista).getByText('Confirmada')).toBeDefined()
  expect(within(lista).getByText('Cancelada')).toBeDefined()
  expect(within(seccion).getByText('Medios del Sur')).toBeDefined()
  expect(within(seccion).getByText('Campaña #12')).toBeDefined()
  expect(within(seccion).getByText('01/01/2027 → 31/01/2027')).toBeDefined()
  expect(within(seccion).getByText('Sin fechas')).toBeDefined()
  expect(within(seccion).getAllByText('Agua Cumbre')).toHaveLength(2)
})

test('campaniasLista_filtroPorEstado_muestraSoloEseEstadoYAvisaLaCantidad', async () => {
  mockFetch(ok(campanias))
  const onCargadas = vi.fn()
  render(
    <CampaniasLista
      filtro={{ cliente: 1 }}
      titulo="Campañas de Agencia Andes"
      onCargadas={onCargadas}
    />,
  )

  await screen.findByText('Verano 2027')
  expect(onCargadas).toHaveBeenCalledWith(campanias.length)
  const filtros = screen.getByRole('group', { name: 'Filtrar por estado' })
  fireEvent.click(within(filtros).getByRole('button', { name: 'Cancelada' }))
  expect(
    within(filtros).getByRole('button', { name: 'Cancelada' }).getAttribute('aria-pressed'),
  ).toBe('true')
  expect(screen.queryByText('Verano 2027')).toBeNull()
  fireEvent.click(within(filtros).getByRole('button', { name: 'Perdida' }))
  expect(screen.getByText('No hay campañas en ese estado.')).toBeDefined()
  fireEvent.click(within(filtros).getByRole('button', { name: 'Todas' }))
  expect(screen.getByText('Verano 2027')).toBeDefined()
})

test('en la ficha de una marca filtra por marca y oculta la columna de marca', async () => {
  const fetchMock = mockFetch(ok(campanias))
  render(<CampaniasLista filtro={{ marca: 7 }} titulo="Campañas de Agua Cumbre" ocultar="marca" />)

  expect(await screen.findByText('Verano 2027')).toBeDefined()
  expect(String(fetchMock.mock.calls[0][0])).toBe('/api/campanias/campanias/?marca=7')
  expect(screen.queryByRole('columnheader', { name: 'Marca' })).toBeNull()
  expect(screen.queryByText('Agua Cumbre')).toBeNull()
})

test('sin campañas muestra la sección vacía sin errores', async () => {
  mockFetch(ok([]))
  render(<CampaniasLista filtro={{ cliente: 1 }} titulo="Campañas de Agencia Andes" />)

  expect(await screen.findByText('Todavía no hay campañas.')).toBeDefined()
  expect(screen.queryByRole('alert')).toBeNull()
})

test('anuncia como alerta el error al cargar las campañas', async () => {
  mockFetch(fail(500, { detail: 'Error' }))
  render(<CampaniasLista filtro={{ marca: 7 }} titulo="Campañas de Agua Cumbre" />)

  expect((await screen.findByRole('alert')).textContent).toBe('No se pudieron cargar las campañas.')
})
