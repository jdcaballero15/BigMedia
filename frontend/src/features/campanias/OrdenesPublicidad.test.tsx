import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import OrdenesPublicidad from './OrdenesPublicidad'
import { PuedeEditarContext } from '../../shared/sesion'
import type { OrdenPublicidad } from './types'

const vigente: OrdenPublicidad = {
  id: 3,
  nombre: 'op-cliente.pdf',
  tamanio: 2048,
  subida_por_nombre: 'operativo',
  subida_en: '2026-11-07T10:30:00-03:00',
  activa: true,
}
const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

test('lista las órdenes vigentes con enlace, usuario y fecha (HU-069)', () => {
  render(<OrdenesPublicidad ordenes={[vigente]} />)
  const enlace = screen.getByRole('link', { name: 'op-cliente.pdf' })
  expect(enlace.getAttribute('href')).toBe('/api/campanias/ordenes-publicidad/3/archivo/')
  expect(enlace.getAttribute('target')).toBe('_blank')
  expect(screen.getByText(/operativo · 07\/11\/2026/)).toBeDefined()
})

test('sin órdenes muestra el aviso', () => {
  render(<OrdenesPublicidad ordenes={[]} />)
  expect(screen.getByText('Sin órdenes de publicidad.')).toBeDefined()
})

test('dar de baja la pasa al histórico', async () => {
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  const fetchMock = vi.fn().mockResolvedValue(ok({ ...vigente, activa: false }))
  vi.stubGlobal('fetch', fetchMock)
  render(<OrdenesPublicidad ordenes={[vigente]} />)
  fireEvent.click(screen.getByRole('button', { name: 'Dar de baja op-cliente.pdf' }))
  await waitFor(() => expect(screen.getByText('Dadas de baja (1)')).toBeDefined())
  expect(screen.getByText('Sin órdenes de publicidad.')).toBeDefined()
  expect(fetchMock).toHaveBeenCalledWith(
    '/api/campanias/ordenes-publicidad/3/dar-de-baja/',
    expect.objectContaining({ method: 'POST' }),
  )
})

test('si no se confirma no da de baja', () => {
  vi.spyOn(window, 'confirm').mockReturnValue(false)
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  render(<OrdenesPublicidad ordenes={[vigente]} />)
  fireEvent.click(screen.getByRole('button', { name: 'Dar de baja op-cliente.pdf' }))
  expect(fetchMock).not.toHaveBeenCalled()
})

test('muestra el error si la baja falla', async () => {
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Sin conexión.')))
  render(<OrdenesPublicidad ordenes={[vigente]} />)
  fireEvent.click(screen.getByRole('button', { name: 'Dar de baja op-cliente.pdf' }))
  expect(await screen.findByRole('alert')).toBeDefined()
  expect(screen.getByText('Sin conexión.')).toBeDefined()
})

test('Lectura abre las órdenes pero no las da de baja', () => {
  render(
    <PuedeEditarContext.Provider value={false}>
      <OrdenesPublicidad ordenes={[vigente]} />
    </PuedeEditarContext.Provider>,
  )
  expect(screen.getByRole('link', { name: 'op-cliente.pdf' })).toBeDefined()
  expect(screen.queryByRole('button', { name: /Dar de baja/ })).toBeNull()
})

test('la sección usa el encabezado, el cuerpo y la separación de las demás tarjetas', () => {
  render(<OrdenesPublicidad ordenes={[vigente]} />)
  const seccion = screen.getByRole('region', { name: 'Órdenes de publicidad' })
  expect(seccion.classList.contains('section-gap')).toBe(true)
  expect(seccion.querySelector('.card-heading h3')?.textContent).toBe('Órdenes de publicidad')
  expect(seccion.querySelector('.card-cuerpo')).not.toBeNull()
})
