import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import CartelForm from './CartelForm'
import type { Cartel, Estado, Formato } from './types'
import { ApiError } from '../../shared/api'

const formatos: Formato[] = [
  {
    id: 1,
    nombre: 'Séxtuples',
    modalidad: 'fija',
    capacidad_predeterminada: 6,
    ancho: null,
    alto: null,
  },
  {
    id: 2,
    nombre: 'LED',
    modalidad: 'digital',
    capacidad_predeterminada: 12,
    ancho: null,
    alto: null,
  },
]
const estados: Estado[] = [
  { id: 1, nombre: 'Activo', codigo: 'activo', operativo: true, es_baja: false },
]
const cartel: Cartel = {
  id: 10,
  formato: 1,
  formato_nombre: 'Séxtuples',
  zona: 1,
  zona_nombre: 'Ciudad',
  proveedor: null,
  proveedor_nombre: null,
  estado: 1,
  estado_nombre: 'Activo',
  es_baja: false,
  operativo: true,
  direccion: 'Av. San Martín 1234',
  tamano: '',
  capacidad: 8,
  tarifa_lista: '150000.00',
  foto_url: '',
  nombre_visible: 'Av. San Martín 1234 · 8 slots',
}
const props = {
  formatos,
  zonas: [{ id: 1, nombre: 'Ciudad' }],
  proveedores: [],
  estados,
  onCancel: vi.fn(),
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

test('precarga capacidad al elegir formato en un cartel nuevo', () => {
  render(<CartelForm {...props} onSave={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Formato'), { target: { value: '1' } })
  expect((screen.getByLabelText('Capacidad') as HTMLInputElement).value).toBe('6')
})

test('editar formato no pisa la capacidad ya guardada', () => {
  render(<CartelForm {...props} cartel={cartel} onSave={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Formato'), { target: { value: '2' } })
  expect((screen.getByLabelText('Capacidad') as HTMLInputElement).value).toBe('8')
})

test('conserva una referencia inactiva al editar un cartel', async () => {
  const onSave = vi.fn().mockResolvedValue(undefined)
  render(
    <CartelForm
      {...props}
      cartel={cartel}
      formatos={[{ ...formatos[0], activo: false }, formatos[1]]}
      onSave={onSave}
    />,
  )
  expect(screen.getByRole('option', { name: 'Séxtuples (inactivo)' })).toBeDefined()
  fireEvent.change(screen.getByLabelText('Dirección'), { target: { value: 'Nueva dirección' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar cartel' }))
  await waitFor(() =>
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ formato: 1, direccion: 'Nueva dirección' }),
    ),
  )
})

test('muestra el error de campo devuelto por la API', async () => {
  const onSave = vi
    .fn()
    .mockRejectedValue(new ApiError(400, { direccion: ['Ingresá una dirección.'] }))
  render(<CartelForm {...props} cartel={cartel} onSave={onSave} />)
  fireEvent.click(screen.getByRole('button', { name: 'Guardar cartel' }))
  await waitFor(() => expect(screen.getByText('Ingresá una dirección.')).toBeDefined())
})
