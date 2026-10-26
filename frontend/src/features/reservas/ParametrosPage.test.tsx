import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import ParametrosPage from './ParametrosPage'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const fail = (status: number, data: unknown) => ({ ok: false, status, json: async () => data })

const URL = '/api/reservas/parametros/'
const iniciales = { borde_inclusivo: true, tentativa_bloquea: false }

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('carga los parámetros en las casillas', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ok(iniciales)),
  )
  render(<ParametrosPage />)
  const borde = await screen.findByLabelText<HTMLInputElement>('El día de borde se pisa')
  expect(borde.checked).toBe(true)
  expect(
    screen.getByLabelText<HTMLInputElement>('La reserva pendiente bloquea el cupo').checked,
  ).toBe(false)
})

test('guarda el cambio con PATCH y avisa', async () => {
  const fetchMock = vi.fn(async (_input: string, options?: RequestInit) =>
    options?.method === 'PATCH' ? ok(JSON.parse(String(options.body))) : ok(iniciales),
  )
  vi.stubGlobal('fetch', fetchMock)
  render(<ParametrosPage />)

  fireEvent.click(await screen.findByLabelText('La reserva pendiente bloquea el cupo'))
  fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

  expect((await screen.findByRole('status')).textContent).toBe('Parámetros guardados.')
  const envio = fetchMock.mock.calls.find(([, options]) => options?.method === 'PATCH')
  expect(envio?.[0]).toBe(URL)
  expect(JSON.parse(String(envio?.[1]?.body))).toEqual({
    borde_inclusivo: true,
    tentativa_bloquea: true,
  })
})

test('muestra el error del servidor al guardar', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (_input: string, options?: RequestInit) =>
      options?.method === 'PATCH'
        ? fail(403, { detail: 'No tenés permiso para realizar esta acción.' })
        : ok(iniciales),
    ),
  )
  render(<ParametrosPage />)
  fireEvent.click(await screen.findByLabelText('El día de borde se pisa'))
  fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No tenés permiso para realizar esta acción.',
  )
  expect(screen.queryByRole('status')).toBeNull()
})

test('avisa si no se pudieron cargar', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => fail(500, {})),
  )
  render(<ParametrosPage />)
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No se pudieron cargar los parámetros.',
  )
  expect(screen.queryByRole('button', { name: 'Guardar' })).toBeNull()
})
