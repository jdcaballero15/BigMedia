import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import CartelesPage from './CartelesPage'
import { PuedeEditarContext } from '../../shared/sesion'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

const estados = [
  { id: 1, nombre: 'Activo', codigo: 'activo', operativo: true, es_baja: false, activo: true },
  { id: 2, nombre: 'Apagado', codigo: 'apagado', operativo: false, es_baja: false, activo: true },
  { id: 3, nombre: 'De baja', codigo: 'baja', operativo: false, es_baja: true, activo: true },
]
const formatos = [
  { id: 1, nombre: 'LED', modalidad: 'digital', capacidad_predeterminada: 6, activo: true },
]
const zonas = [{ id: 1, nombre: 'Ciudad', activo: true }]
const cartel = {
  id: 9,
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
  direccion: 'Costanera 500',
  tamano: '8x3',
  capacidad: 6,
  tarifa_lista: '1000.00',
  foto_url: '',
  nombre_visible: 'Costanera 500 · 8x3',
}
const vigente = {
  id: 1,
  nombre: 'Marca - Costanera 500 - Nov 2026',
  campania: 5,
  campania_nombre: 'Verano',
  cartel: 9,
  cartel_nombre: 'Costanera 500 · 8x3',
  fecha_inicio: '2026-11-01',
  fecha_fin: '2026-11-30',
  estado: 'confirmada',
}

function stubFetch(vigentes: unknown[], guardado: typeof cartel = cartel) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    if (options?.method === 'PATCH') return ok(guardado)
    if (input.includes('/inventario/estados/')) return ok(estados)
    if (input.includes('/inventario/formatos/')) return ok(formatos)
    if (input.includes('/inventario/zonas/')) return ok(zonas)
    if (input.includes('/inventario/proveedores/')) return ok([])
    if (input.includes('/inventario/carteles/')) return ok([guardado])
    if (input.includes('vigentes=1')) return ok(vigentes)
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

async function guardarConEstado(estadoId: string) {
  render(
    <PuedeEditarContext.Provider value={true}>
      <CartelesPage />
    </PuedeEditarContext.Provider>,
  )
  await screen.findByText('Costanera 500 · 8x3')
  await waitFor(() => expect(screen.getAllByRole('option', { name: 'Apagado' })).toHaveLength(1))
  await editarConEstado(estadoId)
}

async function editarConEstado(estadoId: string) {
  fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
  const formulario = screen.getByRole('form', { name: 'Formulario de cartel' })
  fireEvent.change(within(formulario).getByLabelText('Estado'), { target: { value: estadoId } })
  fireEvent.click(within(formulario).getByRole('button', { name: 'Guardar cartel' }))
  await waitFor(() => expect(screen.queryByRole('form')).toBeNull())
}

const consultasVigentes = (fetchMock: ReturnType<typeof stubFetch>) =>
  fetchMock.mock.calls.filter(([url]) => String(url).includes('vigentes=1'))

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('al pasar un cartel a fuera de servicio muestra sus reservas activas', async () => {
  const fetchMock = stubFetch([vigente])
  await guardarConEstado('2')
  const aviso = await screen.findByRole('alertdialog')
  expect(aviso.textContent).toContain('Costanera 500 · 8x3 quedó en «Apagado»')
  expect(aviso.textContent).toContain('Verano')
  expect(String(consultasVigentes(fetchMock)[0]?.[0])).toContain('cartel=9&vigentes=1')
})

test('sin reservas activas avisa que no hay ninguna', async () => {
  const fetchMock = stubFetch([])
  await guardarConEstado('2')
  await waitFor(() => expect(consultasVigentes(fetchMock)).toHaveLength(1))
  expect(screen.queryByRole('alertdialog')).toBeNull()
  expect((await screen.findByText(/no tiene reservas activas/)).textContent).toContain('Apagado')
})

test('cada cambio a fuera de servicio vuelve a consultar las reservas', async () => {
  const fetchMock = stubFetch([])
  await guardarConEstado('2')
  await screen.findByText(/no tiene reservas activas/)
  await editarConEstado('2')
  await waitFor(() => expect(consultasVigentes(fetchMock)).toHaveLength(2))
})

test('si el estado no cambió no consulta las reservas', async () => {
  const apagado = { ...cartel, estado: 2, estado_nombre: 'Apagado', operativo: false }
  const fetchMock = stubFetch([vigente], apagado)
  await guardarConEstado('2')
  expect(consultasVigentes(fetchMock)).toHaveLength(0)
  expect(screen.queryByRole('alertdialog')).toBeNull()
})

test('a un estado operativo no consulta las reservas', async () => {
  const fetchMock = stubFetch([vigente])
  await guardarConEstado('1')
  expect(consultasVigentes(fetchMock)).toHaveLength(0)
  expect(screen.queryByRole('alertdialog')).toBeNull()
})
