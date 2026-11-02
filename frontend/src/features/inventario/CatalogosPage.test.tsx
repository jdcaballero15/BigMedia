import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import CatalogosPage from './CatalogosPage'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const carteleras = {
  id: 7,
  nombre: 'Carteleras',
  activo: true,
  modalidad: 'fija',
  capacidad_predeterminada: 1,
  ancho: null,
  alto: null,
  por_cantidad: false,
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('marcar un formato como circuito lo manda al guardar', async () => {
  const fetchMock = vi.fn(async (_input: string, options?: RequestInit) =>
    options?.method === 'PATCH' ? ok({ ...carteleras, por_cantidad: true }) : ok([carteleras]),
  )
  vi.stubGlobal('fetch', fetchMock)
  render(<CatalogosPage categorias={['formatos']} />)

  fireEvent.click(await screen.findByRole('button', { name: 'Editar' }))
  const casilla = screen.getByLabelText<HTMLInputElement>('Se carga por cantidad (circuito)')
  expect(casilla.checked).toBe(false)
  fireEvent.click(casilla)
  fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

  await vi.waitFor(() =>
    expect(fetchMock.mock.calls.some(([, options]) => options?.method === 'PATCH')).toBe(true),
  )
  const envio = fetchMock.mock.calls.find(([, options]) => options?.method === 'PATCH')
  expect(envio?.[0]).toBe('/api/inventario/formatos/7/')
  expect(JSON.parse(String(envio?.[1]?.body)).por_cantidad).toBe(true)
})

test('un formato que ya es circuito abre con la casilla marcada', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ok([{ ...carteleras, por_cantidad: true }])),
  )
  render(<CatalogosPage categorias={['formatos']} />)

  fireEvent.click(await screen.findByRole('button', { name: 'Editar' }))

  expect(screen.getByLabelText<HTMLInputElement>('Se carga por cantidad (circuito)').checked).toBe(
    true,
  )
})
