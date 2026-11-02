import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import ContactosDelCliente from './ContactosDelCliente'
import { PuedeEditarContext } from '../../shared/sesion'
import type { Cliente, Contacto } from './types'
import { abrirAcciones } from '../../shared/pruebas'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const fail = (status: number, data: unknown) => ({ ok: false, status, json: async () => data })

const URL = '/api/clientes/contactos/'
const LISTA = `${URL}?cliente=4&incluir_inactivos=1`
const central: Cliente = {
  id: 4,
  nombre: 'Central Sur',
  razon_social: '',
  cuit: '',
  tipo: 'intermediario_formal',
  tipo_nombre: 'Intermediario formal',
  nombre_visible: 'Central Sur',
  telefono: '',
  correo: '',
  activo: true,
}
const base = { cliente: 4, cargo: '', correo: '', telefono: '', notas: '' }
const ana: Contacto = {
  ...base,
  id: 1,
  nombre: 'Ana',
  cargo: 'Medios',
  principal: true,
  activo: true,
}
const beto: Contacto = { ...base, id: 2, nombre: 'Beto', principal: false, activo: true }
const caro: Contacto = { ...base, id: 3, nombre: 'Caro', principal: false, activo: false }

type Route = (url: string, options?: RequestInit) => unknown

function mockFetch(route: Route = () => undefined) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const response = route(input, options)
    if (response !== undefined) return response
    if (input === LISTA) return ok([ana, beto, caro])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const escrituras = (fetchMock: ReturnType<typeof mockFetch>) =>
  fetchMock.mock.calls
    .filter(([, options]) => options?.method)
    .map(([url, options]) => [url, options?.method, JSON.parse(String(options?.body))])

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('lista los contactos con su estado', async () => {
  mockFetch()
  render(<ContactosDelCliente cliente={central} />)
  const lista = await screen.findByRole('list', { name: 'Contactos' })
  const filas = within(lista).getAllByRole('listitem')
  expect(within(filas[0]).getByText('Principal')).toBeDefined()
  expect(within(filas[0]).getByText('Medios')).toBeDefined()
  expect(within(filas[0]).getByText('A')).toBeDefined()
  expect(within(filas[1]).getByText('Activo')).toBeDefined()
  expect(within(filas[2]).getByText('Inactivo')).toBeDefined()
  // Solo un activo que no es principal ofrece marcarse como principal.
  filas.forEach(abrirAcciones)
  expect(screen.getAllByRole('button', { name: 'Marcar como principal' })).toHaveLength(1)
  expect(screen.getByRole('button', { name: 'Reactivar' })).toBeDefined()
})

test('da de alta un contacto con el cliente', async () => {
  const fetchMock = mockFetch((url, options) =>
    url === URL && options?.method === 'POST' ? ok({ ...beto, id: 9 }) : undefined,
  )
  render(<ContactosDelCliente cliente={central} />)
  fireEvent.click(await screen.findByRole('button', { name: 'Nuevo contacto' }))
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: ' Dani ' } })
  fireEvent.change(screen.getByLabelText('Cargo o área'), { target: { value: 'Compras' } })
  fireEvent.change(screen.getByLabelText('Notas'), { target: { value: 'Llamar a la tarde' } })
  fireEvent.click(screen.getByLabelText('Contacto principal'))
  fireEvent.click(screen.getByRole('button', { name: 'Guardar contacto' }))

  await waitFor(() => expect(screen.queryByRole('form')).toBeNull())
  expect(escrituras(fetchMock)).toEqual([
    [
      URL,
      'POST',
      {
        nombre: 'Dani',
        cargo: 'Compras',
        correo: '',
        telefono: '',
        notas: 'Llamar a la tarde',
        principal: true,
        cliente: 4,
      },
    ],
  ])
})

test('edita un contacto con PATCH y muestra los errores del servidor', async () => {
  const fetchMock = mockFetch((url, options) =>
    url === `${URL}2/` && options?.method === 'PATCH'
      ? fail(400, { correo: ['Ingresá un correo válido.'] })
      : undefined,
  )
  render(<ContactosDelCliente cliente={central} />)
  const fila = (await screen.findByText('Beto')).closest('li') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Editar' }))
  expect((screen.getByLabelText('Nombre') as HTMLInputElement).value).toBe('Beto')
  fireEvent.change(screen.getByLabelText('Correo'), { target: { value: 'beto' } })
  fireEvent.click(screen.getByRole('button', { name: 'Guardar contacto' }))

  expect(await screen.findByText('Ingresá un correo válido.')).toBeDefined()
  expect(escrituras(fetchMock)[0][2]).toMatchObject({ correo: 'beto' })
})

test('un contacto inactivo no ofrece marcarse como principal al editarlo', async () => {
  mockFetch()
  render(<ContactosDelCliente cliente={central} />)
  const fila = (await screen.findByText('Caro')).closest('li') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Editar' }))
  expect(screen.queryByLabelText('Contacto principal')).toBeNull()
})

test('marca como principal e inactiva con PATCH', async () => {
  const fetchMock = mockFetch((_url, options) =>
    options?.method === 'PATCH' ? ok(beto) : undefined,
  )
  render(<ContactosDelCliente cliente={central} />)
  const filaBeto = (await screen.findByText('Beto')).closest('li') as HTMLElement
  abrirAcciones(filaBeto)
  fireEvent.click(within(filaBeto).getByRole('button', { name: 'Marcar como principal' }))
  const fila = screen.getByText('Ana').closest('li') as HTMLElement
  abrirAcciones(fila)
  fireEvent.click(within(fila).getByRole('button', { name: 'Inactivar' }))

  await waitFor(() => expect(escrituras(fetchMock)).toHaveLength(2))
  expect(escrituras(fetchMock)).toEqual([
    [`${URL}2/`, 'PATCH', { principal: true }],
    [`${URL}1/`, 'PATCH', { activo: false }],
  ])
})

test('informa el error al cambiar un contacto', async () => {
  mockFetch((_url, options) =>
    options?.method === 'PATCH'
      ? fail(400, { detail: 'No se pudo completar la operación.' })
      : undefined,
  )
  render(<ContactosDelCliente cliente={central} />)
  const fila = (await screen.findByText('Beto')).closest('li') as HTMLElement
  abrirAcciones(fila)
  fireEvent.click(within(fila).getByRole('button', { name: 'Marcar como principal' }))
  expect((await screen.findByRole('alert')).textContent).toBe('No se pudo completar la operación.')
})

test('sin contactos lo avisa, y con error de carga lo anuncia', async () => {
  mockFetch((url) => (url === LISTA ? ok([]) : undefined))
  render(<ContactosDelCliente cliente={central} />)
  expect(await screen.findByText('Este cliente todavía no tiene contactos.')).toBeDefined()
  cleanup()

  mockFetch((url) => (url === LISTA ? fail(500, {}) : undefined))
  render(<ContactosDelCliente cliente={central} />)
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No se pudieron cargar los contactos.',
  )
})

test('el rol Lectura ve los contactos pero no los edita', async () => {
  mockFetch()
  render(
    <PuedeEditarContext.Provider value={false}>
      <ContactosDelCliente cliente={central} />
    </PuedeEditarContext.Provider>,
  )
  expect(await screen.findByText('Ana')).toBeDefined()
  expect(screen.queryByRole('button', { name: 'Nuevo contacto' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
})
