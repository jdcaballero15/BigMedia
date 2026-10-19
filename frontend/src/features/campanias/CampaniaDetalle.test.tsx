import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import CampaniaDetalle from './CampaniaDetalle'
import type { Campania } from './types'

const campania: Campania = {
  id: 5,
  nombre: 'Verano 2027',
  marca: 10,
  marca_nombre: 'Axe',
  cliente_facturacion: null,
  cliente_factura: 1,
  cliente_factura_nombre: 'Unilever',
  fecha_inicio: '2027-01-01',
  fecha_fin: '2027-01-31',
  estado: 'confirmada',
}

afterEach(cleanup)

test('muestra el cliente que factura, el estado y las secciones próximas', () => {
  render(<CampaniaDetalle campania={campania} onEditar={vi.fn()} onVolver={vi.fn()} />)
  expect(screen.getByRole('heading', { name: 'Verano 2027' })).toBeDefined()
  expect(screen.getByText('Unilever')).toBeDefined()
  expect(screen.getByText('Confirmada')).toBeDefined()
  expect(screen.getByText('2027-01-01 → 2027-01-31')).toBeDefined()
  expect(screen.getByRole('heading', { name: 'Reservas' })).toBeDefined()
  expect(screen.getByRole('heading', { name: 'Costos y rentabilidad' })).toBeDefined()
})

test('sin fechas muestra el aviso de período', () => {
  render(
    <CampaniaDetalle
      campania={{ ...campania, fecha_inicio: null, fecha_fin: null }}
      onEditar={vi.fn()}
      onVolver={vi.fn()}
    />,
  )
  expect(screen.getByText('Sin fechas planificadas')).toBeDefined()
})
