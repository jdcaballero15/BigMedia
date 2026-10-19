import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import DisponibilidadPage from './DisponibilidadPage'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const fila = {
  id: 7,
  nombre_visible: 'Av. San Martín 1234 · 6x3',
  formato_nombre: 'LED',
  zona_nombre: 'Ciudad',
  modalidad: 'digital',
  capacidad: 20,
  ocupados: 12,
  libre: true,
}

function stubFetch() {
  const fetchMock = vi.fn(async (input: string) => {
    if (input.includes('/inventario/zonas/')) return ok([{ id: 1, nombre: 'Ciudad' }])
    if (input.includes('/inventario/formatos/')) return ok([{ id: 1, nombre: 'LED' }])
    if (input.includes('/reservas/disponibilidad/')) return ok([fila])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('lista la ocupación de los carteles', async () => {
  stubFetch()
  render(<DisponibilidadPage />)
  expect(await screen.findByText('Av. San Martín 1234 · 6x3')).toBeDefined()
  expect(screen.getByText('12 de 20')).toBeDefined()
  expect(screen.getByText('Libre')).toBeDefined()
})

test('el acceso rápido Libres agrega el parámetro ocupacion', async () => {
  const fetchMock = stubFetch()
  render(<DisponibilidadPage />)
  await screen.findByText('Av. San Martín 1234 · 6x3')
  fireEvent.click(screen.getByRole('button', { name: 'Libres' }))
  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('ocupacion=libres'))).toBe(
      true,
    ),
  )
})

test('combina el filtro de modalidad en la consulta', async () => {
  const fetchMock = stubFetch()
  render(<DisponibilidadPage />)
  await screen.findByText('Av. San Martín 1234 · 6x3')
  fireEvent.change(screen.getByLabelText('Modalidad'), { target: { value: 'digital' } })
  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('modalidad=digital'))).toBe(
      true,
    ),
  )
})
