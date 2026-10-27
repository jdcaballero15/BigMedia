import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import MarcaForm from './MarcaForm'
import type { Cliente, Marca, Rubro } from './types'
import { ApiError } from '../../shared/api'

const base = { razon_social: '', cuit: '', tipo_nombre: 'Intermediario', telefono: '', correo: '' }
const clientes: Cliente[] = [
  {
    ...base,
    id: 1,
    nombre: 'Agencia Andes',
    nombre_visible: 'Agencia Andes',
    tipo: 'intermediario',
    activo: true,
  },
  { ...base, id: 6, nombre: '', nombre_visible: 'Cliente sin nombre #6', tipo: '', activo: true },
  {
    ...base,
    id: 2,
    nombre: 'Agencia Cerrada',
    nombre_visible: 'Agencia Cerrada',
    tipo: 'intermediario',
    activo: false,
  },
]
const rubros: Rubro[] = [
  { id: 3, nombre: 'Bebidas', activo: true },
  { id: 4, nombre: 'Viejo rubro', activo: false },
]
const marca: Marca = {
  id: 9,
  nombre: 'Agua Cumbre',
  cliente: 2,
  cliente_nombre: 'Agencia Cerrada',
  rubro: 4,
  rubro_nombre: 'Viejo rubro',
  activo: true,
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

test('una marca nueva solo ofrece clientes y rubros activos', () => {
  render(<MarcaForm clientes={clientes} rubros={rubros} onSave={vi.fn()} onCancel={vi.fn()} />)
  expect(screen.getByRole('heading', { name: 'Nueva marca' })).toBeDefined()
  expect(screen.getByRole('option', { name: 'Agencia Andes' })).toBeDefined()
  expect(screen.getByRole('option', { name: 'Cliente sin nombre #6' })).toBeDefined()
  expect(screen.queryByRole('option', { name: /Agencia Cerrada/ })).toBeNull()
  expect(screen.queryByRole('option', { name: /Viejo rubro/ })).toBeNull()
})

test('envía la marca nueva con cliente y rubro', async () => {
  const onSave = vi.fn().mockResolvedValue(undefined)
  render(<MarcaForm clientes={clientes} rubros={rubros} onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: ' Vino Alto ' } })
  fireEvent.change(screen.getByLabelText('Cliente'), { target: { value: '1' } })
  fireEvent.change(screen.getByLabelText('Rubro'), { target: { value: '3' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar marca' }))
  await waitFor(() =>
    expect(onSave).toHaveBeenCalledWith({
      nombre: 'Vino Alto',
      cliente: 1,
      rubro: 3,
      activo: true,
    }),
  )
})

test('muestra el mensaje de la API cuando falta el cliente', async () => {
  const onSave = vi
    .fn()
    .mockRejectedValue(new ApiError(400, { cliente: ['Seleccioná un cliente.'] }))
  render(<MarcaForm clientes={clientes} rubros={rubros} onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Sin dueño' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar marca' }))
  expect(await screen.findByText('Seleccioná un cliente.')).toBeDefined()
  expect(onSave).toHaveBeenCalledWith({
    nombre: 'Sin dueño',
    cliente: null,
    rubro: null,
    activo: true,
  })
})

test('al editar conserva el cliente y el rubro inactivos ya asignados', async () => {
  const onSave = vi.fn().mockResolvedValue(undefined)
  const onCancel = vi.fn()
  render(
    <MarcaForm
      marca={marca}
      clientes={clientes}
      rubros={rubros}
      onSave={onSave}
      onCancel={onCancel}
    />,
  )
  expect(screen.getByRole('option', { name: 'Agencia Cerrada (inactivo)' })).toBeDefined()
  expect(screen.getByRole('option', { name: 'Viejo rubro (inactivo)' })).toBeDefined()
  fireEvent.click(screen.getByLabelText('Activa'))
  fireEvent.click(screen.getByRole('button', { name: 'Guardar marca' }))
  await waitFor(() =>
    expect(onSave).toHaveBeenCalledWith({
      nombre: 'Agua Cumbre',
      cliente: 2,
      rubro: 4,
      activo: false,
    }),
  )
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
  expect(onCancel).toHaveBeenCalled()
})

test('avisa la marca parecida y guardar igual reenvía confirmando', async () => {
  const onSave = vi
    .fn()
    .mockRejectedValueOnce(
      new ApiError(400, { posible_duplicado: ['Coca Cola — Agencia Andes (activa)'] }),
    )
    .mockResolvedValueOnce(undefined)
  render(<MarcaForm clientes={clientes} rubros={rubros} onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Coca Kola' } })
  fireEvent.change(screen.getByLabelText('Cliente'), { target: { value: '1' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar marca' }))

  const aviso = await screen.findByRole('alert', { name: 'Posible marca duplicada' })
  expect(aviso.textContent).toContain('Coca Cola — Agencia Andes (activa)')
  expect(screen.queryByText('No se pudo completar la operación.')).toBeNull()

  fireEvent.click(screen.getByRole('button', { name: 'Es otra marca, guardar igual' }))
  await waitFor(() => expect(onSave).toHaveBeenCalledTimes(2))
  expect(onSave).toHaveBeenLastCalledWith({
    nombre: 'Coca Kola',
    cliente: 1,
    rubro: null,
    activo: true,
    confirmar_distinta: true,
  })
  await waitFor(() => expect(screen.queryByRole('alert')).toBeNull())
})

test('cambiar el nombre saca el aviso de marca parecida', async () => {
  const onSave = vi
    .fn()
    .mockRejectedValue(
      new ApiError(400, { posible_duplicado: ['Coca Cola — Agencia Andes (activa)'] }),
    )
  render(<MarcaForm clientes={clientes} rubros={rubros} onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Coca Kola' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar marca' }))
  await screen.findByRole('alert', { name: 'Posible marca duplicada' })
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Pepsi' } })
  expect(screen.queryByRole('alert')).toBeNull()
})
