import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import AgregarCarteles, { TAMANO_LOTE } from './AgregarCarteles'
import type { LineaTanda } from './AgregarCarteles'
import type { CartelTanda, ResultadoTanda } from './types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

function cartel(id: number, extra: Partial<CartelTanda> = {}): CartelTanda {
  return {
    id,
    nombre_visible: `Av. Prueba ${id} · 8x3`,
    zona_nombre: 'Ciudad',
    proveedor_nombre: null,
    tarifa_lista: '1000.50',
    capacidad: 1,
    ocupados: 0,
    tentativas: 0,
    en_campania: false,
    ...extra,
  }
}

const linea: LineaTanda = {
  formato: 10,
  formato_nombre: 'Gran Formato',
  solicitadas: 4,
  reservadas: 1,
}

type Overrides = (input: string, options?: RequestInit) => unknown

function stubFetch(carteles: CartelTanda[], overrides?: Overrides) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    const custom = overrides?.(input, options)
    if (custom) return custom
    if (input.includes('/inventario/zonas/')) return ok([{ id: 3, nombre: 'Norte' }])
    if (input.includes('/inventario/proveedores/')) return ok([{ id: 4, nombre: 'Prov' }])
    if (input.includes('/carteles-para-tanda/')) return ok(carteles)
    if (input.includes('/en-bloque/')) {
      const ids = (JSON.parse(String(options?.body)) as { carteles: number[] }).carteles
      const creadas = ids.map((id) => ({ cartel: id, reserva: id + 1000 }))
      return ok({ creadas, existentes: [], fallidas: [] } satisfies ResultadoTanda)
    }
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function pedidos(fetchMock: ReturnType<typeof stubFetch>, parte: string) {
  return fetchMock.mock.calls.filter(([url]) => String(url).includes(parte))
}

function cuerposEnBloque(fetchMock: ReturnType<typeof stubFetch>) {
  return pedidos(fetchMock, '/en-bloque/').map(([, options]) => JSON.parse(String(options?.body)))
}

function renderizar(extra: Partial<Parameters<typeof AgregarCarteles>[0]> = {}) {
  const onCreadas = vi.fn()
  render(
    <AgregarCarteles
      campaniaId={5}
      fechaInicio="2026-11-01"
      fechaFin="2026-11-30"
      linea={linea}
      onCerrar={vi.fn()}
      onCreadas={onCreadas}
      {...extra}
    />,
  )
  return { onCreadas }
}

const elegir = (id: number) =>
  fireEvent.click(screen.getByLabelText(`Elegir Av. Prueba ${id} · 8x3`))

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('abre con las fechas de la campaña y lista los carteles libres del formato', async () => {
  const fetchMock = stubFetch([cartel(1, { tentativas: 2, proveedor_nombre: 'Prov' })])
  renderizar()
  expect(await screen.findByText('Av. Prueba 1 · 8x3')).toBeDefined()
  expect((screen.getByLabelText('Desde') as HTMLInputElement).value).toBe('01/11/2026')
  expect(screen.getByText('· 2 tentativas')).toBeDefined()
  expect(screen.getByText('$1.000,50')).toBeDefined()
  const url = String(pedidos(fetchMock, '/carteles-para-tanda/')[0][0])
  expect(url).toContain('campania=5&formato=10&desde=2026-11-01&hasta=2026-11-30')
})

test('sin fechas en la campaña las pide y no lista ni deja crear', async () => {
  const fetchMock = stubFetch([cartel(1)])
  renderizar({ fechaInicio: '', fechaFin: '' })
  expect(
    screen.getByText('Indicá las fechas de la tanda para ver los carteles libres.'),
  ).toBeDefined()
  expect(
    (screen.getByRole('button', { name: 'Crear reservas' }) as HTMLButtonElement).disabled,
  ).toBe(true)
  fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '01/12/2026' } })
  fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '31/12/2026' } })
  expect(await screen.findByText('Av. Prueba 1 · 8x3')).toBeDefined()
  const urls = pedidos(fetchMock, '/carteles-para-tanda/').map(([url]) => String(url))
  expect(urls).toHaveLength(1)
  expect(urls[0]).toContain('desde=2026-12-01&hasta=2026-12-31')
})

test('los filtros viajan en la consulta', async () => {
  const fetchMock = stubFetch([cartel(1)])
  renderizar()
  await screen.findByText('Av. Prueba 1 · 8x3')
  await screen.findByRole('option', { name: 'Norte' })
  fireEvent.change(screen.getByLabelText('Zona'), { target: { value: '3' } })
  fireEvent.change(screen.getByLabelText('Proveedor'), { target: { value: '4' } })
  fireEvent.change(screen.getByLabelText('Dirección'), { target: { value: ' cordoba ' } })
  await waitFor(() =>
    expect(String(pedidos(fetchMock, '/carteles-para-tanda/').at(-1)?.[0])).toContain(
      'zona=3&proveedor=4&q=cordoba',
    ),
  )
})

test('sin carteles libres lo avisa', async () => {
  stubFetch([])
  renderizar()
  expect(await screen.findByText('No hay carteles libres con estos filtros.')).toBeDefined()
})

test('si falla la carga muestra el error', async () => {
  stubFetch([], (input) =>
    input.includes('/carteles-para-tanda/')
      ? { ok: false, status: 500, json: async () => ({}) }
      : undefined,
  )
  renderizar()
  expect((await screen.findByRole('alert')).textContent).toBe('No se pudieron cargar los carteles.')
})

test('seleccionar todos los filtrados respeta los ya reservados y permite destildar', async () => {
  stubFetch([cartel(1), cartel(2), cartel(3, { en_campania: true })])
  renderizar()
  await screen.findByText('Av. Prueba 1 · 8x3')
  expect(screen.getByText('· ya en la campaña')).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Seleccionar todos los filtrados' }))
  elegir(2)
  const marcados = screen.getAllByRole('checkbox').map((box) => (box as HTMLInputElement).checked)
  expect(marcados).toEqual([true, false, false])
  expect((screen.getByLabelText('Elegir Av. Prueba 3 · 8x3') as HTMLInputElement).disabled).toBe(
    true,
  )
})

test('el contador suma lo ya reservado y muestra el monto estimado', async () => {
  stubFetch([cartel(1), cartel(2, { tarifa_lista: null })])
  renderizar()
  await screen.findByText('Av. Prueba 1 · 8x3')
  expect(screen.getByText('Sin tarifa')).toBeDefined()
  elegir(1)
  elegir(2)
  expect(screen.getByText('Gran Formato 3 de 4')).toBeDefined()
  expect(screen.getByText(/Monto estimado \$1\.000,50/)).toBeDefined()
})

test('una línea sin cantidad muestra solo lo seleccionado y no avisa', async () => {
  const fetchMock = stubFetch([cartel(1)])
  renderizar({ linea: { ...linea, solicitadas: null } })
  await screen.findByText('Av. Prueba 1 · 8x3')
  elegir(1)
  expect(screen.getByText('Gran Formato: 1 seleccionados')).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Crear reservas' }))
  await waitFor(() => expect(cuerposEnBloque(fetchMock)).toHaveLength(1))
})

test('si la selección no coincide con lo solicitado avisa pero deja crear', async () => {
  const fetchMock = stubFetch([cartel(1), cartel(2)])
  const { onCreadas } = renderizar()
  await screen.findByText('Av. Prueba 1 · 8x3')
  elegir(1)
  fireEvent.click(screen.getByRole('button', { name: 'Crear reservas' }))
  expect(screen.getByRole('alert').textContent).toContain('no coincide con lo solicitado (2 de 4)')
  expect(cuerposEnBloque(fetchMock)).toHaveLength(0)
  fireEvent.click(screen.getByRole('button', { name: 'Crear igual' }))
  await waitFor(() =>
    expect(cuerposEnBloque(fetchMock)).toEqual([
      { campania: 5, fecha_inicio: '2026-11-01', fecha_fin: '2026-11-30', carteles: [1] },
    ]),
  )
  expect(await screen.findByText('Se crearon 1 reservas Pendientes.')).toBeDefined()
  expect(onCreadas).toHaveBeenCalledTimes(1)
})

test('si coincide con lo solicitado crea sin avisar', async () => {
  const fetchMock = stubFetch([cartel(1), cartel(2), cartel(3)])
  renderizar()
  await screen.findByText('Av. Prueba 1 · 8x3')
  fireEvent.click(screen.getByRole('button', { name: 'Seleccionar todos los filtrados' }))
  fireEvent.click(screen.getByRole('button', { name: 'Crear reservas' }))
  await waitFor(() => expect(cuerposEnBloque(fetchMock)[0].carteles).toEqual([1, 2, 3]))
})

test('manda la selección por lotes y muestra el avance', async () => {
  const carteles = Array.from({ length: TAMANO_LOTE + 5 }, (_, indice) => cartel(indice + 1))
  const fetchMock = stubFetch(carteles)
  const base = fetchMock.getMockImplementation()
  if (!base) throw new Error('fetch sin implementación')
  let liberar: () => void = () => undefined
  const pausa = new Promise<void>((resolve) => {
    liberar = resolve
  })
  // El primer lote espera, para ver el avance en 0 antes de que responda.
  fetchMock.mockImplementation(async (input: string, options?: RequestInit) => {
    if (input.includes('/en-bloque/') && cuerposEnBloque(fetchMock).length === 1) await pausa
    return base(input, options)
  })
  renderizar({ linea: { ...linea, solicitadas: null } })
  await screen.findByText('Av. Prueba 1 · 8x3')
  fireEvent.click(screen.getByRole('button', { name: 'Seleccionar todos los filtrados' }))
  fireEvent.click(screen.getByRole('button', { name: 'Crear reservas' }))
  expect((await screen.findByText(/Creando reservas…/)).textContent).toContain(
    `0 de ${TAMANO_LOTE + 5}`,
  )
  liberar()
  expect(
    await screen.findByText(`Se crearon ${TAMANO_LOTE + 5} reservas Pendientes.`),
  ).toBeDefined()
  expect(cuerposEnBloque(fetchMock).map((cuerpo) => cuerpo.carteles.length)).toEqual([
    TAMANO_LOTE,
    5,
  ])
})

test('el resumen lista las fallidas y reintenta solo esas', async () => {
  let intento = 0
  const fetchMock = stubFetch([cartel(1), cartel(2), cartel(3)], (input) => {
    if (!input.includes('/en-bloque/')) return undefined
    intento += 1
    if (intento === 1)
      return ok({
        creadas: [{ cartel: 1, reserva: 11 }],
        existentes: [{ cartel: 2, reserva: 12 }],
        fallidas: [{ cartel: 3, motivo: 'El cartel está de baja: no se puede reservar.' }],
      })
    return ok({ creadas: [{ cartel: 3, reserva: 13 }], existentes: [], fallidas: [] })
  })
  renderizar({ linea: { ...linea, solicitadas: null } })
  await screen.findByText('Av. Prueba 1 · 8x3')
  fireEvent.click(screen.getByRole('button', { name: 'Seleccionar todos los filtrados' }))
  fireEvent.click(screen.getByRole('button', { name: 'Crear reservas' }))
  const resumen = await screen.findByRole('status', { name: 'Resumen de la tanda' })
  expect(within(resumen).getByText(/1 ya existían y no se duplicaron/)).toBeDefined()
  expect(
    within(resumen).getByText('Av. Prueba 3 · 8x3: El cartel está de baja: no se puede reservar.'),
  ).toBeDefined()
  fireEvent.click(within(resumen).getByRole('button', { name: 'Reintentar fallidas' }))
  await waitFor(() => expect(cuerposEnBloque(fetchMock).at(-1)?.carteles).toEqual([3]))
  expect(await screen.findByText('Se crearon 1 reservas Pendientes.')).toBeDefined()
  expect(screen.queryByRole('list', { name: 'Reservas fallidas' })).toBeNull()
})

test('un lote que falla entero queda como fallido para reintentar', async () => {
  stubFetch([cartel(1)], (input) =>
    input.includes('/en-bloque/') ? { ok: false, status: 500, json: async () => ({}) } : undefined,
  )
  const { onCreadas } = renderizar({ linea: { ...linea, solicitadas: null } })
  await screen.findByText('Av. Prueba 1 · 8x3')
  elegir(1)
  fireEvent.click(screen.getByRole('button', { name: 'Crear reservas' }))
  expect(
    await screen.findByText('Av. Prueba 1 · 8x3: No se pudo completar el pedido. Reintentá.'),
  ).toBeDefined()
  expect(onCreadas).not.toHaveBeenCalled()
})

test('cambiar las fechas reinicia la selección', async () => {
  stubFetch([cartel(1)])
  renderizar({ linea: { ...linea, solicitadas: null } })
  await screen.findByText('Av. Prueba 1 · 8x3')
  elegir(1)
  expect(screen.getByText('Gran Formato: 1 seleccionados')).toBeDefined()
  fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '15/11/2026' } })
  expect(screen.getByText('Gran Formato: 0 seleccionados')).toBeDefined()
})

test('cerrar avisa al contenedor', async () => {
  stubFetch([])
  const onCerrar = vi.fn()
  renderizar({ onCerrar })
  fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }))
  expect(onCerrar).toHaveBeenCalledTimes(1)
})

test('si fallan los filtros lo avisa', async () => {
  stubFetch([], (input) =>
    input.includes('/inventario/zonas/')
      ? { ok: false, status: 500, json: async () => ({}) }
      : undefined,
  )
  renderizar()
  expect(await screen.findByText('No se pudieron cargar los filtros.')).toBeDefined()
})
