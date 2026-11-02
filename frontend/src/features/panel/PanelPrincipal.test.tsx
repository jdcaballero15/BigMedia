import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, render, screen, within } from '@testing-library/react'
import PanelPrincipal from './PanelPrincipal'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('muestra los contadores y las reservas por vencer', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      ok({
        carteles_libres: 3,
        carteles_ocupados: 2,
        campanias_activas: 4,
        por_vencer: [
          {
            id: 1,
            nombre: 'McDonalds - Centro - Nov 2026',
            cartel_nombre: 'Centro',
            campania: 9,
            fecha_inicio: '2026-11-01',
            fecha_fin: '2026-11-15',
          },
        ],
      }),
    ),
  )
  render(<PanelPrincipal />)
  expect(await screen.findByText('McDonalds - Centro - Nov 2026')).toBeDefined()
  expect(screen.getByText('4')).toBeDefined()
  expect(screen.getByText('15/11/2026')).toBeDefined()
})

test('panel_cifras_salenDeLaApiConElPorcentajeDeOcupacion', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValue(
        ok({ carteles_libres: 3, carteles_ocupados: 1, campanias_activas: 7, por_vencer: [] }),
      ),
  )
  render(<PanelPrincipal />)

  const fila = await screen.findByLabelText('Estado de hoy')
  expect(within(fila).getByText('Carteles libres').parentElement?.className).toBe(
    'cifra cifra-principal',
  )
  expect(within(fila).getByText('25 % de ocupación')).toBeDefined()
  expect(within(fila).getByText('7')).toBeDefined()
  expect(within(fila).getByText('Por vencer').parentElement?.className).toBe('cifra cifra-alerta')
  expect(screen.getByText('Nada por vencer.')).toBeDefined()
})

test('panel_reservaQueVenceHoy_llevaLaEtiquetaSoloEsa', async () => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 9, 28, 9, 0))
  const reserva = { campania: 1, cartel_nombre: 'Centro', fecha_inicio: '2026-10-01' }
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      ok({
        carteles_libres: 0,
        carteles_ocupados: 0,
        campanias_activas: 0,
        por_vencer: [
          { ...reserva, id: 1, nombre: 'Vence hoy SA', fecha_fin: '2026-10-28' },
          { ...reserva, id: 2, nombre: 'Vence mañana SA', fecha_fin: '2026-10-29' },
        ],
      }),
    ),
  )
  try {
    render(<PanelPrincipal />)

    const hoy = (await screen.findByText('Vence hoy SA')).closest('li') as HTMLElement
    const manana = screen.getByText('Vence mañana SA').closest('li') as HTMLElement
    expect(within(hoy).getByText('Vence hoy')).toBeDefined()
    expect(within(manana).queryByText('Vence hoy')).toBeNull()
    expect(
      within(screen.getByLabelText('Estado de hoy')).getByText('0 % de ocupación'),
    ).toBeDefined()
  } finally {
    vi.useRealTimers()
  }
})
