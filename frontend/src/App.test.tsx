import { afterEach, expect, test, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

afterEach(() => {
  vi.unstubAllGlobals()
})

test('muestra que la API está disponible cuando responde correctamente', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ status: 'ok' }),
  }))

  render(<App />)

  expect(await screen.findByText('API disponible')).toBeDefined()
  expect(screen.getByRole('heading', { name: 'Big Media' })).toBeDefined()
})

test('muestra que la API no está disponible cuando falla la conexión', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))

  render(<App />)

  expect(await screen.findByText('API no disponible')).toBeDefined()
})
