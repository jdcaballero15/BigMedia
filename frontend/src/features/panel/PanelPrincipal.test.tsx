import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
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
  expect(screen.getByText('2026-11-15')).toBeDefined()
})
