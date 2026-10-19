import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import DisponibilidadPage from './DisponibilidadPage'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

function stubFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input.includes('/inventario/zonas/')) return ok([])
      if (input.includes('/inventario/formatos/')) return ok([])
      if (input.includes('/reservas/disponibilidad/')) return ok([])
      if (input.includes('/reservas/calendario/')) return ok({ periodos: [], carteles: [] })
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('arranca en la vista de hoy', async () => {
  stubFetch()
  render(<DisponibilidadPage />)
  expect(await screen.findByRole('heading', { name: 'Ocupación de hoy' })).toBeDefined()
})

test('el conmutador cambia a la vista de calendario', async () => {
  stubFetch()
  render(<DisponibilidadPage />)
  await screen.findByRole('heading', { name: 'Ocupación de hoy' })
  fireEvent.click(screen.getByRole('button', { name: 'Calendario' }))
  expect(await screen.findByRole('heading', { name: 'Calendario a futuro' })).toBeDefined()
})
