import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import UsuariosPage from './UsuariosPage'
import type { Usuario } from './types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const fail = (status: number, data: unknown) => ({ ok: false, status, json: async () => data })

const URL = '/api/usuarios/usuarios/'
const ale: Usuario = {
  id: 2,
  username: 'ale',
  first_name: 'Ale',
  last_name: 'Prueba',
  email: 'ale@ejemplo.test',
  rol: 'operativo',
  es_gerencia: true,
  activo: true,
  tiene_clave: true,
  last_login: null,
}
const admin: Usuario = {
  ...ale,
  id: 1,
  username: 'admin',
  first_name: '',
  last_name: '',
  email: '',
  rol: 'administrador',
  es_gerencia: false,
}

type Route = (url: string, options?: RequestInit) => unknown

function mockFetch(route: Route = () => undefined) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const response = route(input, options)
    if (response !== undefined) return response
    if (input === URL) return ok([admin, ale])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const cuerpos = (fetchMock: ReturnType<typeof mockFetch>, method: string) =>
  fetchMock.mock.calls
    .filter(([, options]) => options?.method === method)
    .map(([url, options]) => [url, JSON.parse(String(options?.body))])

beforeEach(() => {
  vi.spyOn(window, 'confirm').mockReturnValue(true)
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

test('lista usuarios con rol, gerencia, contraseña y estado', async () => {
  mockFetch()
  render(<UsuariosPage />)
  const fila = (await screen.findByRole('cell', { name: 'ale' })).closest('tr') as HTMLElement
  expect(within(fila).getByText('Ale Prueba')).toBeDefined()
  expect(within(fila).getByText('Operativo')).toBeDefined()
  expect(within(fila).getByText('Sí')).toBeDefined()
  expect(within(fila).getByText('Definida')).toBeDefined()
  const filaAdmin = screen.getByRole('cell', { name: 'admin' }).closest('tr') as HTMLElement
  expect(within(filaAdmin).getByText('Administrador')).toBeDefined()
  expect(within(filaAdmin).getAllByText('—')).toHaveLength(2)
})

test('muestra error si no carga la lista', async () => {
  mockFetch((url) => (url === URL ? fail(500, {}) : undefined))
  render(<UsuariosPage />)
  expect(await screen.findByRole('alert')).toHaveProperty(
    'textContent',
    'No se pudieron cargar los usuarios.',
  )
})

test('muestra lista vacía', async () => {
  mockFetch((url) => (url === URL ? ok([]) : undefined))
  render(<UsuariosPage />)
  expect(await screen.findByText('No hay usuarios.')).toBeDefined()
})

test('crea un usuario y muestra su link de contraseña', async () => {
  const nuevo = { ...ale, id: 9, username: 'nuevo', tiene_clave: false }
  const fetchMock = mockFetch((url, options) => {
    if (url === URL && options?.method === 'POST') return ok(nuevo)
    if (url === `${URL}9/link-clave/`) return ok({ link: 'https://app/?definir-clave=OQ.tok' })
    return undefined
  })
  render(<UsuariosPage />)
  await screen.findByRole('cell', { name: 'ale' })
  fireEvent.click(screen.getByRole('button', { name: 'Nuevo usuario' }))
  const form = screen.getByRole('form', { name: 'Formulario de usuario' })
  fireEvent.change(within(form).getByLabelText('Usuario'), { target: { value: ' nuevo ' } })
  fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'Nuevo' } })
  fireEvent.change(within(form).getByLabelText('Correo'), { target: { value: 'n@ejemplo.test' } })
  fireEvent.change(within(form).getByLabelText('Rol'), { target: { value: 'lectura' } })
  fireEvent.click(within(form).getByLabelText(/Gerencia/))
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar' }))

  const link = await screen.findByLabelText('Link')
  expect(link).toHaveProperty('value', 'https://app/?definir-clave=OQ.tok')
  expect(cuerpos(fetchMock, 'POST')[0]).toEqual([
    URL,
    {
      username: 'nuevo',
      first_name: 'Nuevo',
      last_name: '',
      email: 'n@ejemplo.test',
      rol: 'lectura',
      es_gerencia: true,
    },
  ])
  expect(window.confirm).not.toHaveBeenCalled()
})

test('muestra los errores de campo al crear', async () => {
  mockFetch((url, options) =>
    url === URL && options?.method === 'POST'
      ? fail(400, { username: ['Ya existe un usuario con ese nombre.'] })
      : undefined,
  )
  render(<UsuariosPage />)
  await screen.findByRole('cell', { name: 'ale' })
  fireEvent.click(screen.getByRole('button', { name: 'Nuevo usuario' }))
  fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))
  expect(await screen.findByText('Ya existe un usuario con ese nombre.')).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
  expect(screen.queryByRole('form', { name: 'Formulario de usuario' })).toBeNull()
})

test('edita un usuario sin mandar el nombre de usuario', async () => {
  const fetchMock = mockFetch((url, options) =>
    url === `${URL}2/` && options?.method === 'PATCH' ? ok(ale) : undefined,
  )
  render(<UsuariosPage />)
  const fila = (await screen.findByRole('cell', { name: 'ale' })).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Editar' }))
  const form = screen.getByRole('form', { name: 'Formulario de usuario' })
  expect(within(form).queryByLabelText('Usuario')).toBeNull()
  fireEvent.change(within(form).getByLabelText('Apellido'), { target: { value: 'Otro' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar' }))
  await waitFor(() => expect(cuerpos(fetchMock, 'PATCH')).toHaveLength(1))
  expect(cuerpos(fetchMock, 'PATCH')[0]).toEqual([
    `${URL}2/`,
    {
      first_name: 'Ale',
      last_name: 'Otro',
      email: 'ale@ejemplo.test',
      rol: 'operativo',
      es_gerencia: true,
    },
  ])
})

test('inactivar al último administrador muestra el rechazo del servidor', async () => {
  mockFetch((url, options) =>
    url === `${URL}1/` && options?.method === 'PATCH'
      ? fail(400, { detail: 'Tiene que quedar al menos un administrador activo.' })
      : undefined,
  )
  render(<UsuariosPage />)
  const fila = (await screen.findByRole('cell', { name: 'admin' })).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Inactivar' }))
  expect(await screen.findByRole('alert')).toHaveProperty(
    'textContent',
    'Tiene que quedar al menos un administrador activo.',
  )
})

test('reactiva un usuario inactivo', async () => {
  const fetchMock = mockFetch((url, options) => {
    if (url === URL && !options?.method) return ok([{ ...ale, activo: false }])
    if (url === `${URL}2/`) return ok(ale)
    return undefined
  })
  render(<UsuariosPage />)
  fireEvent.click(await screen.findByRole('button', { name: 'Reactivar' }))
  await waitFor(() => expect(cuerpos(fetchMock, 'PATCH')).toEqual([[`${URL}2/`, { activo: true }]]))
})

test('no inactiva si se cancela la confirmación', async () => {
  vi.mocked(window.confirm).mockReturnValue(false)
  const fetchMock = mockFetch()
  render(<UsuariosPage />)
  const fila = (await screen.findByRole('cell', { name: 'ale' })).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Inactivar' }))
  fireEvent.click(within(fila).getByRole('button', { name: 'Restablecer contraseña' }))
  expect(cuerpos(fetchMock, 'PATCH')).toHaveLength(0)
  expect(cuerpos(fetchMock, 'POST')).toHaveLength(0)
})

test('restablece la contraseña, copia el link y lo cierra', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined)
  vi.stubGlobal('navigator', { clipboard: { writeText } })
  mockFetch((url) =>
    url === `${URL}2/link-clave/` ? ok({ link: 'https://app/?definir-clave=Mg.tok' }) : undefined,
  )
  render(<UsuariosPage />)
  const fila = (await screen.findByRole('cell', { name: 'ale' })).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Restablecer contraseña' }))
  expect(window.confirm).toHaveBeenCalled()
  fireEvent.click(await screen.findByRole('button', { name: 'Copiar' }))
  expect(await screen.findByRole('button', { name: 'Copiado' })).toBeDefined()
  expect(writeText).toHaveBeenCalledWith('https://app/?definir-clave=Mg.tok')
  fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }))
  expect(screen.queryByLabelText('Link')).toBeNull()
})

test('si no se puede generar el link, avisa', async () => {
  mockFetch((url) => (url === `${URL}1/link-clave/` ? fail(500, {}) : undefined))
  render(<UsuariosPage />)
  const filaAdmin = (await screen.findByRole('cell', { name: 'admin' })).closest(
    'tr',
  ) as HTMLElement
  fireEvent.click(within(filaAdmin).getByRole('button', { name: 'Restablecer contraseña' }))
  expect(await screen.findByRole('alert')).toHaveProperty(
    'textContent',
    'No se pudo completar la operación.',
  )
})

test('si no se puede copiar, pide copiarlo a mano', async () => {
  vi.stubGlobal('navigator', {})
  mockFetch((url) =>
    url === `${URL}2/link-clave/` ? ok({ link: 'https://app/?definir-clave=Mg.tok' }) : undefined,
  )
  render(<UsuariosPage />)
  const fila = (await screen.findByRole('cell', { name: 'ale' })).closest('tr') as HTMLElement
  fireEvent.click(within(fila).getByRole('button', { name: 'Restablecer contraseña' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Copiar' }))
  expect(await screen.findByRole('alert')).toHaveProperty(
    'textContent',
    'No se pudo copiar: seleccioná el link y copialo a mano.',
  )
})
