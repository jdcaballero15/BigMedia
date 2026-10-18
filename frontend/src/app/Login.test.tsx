import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import Login from './Login'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function completarYEnviar(usuario: string, clave: string) {
  fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: usuario } })
  fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: clave } })
  fireEvent.click(screen.getByRole('button', { name: 'Ingresar' }))
}

test('envía las credenciales y avisa el usuario que ingresó', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValue({ ok: true, status: 200, json: async () => ({ username: 'seba' }) })
  vi.stubGlobal('fetch', fetchMock)
  const onLogin = vi.fn()

  render(<Login onLogin={onLogin} />)
  completarYEnviar('seba', 'clave-de-prueba')

  await waitFor(() => expect(onLogin).toHaveBeenCalledWith('seba'))
  const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
  expect(url).toBe('/api/auth/login/')
  expect(JSON.parse(init.body as string)).toEqual({ username: 'seba', password: 'clave-de-prueba' })
})

test('muestra el error de la API cuando las credenciales son incorrectas', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Usuario o contraseña incorrectos.' }),
    }),
  )
  const onLogin = vi.fn()

  render(<Login onLogin={onLogin} />)
  completarYEnviar('seba', 'mala')

  expect(await screen.findByRole('alert')).toHaveProperty(
    'textContent',
    'Usuario o contraseña incorrectos.',
  )
  expect(onLogin).not.toHaveBeenCalled()
  expect(screen.getByRole('button', { name: 'Ingresar' })).toHaveProperty('disabled', false)
})

test('deshabilita el botón mientras espera la respuesta', async () => {
  let responder: (value: unknown) => void = () => {}
  vi.stubGlobal(
    'fetch',
    vi.fn(
      () =>
        new Promise((resolve) => {
          responder = resolve
        }),
    ),
  )

  render(<Login onLogin={vi.fn()} />)
  completarYEnviar('seba', 'clave-de-prueba')

  const boton = await screen.findByRole('button', { name: 'Ingresando…' })
  expect(boton).toHaveProperty('disabled', true)
  responder({ ok: true, status: 200, json: async () => ({ username: 'seba' }) })
  await screen.findByRole('button', { name: 'Ingresar' })
})
