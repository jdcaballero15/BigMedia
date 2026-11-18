import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import PosicionesAlta from './PosicionesAlta'
import type { LineaAlta } from './PosicionesAlta'
import { crearLineasYReservas } from './altaConPosiciones'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const error = (status: number, data: unknown) => ({ ok: false, status, json: async () => data })

const formatos = [
  { id: 10, nombre: 'Gran Formato', activo: true },
  { id: 11, nombre: 'Formato Viejo', activo: false },
  { id: 12, nombre: 'Monocolumna', activo: true },
]

function stubFetch(overrides?: (input: string, options?: RequestInit) => unknown) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const custom = overrides?.(input, options)
    if (custom) return custom
    if (input.includes('/inventario/formatos/')) return ok(formatos)
    if (input.includes('/inventario/')) return ok([])
    if (input.includes('/carteles-para-tanda/')) return ok([])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const linea = (extra: Partial<LineaAlta> = {}): LineaAlta => ({
  formato: 10,
  formato_nombre: 'Gran Formato',
  cantidad: null,
  seleccion: null,
  ...extra,
})

function renderizar(lineas: LineaAlta[] = []) {
  const onCambio = vi.fn()
  render(
    <PosicionesAlta lineas={lineas} onCambio={onCambio} fechaInicio="2026-11-01" fechaFin="" />,
  )
  return onCambio
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('ofrece solo formatos activos que todavía no tienen línea', async () => {
  stubFetch()
  renderizar([linea()])
  await screen.findByRole('option', { name: 'Monocolumna' })
  expect(screen.queryByRole('option', { name: 'Gran Formato' })).toBeNull()
  expect(screen.queryByRole('option', { name: 'Formato Viejo' })).toBeNull()
})

test('agregar una línea sin formato o con cantidad inválida muestra el error', async () => {
  stubFetch()
  const onCambio = renderizar()
  await screen.findByRole('option', { name: 'Gran Formato' })
  fireEvent.click(screen.getByRole('button', { name: 'Agregar línea' }))
  expect(screen.getByText('Elegí un formato.')).toBeDefined()
  fireEvent.change(screen.getByLabelText('Formato'), { target: { value: '10' } })
  fireEvent.change(screen.getByLabelText('Cantidad'), { target: { value: '0' } })
  fireEvent.click(screen.getByRole('button', { name: 'Agregar línea' }))
  expect(
    screen.getByText('La cantidad tiene que ser un número entero mayor que cero.'),
  ).toBeDefined()
  expect(onCambio).not.toHaveBeenCalled()
})

test('una línea sin cantidad se acepta', async () => {
  stubFetch()
  const onCambio = renderizar()
  await screen.findByRole('option', { name: 'Gran Formato' })
  fireEvent.change(screen.getByLabelText('Formato'), { target: { value: '10' } })
  fireEvent.click(screen.getByRole('button', { name: 'Agregar línea' }))
  expect(onCambio).toHaveBeenCalledWith([linea()])
})

test('quitar una línea la saca y cierra su selección de carteles', async () => {
  stubFetch()
  const onCambio = renderizar([linea(), linea({ formato: 12, formato_nombre: 'Monocolumna' })])
  fireEvent.click(screen.getAllByRole('button', { name: 'Agregar carteles' })[0]!)
  expect(await screen.findByRole('region', { name: 'Agregar carteles' })).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Quitar Gran Formato' }))
  expect(onCambio).toHaveBeenCalledWith([linea({ formato: 12, formato_nombre: 'Monocolumna' })])
  expect(screen.queryByRole('region', { name: 'Agregar carteles' })).toBeNull()
})

test('una línea con carteles elegidos ofrece cambiarlos y suma el total', () => {
  stubFetch()
  const carteles = [1, 2, 3].map((id) => ({
    id,
    nombre_visible: `Av. ${id}`,
    zona_nombre: 'Ciudad',
    proveedor_nombre: null,
    tarifa_lista: null,
    capacidad: 1,
    ocupados: 0,
    en_campania: false,
  }))
  renderizar([linea({ seleccion: { carteles, desde: '2026-11-01', hasta: '2026-11-30' } })])
  expect(screen.getByRole('button', { name: 'Cambiar carteles' })).toBeDefined()
  expect(screen.getByText('Carteles elegidos: 3')).toBeDefined()
})

test('Enter en un campo de la sección no envía el formulario de la campaña', async () => {
  stubFetch()
  const onSubmit = vi.fn((event: Event) => event.preventDefault())
  render(
    <form onSubmit={(event) => onSubmit(event.nativeEvent)}>
      <PosicionesAlta lineas={[]} onCambio={vi.fn()} fechaInicio="" fechaFin="" />
    </form>,
  )
  const evento = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true })
  screen.getByLabelText('Cantidad').dispatchEvent(evento)
  expect(evento.defaultPrevented).toBe(true)
})

test('si fallan los formatos lo avisa', async () => {
  stubFetch((input) => (input.includes('/inventario/formatos/') ? error(500, {}) : undefined))
  renderizar()
  expect(await screen.findByText('No se pudieron cargar los formatos.')).toBeDefined()
})

test('una línea que falla al guardar queda en el resumen y sus carteles se reservan igual', async () => {
  stubFetch((input) => {
    if (input.includes('/lineas-formato/'))
      return error(400, { formato: ['Ya hay una línea de este formato.'] })
    if (input.includes('/en-bloque/'))
      return ok({ creadas: [], existentes: [{ cartel: 1, reserva: 5 }], fallidas: [] })
    return undefined
  })
  const carteles = [
    {
      id: 1,
      nombre_visible: 'Av. 1',
      zona_nombre: 'Ciudad',
      proveedor_nombre: null,
      tarifa_lista: null,
      capacidad: 1,
      ocupados: 0,
      en_campania: false,
    },
  ]
  const resultado = await crearLineasYReservas({ id: 9, nombre: 'Invierno' }, [
    linea({ seleccion: { carteles, desde: '2026-11-01', hasta: '2026-11-30' } }),
    linea({ formato: 12, formato_nombre: 'Monocolumna' }),
  ])
  expect(resultado.reservasCreadas).toBe(1)
  expect(resultado.lineasFallidas.map((item) => item.formato)).toEqual([
    'Gran Formato',
    'Monocolumna',
  ])
  expect(resultado.cartelesFallidos).toEqual([])
})
