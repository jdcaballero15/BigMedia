import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import CampaniaForm from './CampaniaForm'
import { ApiError } from '../../shared/api'
import type { Cliente, Marca, Rubro } from '../clientes/types'

const clientes: Cliente[] = [
  {
    id: 1,
    nombre: 'Unilever',
    razon_social: 'Unilever S.A.',
    cuit: '',
    tipo: 'directo',
    tipo_nombre: 'Directo',
    nombre_visible: 'Unilever',
    telefono: '',
    correo: '',
    activo: true,
  },
]
const marcas: Marca[] = [
  {
    id: 10,
    nombre: 'Axe',
    cliente: 1,
    cliente_nombre: 'Unilever',
    rubro: null,
    rubro_nombre: null,
    activo: true,
  },
]
const rubros: Rubro[] = []

const base = {
  marcas,
  clientes,
  rubros,
  onCancel: vi.fn(),
  onCrearMarca: vi.fn(),
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

test('crea una campaña enviando los campos cargados', async () => {
  const onSave = vi.fn().mockResolvedValue(undefined)
  render(<CampaniaForm {...base} onSave={onSave} onCrearMarca={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Verano 2027' } })
  fireEvent.change(screen.getByLabelText('Marca'), { target: { value: '10' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar campaña' }))
  await waitFor(() =>
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ nombre: 'Verano 2027', marca: 10, estado: 'cotizada' }),
    ),
  )
})

test('envía las fechas escritas como dd/mm/aaaa en formato de la API', async () => {
  const onSave = vi.fn().mockResolvedValue(undefined)
  render(<CampaniaForm {...base} onSave={onSave} onCrearMarca={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Fecha de inicio'), { target: { value: '01/11/2026' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar campaña' }))
  await waitFor(() =>
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ fecha_inicio: '2026-11-01', fecha_fin: null }),
    ),
  )
})

test('no envía la campaña si una fecha escrita es inválida', () => {
  const onSave = vi.fn()
  render(<CampaniaForm {...base} onSave={onSave} onCrearMarca={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Fecha de fin'), { target: { value: '30/11' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar campaña' }))
  expect(onSave).not.toHaveBeenCalled()
  expect(screen.getByText('Fecha inválida. Usá dd/mm/aaaa.')).toBeDefined()
})

test('muestra el error de campo devuelto por la API', async () => {
  const onSave = vi.fn().mockRejectedValue(new ApiError(400, { estado: ['Para confirmar falta.'] }))
  render(<CampaniaForm {...base} onSave={onSave} onCrearMarca={vi.fn()} />)
  fireEvent.click(screen.getByRole('button', { name: 'Guardar campaña' }))
  await waitFor(() => expect(screen.getByText('Para confirmar falta.')).toBeDefined())
})

test('permite crear una marca al vuelo y la deja seleccionada', async () => {
  const onCrearMarca = vi.fn().mockResolvedValue({
    id: 20,
    nombre: 'Rexona',
    cliente: 1,
    cliente_nombre: 'Unilever',
    rubro: null,
    rubro_nombre: null,
    activo: true,
  })
  render(<CampaniaForm {...base} marcas={[]} onSave={vi.fn()} onCrearMarca={onCrearMarca} />)
  fireEvent.click(screen.getByRole('button', { name: 'Nueva marca' }))
  const form = screen.getByRole('form', { name: 'Formulario de marca' })
  fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'Rexona' } })
  fireEvent.change(within(form).getByLabelText('Cliente'), { target: { value: '1' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar marca' }))
  await waitFor(() =>
    expect(onCrearMarca).toHaveBeenCalledWith(expect.objectContaining({ nombre: 'Rexona' })),
  )
  await waitFor(() =>
    expect((screen.getByLabelText('Marca') as HTMLSelectElement).value).toBe('20'),
  )
})
