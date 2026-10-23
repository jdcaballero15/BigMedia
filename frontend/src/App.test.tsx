import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import App from './App'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

async function irA(nombre: string) {
  const nav = await screen.findByRole('navigation', { name: 'Navegación' })
  fireEvent.click(within(nav).getByRole('button', { name: nombre }))
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('pide iniciar sesión cuando no hay usuario', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Iniciá sesión.' }),
    }),
  )

  render(<App />)

  expect(await screen.findByRole('heading', { name: 'Ingresar' })).toBeDefined()
  expect(screen.getByLabelText('Usuario')).toBeDefined()
})

test('muestra carteles después de reconocer la sesión', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'seba' })
      if (input.startsWith('/api/clientes/')) return ok([])
      if (input.includes('/carteles/'))
        return ok([
          {
            id: 11,
            nombre_visible: 'Av. San Martín 1234 · 6 slots',
            formato_nombre: 'Séxtuples',
            zona_nombre: 'Ciudad',
            estado_nombre: 'Activo',
            proveedor_nombre: 'Vía Pública Norte',
            capacidad: 6,
            tarifa_lista: '150000.00',
          },
        ])
      if (input.includes('/formatos/')) return ok([{ id: 1, nombre: 'Séxtuples' }])
      if (input.includes('/zonas/')) return ok([{ id: 1, nombre: 'Ciudad' }])
      if (input.includes('/estados/')) return ok([{ id: 1, nombre: 'Activo' }])
      if (input.includes('/proveedores/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )

  render(<App />)
  await irA('Carteles')

  expect(await screen.findByRole('heading', { name: 'Carteles' })).toBeDefined()
  expect(await screen.findByText('Av. San Martín 1234 · 6 slots')).toBeDefined()
  expect(screen.getByText('150000.00')).toBeDefined()
  expect(screen.getByText('Vía Pública Norte')).toBeDefined()
})

test('combina filtros de zona, formato y modalidad en la consulta', async () => {
  const fetchMock = vi.fn(async (input: string) => {
    if (input === '/api/auth/me/') return ok({ username: 'ale' })
    if (input.startsWith('/api/clientes/')) return ok([])
    if (input.includes('/carteles/')) return ok([])
    if (input.includes('/formatos/')) return ok([{ id: 2, nombre: 'LED' }])
    if (input.includes('/zonas/')) return ok([{ id: 1, nombre: 'Ciudad' }])
    if (input.includes('/estados/')) return ok([])
    if (input.includes('/proveedores/')) return ok([])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)

  render(<App />)
  await irA('Carteles')
  await screen.findByRole('heading', { name: 'Carteles' })
  await screen.findByRole('option', { name: 'Ciudad' })
  fireEvent.change(screen.getByLabelText('Zona'), { target: { value: '1' } })
  fireEvent.change(screen.getByLabelText('Formato'), { target: { value: '2' } })
  fireEvent.change(screen.getByLabelText('Modalidad'), { target: { value: 'digital' } })

  await waitFor(() => {
    expect(
      fetchMock.mock.calls.some(
        ([url]) =>
          String(url).includes('zona=1') &&
          String(url).includes('formato=2') &&
          String(url).includes('modalidad=digital'),
      ),
    ).toBe(true)
  })
})

test('crea un cartel desde la pantalla y envía la capacidad del formato', async () => {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    if (input === '/api/auth/me/') return ok({ username: 'seba' })
    if (input.startsWith('/api/clientes/')) return ok([])
    if (input.includes('/formatos/'))
      return ok([{ id: 1, nombre: 'Séxtuples', capacidad_predeterminada: 6 }])
    if (input.includes('/zonas/')) return ok([{ id: 1, nombre: 'Ciudad' }])
    if (input.includes('/estados/')) return ok([{ id: 1, codigo: 'activo', nombre: 'Activo' }])
    if (input.includes('/proveedores/')) return ok([])
    if (input.includes('/carteles/') && options?.method === 'POST') return ok({ id: 1 })
    if (input.includes('/carteles/')) return ok([])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)
  await irA('Carteles')

  await screen.findByRole('button', { name: 'Nuevo cartel' })
  fireEvent.click(screen.getByRole('button', { name: 'Nuevo cartel' }))
  const form = screen.getByRole('form', { name: 'Formulario de cartel' })
  await within(form).findByRole('option', { name: 'Séxtuples' })
  fireEvent.change(within(form).getByLabelText('Formato'), { target: { value: '1' } })
  fireEvent.change(within(form).getByLabelText('Zona'), { target: { value: '1' } })
  fireEvent.change(within(form).getByLabelText('Dirección'), {
    target: { value: 'Av. Libertador 100' },
  })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar cartel' }))

  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          String(url) === '/api/inventario/carteles/' &&
          options?.method === 'POST' &&
          JSON.parse(String(options.body)).capacidad === 6,
      ),
    ).toBe(true),
  )
})

test('crea un proveedor desde su pantalla sin borrar el histórico', async () => {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    if (input === '/api/auth/me/') return ok({ username: 'ale' })
    if (input.startsWith('/api/clientes/')) return ok([])
    if (input.includes('/carteles/')) return ok([])
    if (input.includes('/formatos/')) return ok([])
    if (input.includes('/zonas/')) return ok([])
    if (input.includes('/estados/')) return ok([])
    if (input.includes('/proveedores/') && options?.method === 'POST') return ok({ id: 4 })
    if (input.includes('/proveedores/')) return ok([])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)

  await irA('Proveedores')
  fireEvent.click(screen.getByRole('button', { name: 'Nuevo proveedor' }))
  const form = screen.getByRole('form', { name: 'Formulario de catálogo' })
  fireEvent.change(within(form).getByLabelText('Nombre'), { target: { value: 'Proveedor Norte' } })
  fireEvent.click(within(form).getByRole('button', { name: 'Guardar' }))

  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          String(url) === '/api/inventario/proveedores/' &&
          options?.method === 'POST' &&
          JSON.parse(String(options.body)).nombre === 'Proveedor Norte',
      ),
    ).toBe(true),
  )
})

test('inactiva un proveedor conservando su registro', async () => {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    if (input === '/api/auth/me/') return ok({ username: 'ale' })
    if (input.startsWith('/api/clientes/')) return ok([])
    if (input.includes('/carteles/')) return ok([])
    if (input.includes('/formatos/')) return ok([])
    if (input.includes('/zonas/')) return ok([])
    if (input.includes('/estados/')) return ok([])
    if (input.includes('/proveedores/7/') && options?.method === 'PATCH')
      return ok({ id: 7, nombre: 'Norte', activo: false })
    if (input.includes('/proveedores/')) return ok([{ id: 7, nombre: 'Norte', activo: true }])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  vi.stubGlobal('confirm', () => true)
  render(<App />)

  await irA('Proveedores')
  await screen.findByText('Norte')
  fireEvent.click(screen.getByRole('button', { name: 'Inactivar' }))

  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          String(url) === '/api/inventario/proveedores/7/' &&
          options?.method === 'PATCH' &&
          JSON.parse(String(options.body)).activo === false,
      ),
    ).toBe(true),
  )
})

test('da de baja un cartel y permite consultar las bajas', async () => {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    if (input === '/api/auth/me/') return ok({ username: 'seba' })
    if (input.startsWith('/api/clientes/')) return ok([])
    if (input.includes('/formatos/')) return ok([])
    if (input.includes('/zonas/')) return ok([])
    if (input.includes('/proveedores/')) return ok([])
    if (input.includes('/estados/'))
      return ok([
        { id: 1, nombre: 'Activo', es_baja: false },
        { id: 3, nombre: 'De baja', es_baja: true },
      ])
    if (input.includes('/carteles/11/') && options?.method === 'PATCH')
      return ok({ id: 11, estado: 3 })
    if (input.includes('/carteles/'))
      return ok([
        {
          id: 11,
          nombre_visible: 'San Martín 1234',
          formato_nombre: 'PPL',
          zona_nombre: 'Ciudad',
          proveedor_nombre: null,
          estado_nombre: 'Activo',
          estado: 1,
          capacidad: 1,
          tarifa_lista: null,
        },
      ])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  vi.stubGlobal('confirm', () => true)
  render(<App />)
  await irA('Carteles')

  await screen.findByText('San Martín 1234')
  await screen.findByRole('option', { name: 'De baja' })
  fireEvent.click(screen.getByRole('button', { name: 'Dar de baja' }))
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(
        ([url, options]) =>
          String(url) === '/api/inventario/carteles/11/' &&
          options?.method === 'PATCH' &&
          JSON.parse(String(options.body)).estado === 3,
      ),
    ).toBe(true),
  )
  fireEvent.click(screen.getByLabelText('Incluir bajas'))
  await waitFor(() =>
    expect(
      fetchMock.mock.calls.some(([url]) => String(url).includes('/carteles/?incluir_bajas=1')),
    ).toBe(true),
  )
})

test('navega a las pantallas de clientes y marcas', async () => {
  const fetchMock = vi.fn(async (input: string) => {
    if (input === '/api/auth/me/') return ok({ username: 'ale' })
    if (input.startsWith('/api/inventario/')) return ok([])
    if (input.startsWith('/api/clientes/')) return ok([])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)

  const nav = await screen.findByRole('navigation', { name: 'Navegación' })
  fireEvent.click(within(nav).getByRole('button', { name: 'Clientes' }))
  expect(await screen.findByRole('heading', { name: 'Clientes' })).toBeDefined()
  expect(within(nav).getByRole('button', { name: 'Clientes' }).className).toBe('active')
  fireEvent.click(within(nav).getByRole('button', { name: 'Marcas' }))
  expect(await screen.findByRole('heading', { name: 'Marcas' })).toBeDefined()
  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([url]) => String(url) === '/api/clientes/marcas/')).toBe(
      true,
    ),
  )
})

test('agrupa el menú lateral en secciones y abre en clientes', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'ale' })
      if (input.startsWith('/api/clientes/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
  render(<App />)

  const nav = await screen.findByRole('navigation', { name: 'Navegación' })
  for (const titulo of ['Comercial', 'Inventario', 'Operación', 'Configuración'])
    expect(within(nav).getByText(titulo)).toBeDefined()
  expect(within(nav).getByRole('button', { name: 'Clientes' }).getAttribute('aria-current')).toBe(
    'page',
  )
  expect(await screen.findByRole('heading', { name: 'Clientes' })).toBeDefined()
})

test('catálogos ya no ofrece proveedores ni formatos, que tienen su pantalla', async () => {
  const fetchMock = vi.fn(async (input: string) => {
    if (input === '/api/auth/me/') return ok({ username: 'ale' })
    if (input.startsWith('/api/clientes/')) return ok([])
    if (input.startsWith('/api/inventario/formatos/'))
      return ok([{ id: 2, nombre: 'LED', activo: true }])
    if (input.startsWith('/api/inventario/')) return ok([])
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  render(<App />)

  await irA('Catálogos')
  expect(await screen.findByRole('heading', { name: 'Catálogos' })).toBeDefined()
  const main = screen.getByRole('main')
  expect(within(main).getByRole('button', { name: 'Departamentos' })).toBeDefined()
  expect(within(main).getByRole('button', { name: 'Estados físicos' })).toBeDefined()
  expect(within(main).queryByRole('button', { name: 'Proveedores' })).toBeNull()
  expect(within(main).queryByRole('button', { name: 'Formatos' })).toBeNull()

  await irA('Formatos')
  expect(await screen.findByRole('heading', { name: 'Formatos' })).toBeDefined()
  expect(await screen.findByText('LED')).toBeDefined()
  expect(screen.getByRole('button', { name: 'Nuevo formato' })).toBeDefined()
})

test('oculta Ingresos a quien no es gerencia', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'trabajador', es_gerencia: false })
      if (input.startsWith('/api/clientes/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
  render(<App />)
  const nav = await screen.findByRole('navigation', { name: 'Navegación' })
  expect(within(nav).getByRole('button', { name: 'Ocupación' })).toBeDefined()
  expect(within(nav).queryByRole('button', { name: 'Ingresos' })).toBeNull()
})

test('muestra Ingresos a gerencia', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'seba', es_gerencia: true })
      if (input.startsWith('/api/clientes/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
  render(<App />)
  const nav = await screen.findByRole('navigation', { name: 'Navegación' })
  expect(within(nav).getByRole('button', { name: 'Ingresos' })).toBeDefined()
})

test('oculta Por rubro a quien no es gerencia', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'trabajador', es_gerencia: false })
      if (input.startsWith('/api/clientes/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
  render(<App />)
  const nav = await screen.findByRole('navigation', { name: 'Navegación' })
  expect(within(nav).getByRole('button', { name: 'Ocupación' })).toBeDefined()
  expect(within(nav).queryByRole('button', { name: 'Por rubro' })).toBeNull()
})

test('muestra Por rubro a gerencia', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'seba', es_gerencia: true })
      if (input.startsWith('/api/clientes/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
  render(<App />)
  const nav = await screen.findByRole('navigation', { name: 'Navegación' })
  expect(within(nav).getByRole('button', { name: 'Por rubro' })).toBeDefined()
})

test('oculta Auditoría a quien no es gerencia', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'trabajador', es_gerencia: false })
      if (input.startsWith('/api/clientes/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
  render(<App />)
  const nav = await screen.findByRole('navigation', { name: 'Navegación' })
  expect(within(nav).queryByRole('button', { name: 'Auditoría' })).toBeNull()
})

test('muestra Auditoría a gerencia', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'seba', es_gerencia: true })
      if (input.startsWith('/api/clientes/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
  render(<App />)
  const nav = await screen.findByRole('navigation', { name: 'Navegación' })
  expect(within(nav).getByRole('button', { name: 'Auditoría' })).toBeDefined()
})

test('abre y cierra el menú en pantallas chicas', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'ale' })
      if (input.startsWith('/api/clientes/')) return ok([])
      if (input.startsWith('/api/inventario/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
  const { container } = render(<App />)

  fireEvent.click(await screen.findByRole('button', { name: 'Abrir menú' }))
  expect(container.querySelector('.app-shell')?.classList.contains('menu-open')).toBe(true)
  await irA('Carteles')
  expect(container.querySelector('.app-shell')?.classList.contains('menu-open')).toBe(false)
  expect(screen.getByRole('button', { name: 'Abrir menú' }).getAttribute('aria-expanded')).toBe(
    'false',
  )
})

test('un 401 en endpoint no-auth despacha sesion-expirada y muestra el mensaje en login', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'seba' })
      if (input.startsWith('/api/clientes/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )

  render(<App />)
  // Esperar a que la sesión quede ready
  await screen.findByRole('navigation', { name: 'Navegación' })

  // Disparar el evento como si un fetch a un endpoint no-auth devolviera 401
  window.dispatchEvent(new Event('sesion-expirada'))

  expect(await screen.findByRole('heading', { name: 'Ingresar' })).toBeDefined()
  expect(
    await screen.findByText('Tu sesión expiró por inactividad. Ingresá de nuevo.'),
  ).toBeDefined()
})

test('un 401 en /api/auth/me/ NO despacha sesion-expirada', async () => {
  const listener = vi.fn()
  window.addEventListener('sesion-expirada', listener)

  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Iniciá sesión.' }),
    }),
  )

  render(<App />)
  await screen.findByRole('heading', { name: 'Ingresar' })

  expect(listener).not.toHaveBeenCalled()
  window.removeEventListener('sesion-expirada', listener)
})

test('el rol Lectura no ve acciones de edición', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'consulta', rol: 'lectura' })
      if (input.startsWith('/api/clientes/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Clientes' })).toBeDefined()
  expect(screen.queryByRole('button', { name: 'Nuevo cliente' })).toBeNull()
})

test('el rol Operativo ve acciones de edición', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      if (input === '/api/auth/me/') return ok({ username: 'trabajador', rol: 'operativo' })
      if (input.startsWith('/api/clientes/')) return ok([])
      throw new Error(`URL inesperada: ${input}`)
    }),
  )
  render(<App />)
  expect(await screen.findByRole('button', { name: 'Nuevo cliente' })).toBeDefined()
})
