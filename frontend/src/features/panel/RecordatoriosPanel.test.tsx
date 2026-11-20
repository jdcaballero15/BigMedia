import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import RecordatoriosPanel from './RecordatoriosPanel'
import { PuedeEditarContext } from '../../shared/sesion'
import type { Interaccion } from '../campanias/types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const fail = (status: number) => ({ ok: false, status, json: async () => ({}) })

const URL = '/api/campanias/interacciones/?recordatorio=pendiente'

function recordatorio(id: number, fecha: string, texto: string): Interaccion {
  return {
    id,
    tipo: 'reunion',
    asunto: 'Reunión de verano',
    fecha: '2026-10-20',
    notas: '',
    cliente: 2,
    cliente_nombre: 'Bodega Norte',
    contacto: null,
    contacto_nombre: null,
    campania: null,
    campania_nombre: null,
    marca: null,
    marca_nombre: null,
    registrada_por_nombre: 'operativo',
    recordatorio_fecha: fecha,
    recordatorio_texto: texto,
    recordatorio_hecho_en: null,
    recordatorio_hecho_por_nombre: null,
  }
}

const vencido = recordatorio(5, '2026-11-02', 'Enviar presupuesto')
const deHoy = recordatorio(6, '2026-11-19', 'Llamar para confirmar')

type Route = (url: string, options?: RequestInit) => unknown

function mockFetch(route: Route) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const response = route(input, options)
    if (response === undefined) throw new Error(`URL inesperada: ${input}`)
    return response
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

test('lista los recordatorios pendientes y marca solo los vencidos', async () => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 10, 19, 9, 0))
  mockFetch((url) => (url === URL ? ok([vencido, deHoy]) : undefined))
  render(<RecordatoriosPanel />)

  const lista = await screen.findByRole('list', { name: 'Recordatorios' })
  const filas = within(lista).getAllByRole('listitem')
  expect(filas).toHaveLength(2)
  expect(within(filas[0]).getByText('Enviar presupuesto')).toBeDefined()
  expect(within(filas[0]).getByText('Bodega Norte · cargó operativo')).toBeDefined()
  expect(within(filas[0]).getByText('02/11/2026')).toBeDefined()
  expect(within(filas[0]).getByText('Vencido')).toBeDefined()
  expect(within(filas[1]).getByText('Llamar para confirmar')).toBeDefined()
  expect(within(filas[1]).queryByText('Vencido')).toBeNull()
})

test('Hecho manda el POST y saca el recordatorio de la lista', async () => {
  let hecho = false
  const fetchMock = mockFetch((url, options) => {
    if (
      url === '/api/campanias/interacciones/5/recordatorio-hecho/' &&
      options?.method === 'POST'
    ) {
      hecho = true
      return ok(vencido)
    }
    if (url === URL) return ok(hecho ? [deHoy] : [vencido, deHoy])
    return undefined
  })
  render(<RecordatoriosPanel />)

  const fila = (await screen.findByText('Enviar presupuesto')).closest('li') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Hecho' }))

  await waitFor(() => expect(screen.queryByText('Enviar presupuesto')).toBeNull())
  expect(screen.getByText('Llamar para confirmar')).toBeDefined()
  expect(
    fetchMock.mock.calls.some(
      ([url, options]) =>
        url === '/api/campanias/interacciones/5/recordatorio-hecho/' && options?.method === 'POST',
    ),
  ).toBe(true)
})

test('si no se puede marcar como hecho, avisa y deja el recordatorio', async () => {
  mockFetch((url, options) => {
    if (options?.method === 'POST') return fail(400)
    if (url === URL) return ok([vencido])
    return undefined
  })
  render(<RecordatoriosPanel />)
  fireEvent.click(await screen.findByRole('button', { name: 'Hecho' }))
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No se pudo marcar el recordatorio como hecho.',
  )
  expect(screen.getByText('Enviar presupuesto')).toBeDefined()
})

test('el rol de solo lectura ve los recordatorios sin el botón Hecho', async () => {
  mockFetch((url) => (url === URL ? ok([vencido]) : undefined))
  render(
    <PuedeEditarContext.Provider value={false}>
      <RecordatoriosPanel />
    </PuedeEditarContext.Provider>,
  )
  expect(await screen.findByText('Enviar presupuesto')).toBeDefined()
  expect(screen.queryByRole('button', { name: 'Hecho' })).toBeNull()
})

test('sin recordatorios muestra el vacío, y avisa si no se pueden cargar', async () => {
  mockFetch((url) => (url === URL ? ok([]) : undefined))
  render(<RecordatoriosPanel />)
  expect(await screen.findByText('No hay recordatorios para hoy.')).toBeDefined()
  cleanup()
  mockFetch((url) => (url === URL ? fail(500) : undefined))
  render(<RecordatoriosPanel />)
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No se pudieron cargar los recordatorios.',
  )
})
