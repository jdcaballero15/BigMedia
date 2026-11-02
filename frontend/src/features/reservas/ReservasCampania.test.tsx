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
  estado: 'pendiente',
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

const resultadoConfirmacion = {
  confirmadas: [3],
  conflictos: [
    {
      reserva: 4,
      nombre: 'Axe - Av. Corrientes 1 · 6x3 - Ago 2026',
      cartel_nombre: 'Av. Corrientes 1 · 6x3',
      fecha_inicio: '2026-08-01',
      fecha_fin: '2026-08-31',
      ocupada_por: [{ campania: 8, campania_nombre: 'Invierno' }],
    },
  ],
}

test('con varias reservas confirmadas y en conflicto lo dice en plural', async () => {
  const conflicto = resultadoConfirmacion.conflictos[0]
  stubFetch((input, options) =>
    input.includes('/confirmar-en-bloque/') && options?.method === 'POST'
      ? ok({ confirmadas: [3, 5], conflictos: [conflicto, { ...conflicto, reserva: 6 }] })
      : undefined,
  )
  render(<ReservasCampania campaniaId={5} campaniaConfirmada onCambio={vi.fn()} />)
  await screen.findByText(reserva.nombre)
  fireEvent.click(screen.getByRole('button', { name: 'Confirmar reservas' }))
  const resultado = await screen.findByRole('status', { name: 'Resultado de la confirmación' })
  expect(within(resultado).getByText('Se confirmaron 2 reservas.')).toBeDefined()
  expect(within(resultado).getByText('2 quedaron Pendientes por falta de cupo:')).toBeDefined()
})

test('confirma las Pendientes en bloque y lista los conflictos', async () => {
  const onCambio = vi.fn()
  const fetchMock = stubFetch((input, options) =>
    input.includes('/confirmar-en-bloque/') && options?.method === 'POST'
      ? ok(resultadoConfirmacion)
      : undefined,
  )
  render(<ReservasCampania campaniaId={5} campaniaConfirmada onCambio={onCambio} />)
  await screen.findByText(reserva.nombre)
  fireEvent.click(screen.getByRole('button', { name: 'Confirmar reservas' }))
  const resultado = await screen.findByRole('status', { name: 'Resultado de la confirmación' })
  expect(within(resultado).getByText('Se confirmó 1 reserva.')).toBeDefined()
  expect(within(resultado).getByText('1 quedó Pendiente por falta de cupo:')).toBeDefined()
  expect(
    within(resultado).getByText(
      'Av. Corrientes 1 · 6x3, 01/08/2026 → 31/08/2026: ocupado por Invierno',
    ),
  ).toBeDefined()
  const [, options] =
    fetchMock.mock.calls.find(([url]) => String(url).includes('/confirmar-en-bloque/')) ?? []
  expect(JSON.parse(String(options?.body))).toEqual({ campania: 5 })
  expect(onCambio).toHaveBeenCalledTimes(1)
})

test('sin la campaña Confirmada no ofrece confirmar en bloque', async () => {
  stubFetch()
  render(<ReservasCampania campaniaId={5} />)
  await screen.findByText(reserva.nombre)
  expect(screen.queryByRole('button', { name: 'Confirmar reservas' })).toBeNull()
})

test('sin Pendientes no ofrece confirmar en bloque', async () => {
  stubFetch((input) =>
    input.includes('/reservas/reservas/') ? ok([{ ...reserva, estado: 'confirmada' }]) : undefined,
  )
  render(<ReservasCampania campaniaId={5} campaniaConfirmada />)
  await screen.findByText(reserva.nombre)
  expect(screen.queryByRole('button', { name: 'Confirmar reservas' })).toBeNull()
})

test('si falla la confirmación en bloque lo avisa', async () => {
  stubFetch((input) =>
    input.includes('/confirmar-en-bloque/')
      ? { ok: false, status: 400, json: async () => ({}) }
      : undefined,
  )
  render(<ReservasCampania campaniaId={5} campaniaConfirmada />)
  await screen.findByText(reserva.nombre)
  fireEvent.click(screen.getByRole('button', { name: 'Confirmar reservas' }))
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No se pudieron confirmar las reservas.',
  )
})
