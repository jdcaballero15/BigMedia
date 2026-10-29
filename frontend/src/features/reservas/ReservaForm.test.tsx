import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import ReservaForm from './ReservaForm'
import { ApiError } from '../../shared/api'
import type { Cartel } from '../inventario/types'

const carteles = [
  {
    id: 7,
    nombre_visible: 'Av. San Martín 1234 · 6x3',
    tarifa_lista: '150000.00',
    formato: 1,
    formato_nombre: 'LED',
    zona: 1,
    zona_nombre: 'Ciudad',
    proveedor: null,
    proveedor_nombre: null,
    estado: 1,
    estado_nombre: 'Activo',
    es_baja: false,
    operativo: true,
    direccion: 'Av. San Martín 1234',
    tamano: '6x3',
    capacidad: 1,
    foto_url: '',
  },
] as unknown as Cartel[]

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

test('precarga el precio de alquiler al elegir el cartel', () => {
  render(<ReservaForm campaniaId={5} carteles={carteles} onSave={vi.fn()} onCancel={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Cartel'), { target: { value: '7' } })
  expect((screen.getByLabelText('Precio de alquiler') as HTMLInputElement).value).toBe('150000.00')
})

test('no envía la reserva si una fecha escrita es inválida', () => {
  const onSave = vi.fn()
  render(<ReservaForm campaniaId={5} carteles={carteles} onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Fecha de inicio'), { target: { value: '31/02/2026' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar reserva' }))
  expect(onSave).not.toHaveBeenCalled()
  expect(screen.getByText('Fecha inválida. Usá dd/mm/aaaa.')).toBeDefined()
})

test('envía la reserva con la campaña fija y los datos cargados', async () => {
  const onSave = vi.fn().mockResolvedValue(undefined)
  render(<ReservaForm campaniaId={5} carteles={carteles} onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Cartel'), { target: { value: '7' } })
  fireEvent.change(screen.getByLabelText('Fecha de inicio'), { target: { value: '01/08/2026' } })
  fireEvent.change(screen.getByLabelText('Fecha de fin'), { target: { value: '31/08/2026' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar reserva' }))
  await waitFor(() =>
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ campania: 5, cartel: 7, fecha_inicio: '2026-08-01' }),
    ),
  )
})

test('muestra el mensaje de conflicto de cupo del servidor', async () => {
  const conflicto =
    'Av. San Martín 1234 · 6x3: sin cupo libre (1 de 1) entre 2026-08-01 y 2026-08-31.'
  const onSave = vi.fn().mockRejectedValue(new ApiError(400, { disponibilidad: [conflicto] }))
  render(<ReservaForm campaniaId={5} carteles={carteles} onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.click(screen.getByRole('button', { name: 'Guardar reserva' }))
  await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('sin cupo libre'))
})

test('muestra el error de campo de la API', async () => {
  const onSave = vi
    .fn()
    .mockRejectedValue(new ApiError(400, { fecha_fin: ['La fecha de fin no puede ser anterior.'] }))
  render(<ReservaForm campaniaId={5} carteles={carteles} onSave={onSave} onCancel={vi.fn()} />)
  fireEvent.click(screen.getByRole('button', { name: 'Guardar reserva' }))
  await waitFor(() =>
    expect(screen.getByText('La fecha de fin no puede ser anterior.')).toBeDefined(),
  )
})

const deBaja = {
  ...carteles[0],
  id: 8,
  nombre_visible: 'Ruta 40 km 10',
  es_baja: true,
  operativo: false,
} as Cartel
const apagado = {
  ...carteles[0],
  id: 9,
  nombre_visible: 'Costanera 500',
  estado_nombre: 'Apagado',
  operativo: false,
} as Cartel

test('no ofrece un cartel fuera de servicio en una reserva nueva', () => {
  render(
    <ReservaForm
      campaniaId={5}
      carteles={[...carteles, apagado]}
      onSave={vi.fn()}
      onCancel={vi.fn()}
    />,
  )
  expect(screen.queryByRole('option', { name: /Costanera 500/ })).toBeNull()
  expect(screen.getByRole('option', { name: /Av. San Martín 1234/ })).toBeDefined()
})

test('muestra el cartel fuera de servicio ya asignado al editar una reserva', () => {
  const reserva = { id: 4, cartel: 9, fecha_inicio: '2026-08-01', fecha_fin: '2026-08-31' }
  render(
    <ReservaForm
      campaniaId={5}
      reserva={reserva as never}
      carteles={[...carteles, apagado]}
      onSave={vi.fn()}
      onCancel={vi.fn()}
    />,
  )
  expect(screen.getByRole('option', { name: 'Costanera 500 (fuera de servicio)' })).toBeDefined()
})

test('no ofrece un cartel de baja en una reserva nueva', () => {
  render(
    <ReservaForm
      campaniaId={5}
      carteles={[...carteles, deBaja]}
      onSave={vi.fn()}
      onCancel={vi.fn()}
    />,
  )
  expect(screen.queryByRole('option', { name: /Ruta 40 km 10/ })).toBeNull()
})

test('muestra el cartel de baja ya asignado al editar una reserva', () => {
  const reserva = { id: 3, cartel: 8, fecha_inicio: '2026-08-01', fecha_fin: '2026-08-31' }
  render(
    <ReservaForm
      campaniaId={5}
      reserva={reserva as never}
      carteles={[...carteles, deBaja]}
      onSave={vi.fn()}
      onCancel={vi.fn()}
    />,
  )
  expect((screen.getByLabelText('Cartel') as HTMLSelectElement).value).toBe('8')
  expect(screen.getByRole('option', { name: 'Ruta 40 km 10 (de baja)' })).toBeDefined()
})

function estadosOfrecidos(): string[] {
  const select = screen.getByLabelText('Estado') as HTMLSelectElement
  return Array.from(select.options).map((opcion) => opcion.textContent ?? '')
}

test('una reserva nueva solo ofrece Pendiente y Confirmada', () => {
  render(<ReservaForm campaniaId={5} carteles={carteles} onSave={vi.fn()} onCancel={vi.fn()} />)
  expect(estadosOfrecidos()).toEqual(['Pendiente', 'Confirmada'])
})

test('al editar una reserva se ofrecen los cuatro estados', () => {
  const reserva = {
    id: 3,
    cartel: 7,
    estado: 'confirmada',
    fecha_inicio: '2026-08-01',
    fecha_fin: '2026-08-31',
  }
  render(
    <ReservaForm
      campaniaId={5}
      reserva={reserva as never}
      carteles={carteles}
      onSave={vi.fn()}
      onCancel={vi.fn()}
    />,
  )
  expect(estadosOfrecidos()).toEqual(['Pendiente', 'Confirmada', 'Finalizada', 'Cancelada'])
})
