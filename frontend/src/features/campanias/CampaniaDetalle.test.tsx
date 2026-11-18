import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import CampaniaDetalle from './CampaniaDetalle'
import type { Campania } from './types'

// El hub monta ReservasCampania, que pide carteles y reservas: devolvemos listas vacías.
beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [] }))
})

const campania: Campania = {
  id: 5,
  nombre: 'Verano 2027',
  marca: 10,
  marca_nombre: 'Axe',
  cliente_facturacion: null,
  cliente_factura: 1,
  cliente_factura_nombre: 'Unilever',
  fecha_inicio: '2027-01-01',
  fecha_fin: '2027-01-31',
  estado: 'confirmada',
  ordenes_publicidad: [],
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('muestra el cliente que factura, el estado y las secciones próximas', () => {
  render(<CampaniaDetalle campania={campania} onEditar={vi.fn()} onVolver={vi.fn()} />)
  expect(screen.getByRole('heading', { name: 'Verano 2027' })).toBeDefined()
  expect(screen.getByText('Unilever')).toBeDefined()
  expect(screen.getByText('Confirmada')).toBeDefined()
  expect(screen.getByText('01/01/2027 → 31/01/2027')).toBeDefined()
  expect(screen.getByRole('heading', { name: 'Reservas' })).toBeDefined()
  expect(screen.getByRole('heading', { name: 'Costos y rentabilidad' })).toBeDefined()
})

test('sin fechas muestra el aviso de período', () => {
  render(
    <CampaniaDetalle
      campania={{ ...campania, fecha_inicio: null, fecha_fin: null }}
      onEditar={vi.fn()}
      onVolver={vi.fn()}
    />,
  )
  expect(screen.getByText('Sin fechas planificadas')).toBeDefined()
})

test('la tarjeta de datos tiene espacio interior y separación con la siguiente', () => {
  render(<CampaniaDetalle campania={campania} onEditar={vi.fn()} onVolver={vi.fn()} />)
  const tarjeta = screen.getByText('Cliente que factura').closest('.card') as HTMLElement
  expect(tarjeta.classList.contains('card-cuerpo')).toBe(true)
  expect(tarjeta.classList.contains('section-gap')).toBe(true)
})

// --- Cancelar la campaña (HU-024) ---

const respuestaVacia = { ok: true, status: 200, json: async () => [] }

function stubCancelar(respuesta: unknown) {
  const fetchMock = vi.fn(async (input: string, _opciones?: RequestInit) =>
    String(input).includes('/cancelar-campania/') ? respuesta : respuestaVacia,
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

test('cancelar la campaña pide confirmación, llama al servidor y la muestra Cancelada', async () => {
  vi.stubGlobal(
    'confirm',
    vi.fn(() => true),
  )
  const fetchMock = stubCancelar({
    ok: true,
    status: 200,
    json: async () => ({ campania: 5, estado: 'cancelada', canceladas: [], terminadas: [] }),
  })
  render(<CampaniaDetalle campania={campania} onEditar={vi.fn()} onVolver={vi.fn()} />)
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar campaña' }))
  expect(await screen.findByText('Cancelada')).toBeDefined()
  expect(screen.queryByRole('button', { name: 'Cancelar campaña' })).toBeNull()
  const llamada = fetchMock.mock.calls.find(([url]) => String(url).includes('/cancelar-campania/'))
  const opciones = llamada?.[1] ?? {}
  expect(JSON.parse(String(opciones.body))).toEqual({
    campania: 5,
  })
})

test('si no se confirma, no cancela', () => {
  vi.stubGlobal(
    'confirm',
    vi.fn(() => false),
  )
  const fetchMock = stubCancelar(respuestaVacia)
  render(<CampaniaDetalle campania={campania} onEditar={vi.fn()} onVolver={vi.fn()} />)
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar campaña' }))
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/cancelar-campania/'))).toBe(
    false,
  )
  expect(screen.getByText('Confirmada')).toBeDefined()
})

test('si falla la cancelación lo avisa y sigue Confirmada', async () => {
  vi.stubGlobal(
    'confirm',
    vi.fn(() => true),
  )
  stubCancelar({
    ok: false,
    status: 400,
    json: async () => ({ campania: ['La campaña ya está cancelada.'] }),
  })
  render(<CampaniaDetalle campania={campania} onEditar={vi.fn()} onVolver={vi.fn()} />)
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar campaña' }))
  await waitFor(() => expect(screen.getAllByRole('alert').length).toBeGreaterThan(0))
  expect(screen.getByText('Confirmada')).toBeDefined()
})

test('una campaña cancelada no ofrece cancelar', () => {
  render(
    <CampaniaDetalle
      campania={{ ...campania, estado: 'cancelada' }}
      onEditar={vi.fn()}
      onVolver={vi.fn()}
    />,
  )
  expect(screen.getByText('Cancelada')).toBeDefined()
  expect(screen.queryByRole('button', { name: 'Cancelar campaña' })).toBeNull()
})
