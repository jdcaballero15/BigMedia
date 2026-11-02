import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import CalendarioDisponibilidad from './CalendarioDisponibilidad'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const calendario = {
  periodos: [
    { clave: '2026-10', etiqueta: 'Oct 2026' },
    { clave: '2026-11', etiqueta: 'Nov 2026' },
  ],
  carteles: [
    {
      id: 7,
      nombre_visible: 'Av. San Martín 1234 · 6x3',
      formato_nombre: 'LED',
      zona_nombre: 'Ciudad',
      capacidad: 1,
      celdas: [
        { periodo: '2026-10', ocupados: 0 },
        { periodo: '2026-11', ocupados: 1 },
      ],
    },
  ],
}

const reserva = {
  id: 3,
  nombre: 'McDonalds - Av. San Martín 1234 · 6x3 - Nov 2026',
  campania_nombre: 'Verano',
  fecha_inicio: '2026-11-10',
  fecha_fin: '2026-11-20',
}

function stubFetch() {
  const fetchMock = vi.fn(async (input: string) => {
    if (input.includes('/inventario/zonas/')) return ok([{ id: 1, nombre: 'Ciudad' }])
    if (input.includes('/inventario/formatos/')) return ok([{ id: 1, nombre: 'LED' }])
    if (input.includes('/reservas/calendario/')) return ok(calendario)
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

test('muestra la grilla de carteles por mes', async () => {
  stubFetch()
  render(<CalendarioDisponibilidad />)
  expect(await screen.findByText('Av. San Martín 1234 · 6x3')).toBeDefined()
  expect(screen.getByText('Oct 2026')).toBeDefined()
  expect(screen.getByText('Nov 2026')).toBeDefined()
  expect(screen.getByText('1/1')).toBeDefined()
})

test('calendario_celda_muestraLaBarraDeOcupacionYAmbarSiEstaLlena', async () => {
  stubFetch()
  render(<CalendarioDisponibilidad />)
  await screen.findByText('Av. San Martín 1234 · 6x3')

  const llena = screen.getByRole('button', { name: /2026-11: 1 de 1/ })
  expect(llena.className).toBe('celda celda-lleno')
  expect((llena.querySelector('.celda-barra') as HTMLElement).style.width).toBe('100%')
  const libre = screen.getByRole('button', { name: /2026-10: 0 de 1/ }) as HTMLButtonElement
  expect(libre.className).toBe('celda celda-libre')
  expect(libre.disabled).toBe(true)
  expect((libre.querySelector('.celda-barra') as HTMLElement).style.width).toBe('0%')
})

test('tocar una celda ocupada muestra la campaña que la ocupa', async () => {
  const fetchMock = stubFetch()
  render(<CalendarioDisponibilidad />)
  await screen.findByText('Av. San Martín 1234 · 6x3')
  fireEvent.click(screen.getByRole('button', { name: /2026-11: 1 de 1/ }))
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(([url]) => String(url).includes('/reservas/reservas/?cartel=7')),
    ).toBe(true),
  )
  expect(await screen.findByText(/Verano/)).toBeDefined()
})
