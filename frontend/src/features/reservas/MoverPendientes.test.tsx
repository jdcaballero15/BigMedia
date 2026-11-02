import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import MoverPendientes from './MoverPendientes'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const falla = { ok: false, status: 500, json: async () => ({}) }

const pendiente = (id: number, inicio = '2026-11-01', fin = '2026-11-30') => ({
  id,
  fecha_inicio: inicio,
  fecha_fin: fin,
  estado: 'pendiente',
})

function stubFetch(
  pendientes: unknown[],
  overrides?: (input: string, options?: RequestInit) => unknown,
) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const custom = overrides?.(input, options)
    if (custom) return custom
    if (input.includes('/mover-pendientes/')) return ok({ movidas: [1] })
    if (input.includes('/reservas/reservas/?')) return ok(pendientes)
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function renderizar(onListo = vi.fn()) {
  render(
    <MoverPendientes
      campaniaId={5}
      inicioAnterior="2026-11-01"
      finAnterior="2026-11-30"
      inicioNuevo="2026-12-01"
      finNuevo="2026-12-31"
      onListo={onListo}
    />,
  )
  return onListo
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('pregunta por las Pendientes que tenían las fechas anteriores y las mueve', async () => {
  const fetchMock = stubFetch([pendiente(1), pendiente(2, '2026-11-15')])
  const onListo = renderizar()
  const dialogo = await screen.findByRole('alertdialog', { name: 'Actualizar reservas Pendientes' })
  expect(dialogo.textContent).toContain('las 1 reservas Pendientes del 01/11/2026 → 30/11/2026')
  expect(dialogo.textContent).toContain('a 01/12/2026 → 31/12/2026')
  expect(String(fetchMock.mock.calls[0][0])).toContain('campania=5&estado=pendiente')
  fireEvent.click(screen.getByRole('button', { name: 'Actualizar Pendientes' }))
  await waitFor(() => expect(onListo).toHaveBeenCalledTimes(1))
  const [, options] = fetchMock.mock.calls.find(([url]) => String(url).includes('/mover-')) ?? []
  expect(JSON.parse(String(options?.body))).toEqual({
    campania: 5,
    fecha_inicio_anterior: '2026-11-01',
    fecha_fin_anterior: '2026-11-30',
  })
})

test('si no hay Pendientes con las fechas anteriores no pregunta', async () => {
  stubFetch([pendiente(2, '2026-11-15')])
  const onListo = renderizar()
  await waitFor(() => expect(onListo).toHaveBeenCalledTimes(1))
  expect(screen.queryByRole('alertdialog')).toBeNull()
})

test('rechazar no mueve nada', async () => {
  const fetchMock = stubFetch([pendiente(1)])
  const onListo = renderizar()
  await screen.findByRole('alertdialog')
  fireEvent.click(screen.getByRole('button', { name: 'No, dejarlas' }))
  expect(onListo).toHaveBeenCalledTimes(1)
  expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/mover-'))).toBe(false)
})

test('si falla el movimiento lo avisa y deja reintentar', async () => {
  stubFetch([pendiente(1)], (input) => (input.includes('/mover-pendientes/') ? falla : undefined))
  const onListo = renderizar()
  await screen.findByRole('alertdialog')
  fireEvent.click(screen.getByRole('button', { name: 'Actualizar Pendientes' }))
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No se pudieron actualizar las reservas. Podés reintentar.',
  )
  expect(
    (screen.getByRole('button', { name: 'Actualizar Pendientes' }) as HTMLButtonElement).disabled,
  ).toBe(false)
  expect(onListo).not.toHaveBeenCalled()
})

test('si no se pueden leer las reservas no pregunta', async () => {
  stubFetch([], (input) => (input.includes('/reservas/reservas/?') ? falla : undefined))
  const onListo = renderizar()
  await waitFor(() => expect(onListo).toHaveBeenCalledTimes(1))
})
