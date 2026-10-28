import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { PuedeEditarContext } from './sesion'
import CartelesPage from '../features/inventario/CartelesPage'
import CatalogosPage from '../features/inventario/CatalogosPage'
import ClientesPage from '../features/clientes/ClientesPage'
import MarcasPage from '../features/clientes/MarcasPage'
import RubrosAdmin from '../features/clientes/RubrosAdmin'
import CampaniasPage from '../features/campanias/CampaniasPage'
import CampaniaDetalle from '../features/campanias/CampaniaDetalle'
import ReservasCampania from '../features/reservas/ReservasCampania'
import CostosReserva from '../features/costos/CostosReserva'
import type { Campania } from '../features/campanias/types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const campania: Campania = {
  id: 1,
  nombre: 'Verano',
  marca: null,
  marca_nombre: null,
  cliente_facturacion: null,
  cliente_factura: null,
  cliente_factura_nombre: '',
  fecha_inicio: null,
  fecha_fin: null,
  estado: 'cotizada',
}

const pantallas: [string, () => ReactNode, string][] = [
  ['carteles', () => <CartelesPage />, 'Nuevo cartel'],
  ['catálogos', () => <CatalogosPage categorias={['zonas']} />, 'Nuevo departamento'],
  ['clientes', () => <ClientesPage />, 'Nuevo cliente'],
  ['marcas', () => <MarcasPage />, 'Nueva marca'],
  ['rubros', () => <RubrosAdmin rubros={[]} onChanged={vi.fn()} />, 'Nuevo rubro'],
  ['campañas', () => <CampaniasPage />, 'Nueva campaña'],
  [
    'detalle de campaña',
    () => <CampaniaDetalle campania={campania} onEditar={vi.fn()} onVolver={vi.fn()} />,
    'Editar',
  ],
  ['reservas', () => <ReservasCampania campaniaId={1} />, 'Nueva reserva'],
  ['costos', () => <CostosReserva reservaId={1} />, 'Agregar costo'],
]

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test.each(pantallas)('%s: Lectura no ve la acción de edición', async (_nombre, pantalla, boton) => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ok([])),
  )

  render(<PuedeEditarContext value={false}>{pantalla()}</PuedeEditarContext>)

  await screen.findAllByRole('heading')
  expect(screen.queryByRole('button', { name: boton })).toBeNull()
})

test.each(pantallas)('%s: Operativo ve la acción de edición', async (_nombre, pantalla, boton) => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ok([])),
  )

  render(<PuedeEditarContext value={true}>{pantalla()}</PuedeEditarContext>)

  expect(await screen.findByRole('button', { name: boton })).toBeDefined()
})

test('clientes: Lectura no ve Editar ni Inactivar en las filas', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) =>
      input.includes('/clientes/clientes/')
        ? ok([{ id: 1, nombre_visible: 'Acme', activo: true, correo: '' }])
        : ok([]),
    ),
  )

  render(
    <PuedeEditarContext value={false}>
      <ClientesPage />
    </PuedeEditarContext>,
  )

  expect(await screen.findByText('Acme')).toBeDefined()
  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Inactivar' })).toBeNull()
  expect(screen.getByRole('button', { name: 'Ver ficha' })).toBeDefined()
})
