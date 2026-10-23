import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import DefinirClave from './DefinirClave'

const fail = (status: number, data: unknown) => ({ ok: false, status, json: async () => data })

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function completar(clave: string, repetida = clave) {
  fireEvent.change(screen.getByLabelText('Contraseña nueva'), { target: { value: clave } })
  fireEvent.change(screen.getByLabelText('Repetila'), { target: { value: repetida } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar contraseña' }))
}

test('no envía si las contraseñas no coinciden', async () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  render(<DefinirClave codigo="MQ.tok" onListo={vi.fn()} />)
  completar('una-clave-larga-1', 'otra')
  expect(await screen.findByRole('alert')).toHaveProperty(
    'textContent',
    'Las contraseñas no coinciden.',
  )
  expect(fetchMock).not.toHaveBeenCalled()
})

test('muestra el error de contraseña débil del servidor', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(fail(400, { clave: ['La contraseña es demasiado corta.'] })),
  )
  const onListo = vi.fn()
  render(<DefinirClave codigo="MQ.tok" onListo={onListo} />)
  completar('123')
  expect(await screen.findByText('La contraseña es demasiado corta.')).toBeDefined()
  expect(onListo).not.toHaveBeenCalled()
})

test('muestra que el link venció', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(fail(400, { token: ['El link no es válido o ya venció.'] })),
  )
  render(<DefinirClave codigo="MQ.tok" onListo={vi.fn()} />)
  completar('una-clave-larga-1')
  expect(await screen.findByRole('alert')).toHaveProperty(
    'textContent',
    'El link no es válido o ya venció.',
  )
})

test('un error de red muestra un mensaje general', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('red')))
  render(<DefinirClave codigo="MQ.tok" onListo={vi.fn()} />)
  completar('una-clave-larga-1')
  expect(await screen.findByRole('alert')).toHaveProperty(
    'textContent',
    'No se pudo definir la contraseña.',
  )
})
