import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import InteraccionForm from './InteraccionForm'
import { ApiError } from '../../shared/api'
import type { Cliente, Contacto } from '../clientes/types'
import type { Interaccion } from './types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

function cliente(id: number, nombre: string, tipo: Cliente['tipo'], activo = true): Cliente {
  return {
    id,
    nombre,
    razon_social: '',
    cuit: '',
    tipo,
    tipo_nombre: '',
    nombre_visible: nombre,
    telefono: '',
    correo: '',
    activo,
  }
}

const central = cliente(1, 'Central Sur', 'intermediario_formal')
const directo = cliente(2, 'Bodega Norte', 'directo')
const inactivo = cliente(3, 'Cliente Dormido', 'directo', false)
const clientes = [central, directo, inactivo]

const ana: Contacto = {
  id: 11,
  cliente: 1,
  nombre: 'Ana Prueba',
  cargo: '',
  correo: '',
  telefono: '',
  notas: '',
  principal: true,
  activo: true,
}

function mockFetch() {
  const fetchMock = vi.fn(async (input: string) => {
    if (input === '/api/clientes/contactos/?cliente=1') return ok([ana])
    if (input === '/api/campanias/campanias/?cliente=1')
      return ok([{ id: 21, nombre: 'Verano 2027' }])
    if (input.startsWith('/api/campanias/campanias/?cliente=')) return ok([])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function formulario() {
  return screen.getByRole('form', { name: 'Formulario de interacción' })
}

test('una interacción nueva propone Llamada y la fecha de hoy, y no ofrece clientes inactivos', () => {
  mockFetch()
  render(<InteraccionForm clientes={clientes} onSave={vi.fn()} onCancel={vi.fn()} />)
  expect((screen.getByLabelText('Tipo') as HTMLSelectElement).value).toBe('llamada')
  expect((screen.getByLabelText('Fecha') as HTMLInputElement).value).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  expect(screen.queryByRole('option', { name: /Cliente Dormido/ })).toBeNull()
  expect(screen.queryByLabelText('Contacto')).toBeNull()
})

test('con un intermediario formal ofrece sus contactos activos y sus campañas, y envía todo', async () => {
  mockFetch()
  const onSave = vi.fn().mockResolvedValue(undefined)
  render(<InteraccionForm clientes={clientes} onSave={onSave} onCancel={vi.fn()} />)

  fireEvent.change(screen.getByLabelText('Cliente'), { target: { value: '1' } })
  fireEvent.change(screen.getByLabelText('Tipo'), { target: { value: 'reunion' } })
  fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: '2026-10-20' } })
  fireEvent.change(screen.getByLabelText('Asunto'), { target: { value: '  Renovación  ' } })
  fireEvent.change(screen.getByLabelText('Notas'), { target: { value: 'Pidió cotizar.' } })
  expect(await screen.findByRole('option', { name: 'Ana Prueba' })).toBeDefined()
  expect(await screen.findByRole('option', { name: 'Verano 2027' })).toBeDefined()
  fireEvent.change(screen.getByLabelText('Contacto'), { target: { value: '11' } })
  fireEvent.change(screen.getByLabelText('Campaña (opcional)'), { target: { value: '21' } })
  fireEvent.click(within(formulario()).getByRole('button', { name: 'Guardar interacción' }))

  await waitFor(() =>
    expect(onSave).toHaveBeenCalledWith({
      tipo: 'reunion',
      asunto: 'Renovación',
      fecha: '2026-10-20',
      notas: 'Pidió cotizar.',
      cliente: 1,
      contacto: 11,
      campania: 21,
    }),
  )
})

test('un cliente directo no ofrece contactos y cambiar de cliente limpia la campaña', async () => {
  mockFetch()
  const onSave = vi.fn().mockResolvedValue(undefined)
  render(<InteraccionForm clientes={clientes} onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Cliente'), { target: { value: '1' } })
  fireEvent.change(await screen.findByLabelText('Campaña (opcional)'), {
    target: { value: '21' },
  })
  await screen.findByRole('option', { name: 'Verano 2027' })
  fireEvent.change(screen.getByLabelText('Cliente'), { target: { value: '2' } })
  expect(screen.queryByLabelText('Contacto')).toBeNull()
  fireEvent.change(screen.getByLabelText('Asunto'), { target: { value: 'Llamado' } })
  fireEvent.click(within(formulario()).getByRole('button', { name: 'Guardar interacción' }))
  await waitFor(() =>
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ cliente: 2, contacto: null, campania: null }),
    ),
  )
})

test('al editar conserva el contacto inactivado y la campaña que ya tenía', async () => {
  mockFetch()
  const interaccion: Interaccion = {
    id: 5,
    tipo: 'llamada',
    asunto: 'Seguimiento',
    fecha: '2026-09-01',
    notas: '',
    cliente: 1,
    cliente_nombre: 'Central Sur',
    contacto: 12,
    contacto_nombre: 'Beto Prueba',
    campania: 22,
    campania_nombre: 'Invierno 2026',
    registrada_por_nombre: 'operativo',
  }
  render(
    <InteraccionForm
      interaccion={interaccion}
      clientes={clientes}
      onSave={vi.fn()}
      onCancel={vi.fn()}
    />,
  )
  expect(screen.getByRole('heading', { name: 'Editar interacción' })).toBeDefined()
  expect(await screen.findByRole('option', { name: 'Beto Prueba (inactivo)' })).toBeDefined()
  expect(screen.getByRole('option', { name: 'Ana Prueba' })).toBeDefined()
  expect((screen.getByLabelText('Contacto') as HTMLSelectElement).value).toBe('12')
  expect((screen.getByLabelText('Campaña (opcional)') as HTMLSelectElement).value).toBe('22')
})

test('muestra los errores de campo y el mensaje de la API', async () => {
  mockFetch()
  const onSave = vi
    .fn()
    .mockRejectedValue(new ApiError(400, { asunto: ['Este campo no puede estar en blanco.'] }))
  render(<InteraccionForm clientes={clientes} onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.click(within(formulario()).getByRole('button', { name: 'Guardar interacción' }))
  expect(await screen.findByText('Este campo no puede estar en blanco.')).toBeDefined()
  expect(screen.getByRole('alert').textContent).toBe('No se pudo completar la operación.')
})

test('cancelar avisa al padre', () => {
  mockFetch()
  const onCancel = vi.fn()
  render(<InteraccionForm clientes={clientes} onSave={vi.fn()} onCancel={onCancel} />)
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
  expect(onCancel).toHaveBeenCalled()
})
