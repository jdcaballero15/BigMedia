import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

test('pide iniciar sesión cuando no hay usuario', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: false, status: 401, json: async () => ({ detail: 'Iniciá sesión.' }),
  }))

  render(<App />)

  expect(await screen.findByRole('heading', { name: 'Ingresar' })).toBeDefined()
  expect(screen.getByLabelText('Usuario')).toBeDefined()
})

test('muestra carteles después de reconocer la sesión', async () => {
  vi.stubGlobal('fetch', vi.fn(async (input: string) => {
    if (input === '/api/auth/me/') return ok({ username: 'seba' })
    if (input.includes('/carteles/')) return ok([{
      id: 11, nombre_visible: 'Av. San Martín 1234 · 6 slots',
      formato_nombre: 'Séxtuples', zona_nombre: 'Ciudad', estado_nombre: 'Activo',
      capacidad: 6, tarifa_lista: '150000.00',
    }])
    if (input.includes('/formatos/')) return ok([{ id: 1, nombre: 'Séxtuples' }])
    if (input.includes('/zonas/')) return ok([{ id: 1, nombre: 'Ciudad' }])
    if (input.includes('/estados/')) return ok([{ id: 1, nombre: 'Activo' }])
    if (input.includes('/proveedores/')) return ok([])
    throw new Error(`URL inesperada: ${input}`)
  }))

  render(<App />)

  expect(await screen.findByRole('heading', { name: 'Carteles' })).toBeDefined()
  expect(await screen.findByText('Av. San Martín 1234 · 6 slots')).toBeDefined()
  expect(screen.getByText('150000.00')).toBeDefined()
})

test('combina filtros de zona y formato en la consulta', async () => {
  const fetchMock = vi.fn(async (input: string) => {
    if (input === '/api/auth/me/') return ok({ username: 'ale' })
    if (input.includes('/carteles/')) return ok([])
    if (input.includes('/formatos/')) return ok([{ id: 2, nombre: 'LED' }])
    if (input.includes('/zonas/')) return ok([{ id: 1, nombre: 'Ciudad' }])
    if (input.includes('/estados/')) return ok([])
    if (input.includes('/proveedores/')) return ok([])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)

  render(<App />)
  await screen.findByRole('heading', { name: 'Carteles' })
  await screen.findByRole('option', { name: 'Ciudad' })
  fireEvent.change(screen.getByLabelText('Zona'), { target: { value: '1' } })
  fireEvent.change(screen.getByLabelText('Formato'), { target: { value: '2' } })

  await waitFor(() => {
    expect(fetchMock.mock.calls.some(([url]) =>
      String(url).includes('zona=1') && String(url).includes('formato=2')
    )).toBe(true)
  })
})
