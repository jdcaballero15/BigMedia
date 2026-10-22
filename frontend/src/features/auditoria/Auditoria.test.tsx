import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import AuditoriaPage from './Auditoria'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const registros = [
  {
    id: 1,
    entidad: 'reserva',
    entidad_id: 5,
    campo: 'fecha_fin',
    valor_anterior: '2026-08-31',
    valor_nuevo: '2026-09-30',
    usuario: 3,
    usuario_nombre: 'operativo',
    origen: 'usuario',
    momento: '2026-10-01T14:30:00Z',
  },
  {
    id: 2,
    entidad: 'reserva',
    entidad_id: 7,
    campo: 'estado',
    valor_anterior: 'pendiente',
    valor_nuevo: 'confirmada',
    usuario: 3,
    usuario_nombre: 'operativo',
    origen: 'usuario',
    momento: '2026-09-15T09:00:00Z',
  },
]

const usuarios = [{ id: 3, nombre: 'operativo' }]

function stubFetch(filas: unknown = registros, usuariosData: unknown = usuarios) {
  const fetchMock = vi.fn(async (input: string) => {
    if (input.includes('/auditoria/usuarios/')) return ok(usuariosData)
    if (input.includes('/auditoria/registros/')) return ok(filas)
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('muestra filas con momento, usuario, entidad, campo y valores', async () => {
  stubFetch()
  render(<AuditoriaPage />)

  // espera las filas (puede haber múltiples "operativo" en select + tabla)
  expect((await screen.findAllByText('operativo')).length).toBeGreaterThan(0)
  expect(screen.getByText('Reserva #5')).toBeDefined()
  expect(screen.getByText('fecha_fin')).toBeDefined()
  expect(screen.getByText('2026-08-31')).toBeDefined()
  expect(screen.getByText('2026-09-30')).toBeDefined()
  // valor null se muestra como —
  expect(screen.getByText('Reserva #7')).toBeDefined()
  expect(screen.getByText('estado')).toBeDefined()
})

test('estado vacío cuando no hay registros', async () => {
  stubFetch([])
  render(<AuditoriaPage />)
  expect(await screen.findByText('Sin cambios registrados para estos filtros.')).toBeDefined()
})

test('elegir un usuario re-pide con usuario=<id>', async () => {
  const fetchMock = stubFetch()
  render(<AuditoriaPage />)

  // espera a que carguen los usuarios en el select
  expect(await screen.findByRole('option', { name: 'operativo' })).toBeDefined()
  fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: '3' } })

  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('usuario=3'))).toBe(true),
  )
})

test('cambiar fecha Desde re-pide con desde=<valor>', async () => {
  const fetchMock = stubFetch()
  render(<AuditoriaPage />)

  await screen.findAllByText('operativo')
  fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-01-01' } })

  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('desde=2026-01-01'))).toBe(
      true,
    ),
  )
})

test('cambiar fecha Hasta re-pide con hasta=<valor>', async () => {
  const fetchMock = stubFetch()
  render(<AuditoriaPage />)

  await screen.findAllByText('operativo')
  fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '2026-12-31' } })

  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('hasta=2026-12-31'))).toBe(
      true,
    ),
  )
})

test('el filtro Entidad incluye las opciones Campaña y Cartel', async () => {
  stubFetch()
  render(<AuditoriaPage />)

  await screen.findAllByText('operativo')
  expect(screen.getByRole('option', { name: 'Campaña' })).toBeDefined()
  expect(screen.getByRole('option', { name: 'Cartel' })).toBeDefined()
})

test('la columna Entidad muestra etiqueta correcta para campania', async () => {
  const registroCampania = [
    {
      id: 10,
      entidad: 'campania',
      entidad_id: 3,
      campo: 'estado',
      valor_anterior: 'cotizada',
      valor_nuevo: 'confirmada',
      usuario: 3,
      usuario_nombre: 'operativo',
      origen: 'usuario',
      momento: '2026-10-10T10:00:00Z',
    },
  ]
  stubFetch(registroCampania)
  render(<AuditoriaPage />)

  expect(await screen.findByText('Campaña #3')).toBeDefined()
})
