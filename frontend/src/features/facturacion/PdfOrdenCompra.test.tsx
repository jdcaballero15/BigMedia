import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import PdfOrdenCompra from './PdfOrdenCompra'

const URL = '/api/facturacion/items/8/orden-compra-pdf/'
const ok = (data: unknown, status = 200) => ({ ok: true, status, json: async () => data })
const rechazo = (data: unknown) => ({ ok: false, status: 400, json: async () => data })

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function adjuntar(nombre = 'oc.pdf') {
  const archivo = new File(['%PDF-1.4'], nombre, { type: 'application/pdf' })
  fireEvent.change(screen.getByLabelText('PDF de la orden de compra'), {
    target: { files: [archivo] },
  })
  return archivo
}

test('sube el PDF como multipart y muestra el enlace para abrirlo', async () => {
  const fetchMock = vi.fn(async () => ok({ nombre: 'oc.pdf', tamanio: 8 }))
  vi.stubGlobal('fetch', fetchMock)
  const onCambio = vi.fn()
  render(<PdfOrdenCompra itemId={8} pdf={null} onCambio={onCambio} />)
  const archivo = adjuntar()
  const enlace = await screen.findByRole('link', { name: 'Abrir oc.pdf' })
  expect(enlace.getAttribute('href')).toBe(URL)
  expect(enlace.getAttribute('target')).toBe('_blank')
  const [url, options] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
  expect(url).toBe(URL)
  expect(options.method).toBe('PUT')
  expect((options.body as FormData).get('archivo')).toBe(archivo)
  expect(onCambio).toHaveBeenCalledTimes(1)
})

test('un archivo rechazado muestra el motivo', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => rechazo({ archivo: ['El archivo tiene que ser un PDF.'] })),
  )
  const onCambio = vi.fn()
  render(<PdfOrdenCompra itemId={8} pdf={null} onCambio={onCambio} />)
  adjuntar('oc.docx')
  expect(await screen.findByText('El archivo tiene que ser un PDF.')).toBeDefined()
  expect(onCambio).not.toHaveBeenCalled()
})

test('un error sin motivo muestra un mensaje general', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) })),
  )
  render(<PdfOrdenCompra itemId={8} pdf={null} onCambio={vi.fn()} />)
  adjuntar()
  expect(await screen.findByText('No se pudo actualizar el PDF.')).toBeDefined()
})

test('elegir y cancelar sin archivo no sube nada', () => {
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  render(<PdfOrdenCompra itemId={8} pdf={null} onCambio={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('PDF de la orden de compra'), { target: { files: [] } })
  expect(fetchMock).not.toHaveBeenCalled()
})

test('quita el PDF', async () => {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    status: 204,
    json: async () => {
      throw new Error('sin cuerpo')
    },
  }))
  vi.stubGlobal('fetch', fetchMock)
  const onCambio = vi.fn()
  render(<PdfOrdenCompra itemId={8} pdf={{ nombre: 'oc.pdf', tamanio: 8 }} onCambio={onCambio} />)
  fireEvent.click(screen.getByRole('button', { name: 'Quitar PDF' }))
  await waitFor(() => expect(screen.queryByRole('link', { name: 'Abrir oc.pdf' })).toBeNull())
  const [url, options] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
  expect([url, options.method]).toEqual([URL, 'DELETE'])
  expect(onCambio).toHaveBeenCalledTimes(1)
})
