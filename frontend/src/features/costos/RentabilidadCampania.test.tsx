import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import RentabilidadCampania from './RentabilidadCampania'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('muestra los totales y el margen de la campaña', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      ok({
        cantidad_reservas: 2,
        ingreso: '1500.00',
        costo: '600.00',
        margen: '900.00',
        porcentaje: 60,
      }),
    ),
  )
  render(<RentabilidadCampania campaniaId={5} />)
  expect(await screen.findByText('1500.00')).toBeDefined()
  expect(screen.getByText(/900.00 \(60%\)/)).toBeDefined()
})
