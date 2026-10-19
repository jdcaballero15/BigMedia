import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import ClienteForm from './ClienteForm'
import type { Cliente } from './types'
import { ApiError } from '../../shared/api'

const cliente: Cliente = {
  id: 5,
  nombre: 'Café Mendoza',
  razon_social: 'Café Mendoza SRL',
  cuit: '20123456786',
  tipo: 'intermediario',
  tipo_nombre: 'Intermediario',
  telefono: '261 555 0000',
  correo: 'hola@cafe.com.ar',
  activo: true,
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

test('envía los datos del cliente nuevo sin espacios sobrantes', async () => {
  const onSave = vi.fn().mockResolvedValue(undefined)
  render(<ClienteForm onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Nombre de fantasía'), {
    target: { value: ' Bodega Sol ' },
  })
  fireEvent.change(screen.getByLabelText('Razón social'), { target: { value: 'Bodega Sol SA' } })
  fireEvent.change(screen.getByLabelText('CUIT'), { target: { value: '20-12345678-6' } })
  fireEvent.change(screen.getByLabelText('Tipo'), { target: { value: 'directo' } })
  fireEvent.change(screen.getByLabelText('Teléfono'), { target: { value: '261 444' } })
  fireEvent.change(screen.getByLabelText('Correo'), { target: { value: 'ventas@sol.com' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar cliente' }))
  await waitFor(() =>
    expect(onSave).toHaveBeenCalledWith({
      nombre: 'Bodega Sol',
      razon_social: 'Bodega Sol SA',
      cuit: '20-12345678-6',
      tipo: 'directo',
      telefono: '261 444',
      correo: 'ventas@sol.com',
      activo: true,
    }),
  )
})

test('avisa que un cliente directo nuevo crea su marca', () => {
  render(<ClienteForm onSave={vi.fn()} onCancel={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Tipo'), { target: { value: 'directo' } })
  expect(screen.getByText(/se crea también una marca con su nombre/)).toBeDefined()
})

test('precarga el cliente al editar y permite inactivarlo', async () => {
  const onSave = vi.fn().mockResolvedValue(undefined)
  render(<ClienteForm cliente={cliente} onSave={onSave} onCancel={vi.fn()} />)
  expect(screen.getByRole('heading', { name: 'Editar cliente' })).toBeDefined()
  expect((screen.getByLabelText('Razón social') as HTMLInputElement).value).toBe('Café Mendoza SRL')
  fireEvent.click(screen.getByLabelText('Activo'))
  fireEvent.click(screen.getByRole('button', { name: 'Guardar cliente' }))
  await waitFor(() =>
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ tipo: 'intermediario', cuit: '20123456786', activo: false }),
    ),
  )
})

test('muestra junto al campo los errores de validación de la API', async () => {
  const onSave = vi.fn().mockRejectedValue(
    new ApiError(400, {
      cuit: ['El CUIT no es válido: revisá el dígito verificador.'],
      razon_social: ['Ingresá la razón social.'],
    }),
  )
  render(<ClienteForm onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('CUIT'), { target: { value: '20123456780' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar cliente' }))
  expect(
    await screen.findByText('El CUIT no es válido: revisá el dígito verificador.'),
  ).toBeDefined()
  expect(screen.getByText('Ingresá la razón social.')).toBeDefined()
  expect(screen.getByRole('alert').textContent).toBe('No se pudo completar la operación.')
})

test('cancelar avisa al contenedor', () => {
  const onCancel = vi.fn()
  render(<ClienteForm onSave={vi.fn()} onCancel={onCancel} />)
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
  expect(onCancel).toHaveBeenCalled()
})
