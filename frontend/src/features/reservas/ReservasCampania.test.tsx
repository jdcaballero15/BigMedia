import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import ReservasCampania from './ReservasCampania'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const reserva = {
  id: 3,
  campania: 5,
  campania_nombre: 'Verano 2027',
  cartel: 7,
  cartel_nombre: 'Av. San Martín 1234 · 6x3',
  fecha_inicio: '2026-08-01',
  fecha_fin: '2026-08-31',
  estado: 'confirmada',
  estado_visible: 'confirmada',
  precio_alquiler: '150000.00',
  precio_impresion: '0.00',
  precio_fijacion: '0.00',
  total: '150000.00',
  nombre: "McDonald's - Av. San Martín 1234 · 6x3 - Ago 2026",
}

const cartel = {
  id: 7,
  nombre_visible: 'Av. San Martín 1234 · 6x3',
  tarifa_lista: '150000.00',
  estado: 1,
}

function stubFetch(overrides?: (input: string, options?: RequestInit) => unknown) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const custom = overrides?.(input, options)
    if (custom) return custom
    if (input.includes('/inventario/carteles/')) return ok([cartel])
    if (input.includes('/reservas/reservas/')) return ok([reserva])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('lista las reservas de la campaña', async () => {
  stubFetch()
  render(<ReservasCampania campaniaId={5} />)
  expect(await screen.findByText(reserva.nombre)).toBeDefined()
  expect(screen.getByText('01/08/2026 → 31/08/2026')).toBeDefined()
})

test('pide las reservas filtrando por campaña', async () => {
  const fetchMock = stubFetch()
  render(<ReservasCampania campaniaId={5} />)
  await screen.findByText(reserva.nombre)
  expect(
    fetchMock.mock.calls.some(([url]) => String(url).includes('/reservas/reservas/?campania=5')),
  ).toBe(true)
})

test('crea una reserva desde la campaña', async () => {
  const fetchMock = stubFetch((input, options) => {
    if (input.includes('/reservas/reservas/') && options?.method === 'POST') return ok({ id: 9 })
    return undefined
  })
  render(<ReservasCampania campaniaId={5} />)
  await screen.findByText(reserva.nombre)
  fireEvent.click(screen.getByRole('button', { name: 'Nueva reserva' }))
  const form = screen.getByRole('form', { name: 'Formulario de reserva' })
  fireEvent.change(within(form).getByLabelText('Cartel'), { target: { value: '7' } })
  fireEvent.change(within(form).getByLabelText('Fecha de inicio'), {
    target: { value: '01/08/2026' },
  })
  fireEvent.change(within(form).getByLabelText('Fecha de fin'), { target: { value: '31/08/2026' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar reserva' }))
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          String(url) === '/api/reservas/reservas/' &&
          options?.method === 'POST' &&
          JSON.parse(String(options.body)).campania === 5,
      ),
    ).toBe(true),
  )
})

test('pide también los carteles de baja para mostrar el ya asignado', async () => {
  const fetchMock = stubFetch()
  render(<ReservasCampania campaniaId={5} />)
  await screen.findByText(reserva.nombre)
  expect(fetchMock).toHaveBeenCalledWith(
    '/api/inventario/carteles/?incluir_bajas=1',
    expect.anything(),
  )
})

function abrirMenu() {
  fireEvent.click(screen.getByRole('button', { name: 'Más acciones' }))
}

test('quitar una reserva pide confirmación y la saca de la campaña', async () => {
  const onCambio = vi.fn()
  vi.stubGlobal(
    'confirm',
    vi.fn(() => true),
  )
  const fetchMock = stubFetch((input, options) =>
    input.includes('/quitar/') && options?.method === 'POST'
      ? ok({ ...reserva, estado: 'cancelada', estado_visible: 'cancelada' })
      : undefined,
  )
  render(<ReservasCampania campaniaId={5} onCambio={onCambio} />)
  await screen.findByText(reserva.nombre)
  abrirMenu()
  fireEvent.click(screen.getByRole('button', { name: 'Quitar' }))
  await waitFor(() => expect(onCambio).toHaveBeenCalledTimes(1))
  expect(
    fetchMock.mock.calls.some(
      ([url, options]) =>
        String(url) === '/api/reservas/reservas/3/quitar/' && options?.method === 'POST',
    ),
  ).toBe(true)
})

test('si no se confirma, quitar no llama al servidor', async () => {
  vi.stubGlobal(
    'confirm',
    vi.fn(() => false),
  )
  const fetchMock = stubFetch()
  render(<ReservasCampania campaniaId={5} />)
  await screen.findByText(reserva.nombre)
  abrirMenu()
  fireEvent.click(screen.getByRole('button', { name: 'Quitar' }))
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/quitar/'))).toBe(false)
})

test('una reserva en exhibición avisa que termina hoy', async () => {
  const confirmar = vi.fn((_mensaje?: string) => false)
  vi.stubGlobal('confirm', confirmar)
  stubFetch((input) =>
    input.includes('/reservas/reservas/')
      ? ok([{ ...reserva, fecha_inicio: '2020-01-01', fecha_fin: '2099-12-31' }])
      : undefined,
  )
  render(<ReservasCampania campaniaId={5} />)
  await screen.findByText(reserva.nombre)
  abrirMenu()
  fireEvent.click(screen.getByRole('button', { name: 'Quitar' }))
  expect(String(confirmar.mock.calls[0]?.[0])).toContain('termina hoy')
})

test('si falla quitar lo avisa', async () => {
  vi.stubGlobal(
    'confirm',
    vi.fn(() => true),
  )
  stubFetch((input) =>
    input.includes('/quitar/')
      ? { ok: false, status: 400, json: async () => ({ reserva: ['La reserva ya terminó.'] }) }
      : undefined,
  )
  render(<ReservasCampania campaniaId={5} />)
  await screen.findByText(reserva.nombre)
  abrirMenu()
  fireEvent.click(screen.getByRole('button', { name: 'Quitar' }))
  expect(await screen.findByRole('alert')).toBeDefined()
})

test('una reserva finalizada o cancelada no ofrece quitar y muestra su estado', async () => {
  stubFetch((input) =>
    input.includes('/reservas/reservas/')
      ? ok([{ ...reserva, estado_visible: 'finalizada' }])
      : undefined,
  )
  render(<ReservasCampania campaniaId={5} />)
  await screen.findByText(reserva.nombre)
  expect(screen.getByText('Finalizada')).toBeDefined()
  abrirMenu()
  expect(screen.queryByRole('button', { name: 'Quitar' })).toBeNull()
})

test('con la campaña cancelada no ofrece nueva reserva ni quitar', async () => {
  stubFetch()
  render(<ReservasCampania campaniaId={5} campaniaCancelada />)
  await screen.findByText(reserva.nombre)
  expect(screen.queryByRole('button', { name: 'Nueva reserva' })).toBeNull()
  abrirMenu()
  expect(screen.queryByRole('button', { name: 'Quitar' })).toBeNull()
})
