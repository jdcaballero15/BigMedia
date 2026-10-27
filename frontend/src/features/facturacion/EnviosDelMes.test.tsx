import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import EnviosDelMes from './EnviosDelMes'
import type { EnvioFacturacion, ResultadoEnvio } from './types'

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const falla = { ok: false, status: 500, json: async () => ({}) }

const envio: EnvioFacturacion = {
  id: 4,
  mes: '2026-11',
  enviado_por_nombre: 'seba',
  enviado_en: '2026-11-30T15:00:00-03:00',
  items: [1, 2],
  cantidad: 2,
}

function stubFetch(
  envios: EnvioFacturacion[],
  resultado?: ResultadoEnvio | typeof falla,
  listado?: typeof falla,
) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
    if (options?.method === 'POST') {
      if (resultado && 'ok' in resultado) return resultado
      return ok(resultado)
    }
    if (input.includes('/facturacion/envios/?mes=')) return listado ?? ok(envios)
    throw new Error(`URL inesperada: ${input}`)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function renderizar(extra: Partial<Parameters<typeof EnviosDelMes>[0]> = {}) {
  const onEnviado = vi.fn()
  render(<EnviosDelMes mes="2026-11" puedeEditar hayBorradores onEnviado={onEnviado} {...extra} />)
  return onEnviado
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

test('lista los envíos del mes con su planilla', async () => {
  const fetchMock = stubFetch([envio])
  renderizar()
  const lista = await screen.findByRole('list', { name: 'Envíos del mes' })
  expect(lista.textContent).toContain('seba · 2 ítems')
  expect(within(lista).getByRole('link', { name: 'Descargar planilla' }).getAttribute('href')).toBe(
    '/api/facturacion/envios/4/planilla/',
  )
  expect(String(fetchMock.mock.calls[0][0])).toBe('/api/facturacion/envios/?mes=2026-11')
})

test('envía a facturar y muestra los incompletos con lo que les falta', async () => {
  const fetchMock = stubFetch([], {
    envio,
    incompletos: [{ item: 3, descripcion: 'Sin cliente', faltan: ['cliente', 'importe neto'] }],
  })
  const onEnviado = renderizar()
  await screen.findByText('Todavía no se envió nada de este mes.')
  fireEvent.click(screen.getByRole('button', { name: 'Enviar a facturar' }))
  const resumen = await screen.findByRole('status', { name: 'Resultado del envío' })
  expect(resumen.textContent).toContain('Se enviaron 2 ítems a facturar.')
  expect(within(resumen).getByText('1 quedó en Borrador porque le falta:')).toBeDefined()
  expect(within(resumen).getByText('Sin cliente: cliente, importe neto')).toBeDefined()
  expect(within(resumen).getByRole('link', { name: 'Descargar planilla' })).toBeDefined()
  expect(onEnviado).toHaveBeenCalledTimes(1)
  const [, options] = fetchMock.mock.calls.find(([, o]) => o?.method === 'POST') ?? []
  expect(JSON.parse(String(options?.body))).toEqual({ mes: '2026-11' })
  await waitFor(() =>
    expect(fetchMock.mock.calls.filter(([, o]) => o?.method !== 'POST')).toHaveLength(2),
  )
})

test('con un solo ítem enviado y varios incompletos concuerda el número', async () => {
  const incompleto = { item: 3, descripcion: 'Sin cliente', faltan: ['cliente'] }
  stubFetch([], {
    envio: { ...envio, cantidad: 1 },
    incompletos: [incompleto, { ...incompleto, item: 5, descripcion: 'Sin importe' }],
  })
  renderizar()
  await screen.findByText('Todavía no se envió nada de este mes.')
  fireEvent.click(screen.getByRole('button', { name: 'Enviar a facturar' }))
  const resumen = await screen.findByRole('status', { name: 'Resultado del envío' })
  expect(resumen.textContent).toContain('Se envió 1 ítem a facturar.')
  expect(within(resumen).getByText('2 quedaron en Borrador porque les falta:')).toBeDefined()
})

test('sin ítems completos lo avisa y no recarga los ítems', async () => {
  stubFetch([], { envio: null, incompletos: [] })
  const onEnviado = renderizar()
  fireEvent.click(screen.getByRole('button', { name: 'Enviar a facturar' }))
  expect(await screen.findByText('No hay ítems completos para enviar.')).toBeDefined()
  expect(onEnviado).not.toHaveBeenCalled()
})

test('si falla el envío lo avisa', async () => {
  stubFetch([], falla)
  renderizar()
  fireEvent.click(screen.getByRole('button', { name: 'Enviar a facturar' }))
  expect((await screen.findByRole('alert')).textContent).toBe('No se pudo enviar a facturar.')
})

test('si falla el listado lo avisa', async () => {
  stubFetch([], undefined, falla)
  renderizar()
  expect((await screen.findByRole('alert')).textContent).toBe(
    'No se pudieron cargar los envíos del mes.',
  )
})

test('sin Borradores o sin permiso no ofrece enviar', async () => {
  stubFetch([])
  renderizar({ hayBorradores: false })
  await screen.findByText('Todavía no se envió nada de este mes.')
  expect(screen.queryByRole('button', { name: 'Enviar a facturar' })).toBeNull()
  cleanup()
  stubFetch([])
  renderizar({ puedeEditar: false })
  await screen.findByText('Todavía no se envió nada de este mes.')
  expect(screen.queryByRole('button', { name: 'Enviar a facturar' })).toBeNull()
})
