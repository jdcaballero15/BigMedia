import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import ReservasAfectadas from './ReservasAfectadas'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const falla = { ok: false, status: 500, json: async () => ({}) }

const reserva = (id: number, estado: string) => ({
  id,
  nombre: `Marca - Costanera 500 - Reserva ${id}`,
  campania: 5,
  campania_nombre: 'Verano',
  cartel: 9,
  cartel_nombre: 'Costanera 500',
  fecha_inicio: '2026-11-01',
  fecha_fin: '2026-11-30',
  estado,
})

function stubFetch(respuesta: unknown) {
  const fetchMock = vi.fn<(input: string) => Promise<unknown>>(async () => respuesta)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function renderizar(onCerrar = vi.fn()) {
  render(
    <ReservasAfectadas
      cartelId={9}
      cartelNombre="Costanera 500"
      estadoNombre="Apagado"
      onCerrar={onCerrar}
    />,
  )
  return onCerrar
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('lista las reservas activas del cartel fuera de servicio', async () => {
  const fetchMock = stubFetch(ok([reserva(1, 'confirmada'), reserva(2, 'pendiente')]))
  const onCerrar = renderizar()
  const aviso = await screen.findByRole('alertdialog', {
    name: 'Reservas activas del cartel fuera de servicio',
  })
  expect(String(fetchMock.mock.calls[0]?.[0])).toContain(
    '/api/reservas/reservas/?cartel=9&vigentes=1',
  )
  expect(aviso.textContent).toContain('Costanera 500 quedó en «Apagado» y tiene 2 reservas activas')
  const tabla = screen.getByRole('table', { name: 'Reservas activas del cartel' })
  expect(tabla.textContent).toContain('Verano')
  expect(tabla.textContent).toContain('01/11/2026')
  expect(tabla.textContent).toContain('Confirmada')
  expect(tabla.textContent).toContain('Pendiente')
  fireEvent.click(screen.getByRole('button', { name: 'Entendido' }))
  expect(onCerrar).toHaveBeenCalledTimes(1)
})

test('usa el singular con una sola reserva', async () => {
  stubFetch(ok([reserva(1, 'confirmada')]))
  renderizar()
  const aviso = await screen.findByRole('alertdialog')
  expect(aviso.textContent).toContain('tiene 1 reserva activa.')
})

test('muestra que está consultando mientras carga', () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => new Promise(() => undefined)),
  )
  renderizar()
  expect(screen.getByRole('status').textContent).toContain('Consultando reservas activas')
})

test('avisa que el cartel no tiene reservas activas', async () => {
  const fetchMock = stubFetch(ok([]))
  const onCerrar = renderizar()
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
  const estado = await screen.findByText(/no tiene reservas activas/)
  expect(estado.textContent).toContain('Costanera 500 quedó en «Apagado»')
  expect(screen.queryByRole('alertdialog')).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: 'Entendido' }))
  expect(onCerrar).toHaveBeenCalledTimes(1)
})

test('avisa si no se pudieron consultar las reservas', async () => {
  stubFetch(falla)
  const onCerrar = renderizar()
  const alerta = await screen.findByRole('alert')
  expect(alerta.textContent).toContain('No se pudieron consultar las reservas activas del cartel.')
  fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }))
  expect(onCerrar).toHaveBeenCalledTimes(1)
})
