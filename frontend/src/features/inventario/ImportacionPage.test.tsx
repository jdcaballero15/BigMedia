import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { descargarCsv } from '../../shared/csv'
import ImportacionPage from './ImportacionPage'
import type { Importacion } from './types'

vi.mock('../../shared/csv', () => ({ descargarCsv: vi.fn() }))

const ok = (data: unknown) => ({ ok: true, status: 200, json: async () => data })
const fail = (status: number, data: unknown) => ({ ok: false, status, json: async () => data })

const URL = '/api/inventario/importaciones/'
const formatos = [
  { id: 3, nombre: 'Séxtuples', modalidad: 'fija', capacidad_predeterminada: 6 },
  { id: 4, nombre: 'LED', modalidad: 'digital', capacidad_predeterminada: 8 },
]

function importacion(simulado: boolean): Importacion {
  return {
    simulado,
    resumen: { leidas: 3, creadas: 1, omitidas: 0, rechazadas: 1, en_revision: 1, incompletas: 1 },
    filas: [
      {
        fila: 2,
        ref_origen: 'Sextuples fila 3',
        resultado: 'creada',
        campo: '',
        motivo: 'Incompleto: faltan proveedor, tarifa_lista, foto_url.',
        cartel_coincidente: '',
      },
      {
        fila: 3,
        ref_origen: '',
        resultado: 'rechazada',
        campo: 'zona',
        motivo: 'Falta la zona.',
        cartel_coincidente: '',
      },
      {
        fila: 4,
        ref_origen: '',
        resultado: 'en_revision',
        campo: '',
        motivo: 'Posible duplicado de Calle Ficticia 100 · 6 slots.',
        cartel_coincidente: 'Calle Ficticia 100 · 6 slots',
      },
    ],
  }
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function stubFetch(respuesta: (options?: RequestInit) => unknown) {
  const fetchMock = vi.fn(async (input: string, options?: RequestInit) =>
    input === URL ? respuesta(options) : ok(formatos),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

async function elegirArchivo() {
  fireEvent.change(await screen.findByLabelText('Formato'), { target: { value: '3' } })
  const archivo = new File(['formato,direccion'], 'sextuples.csv', { type: 'text/csv' })
  fireEvent.change(screen.getByLabelText('Archivo CSV'), { target: { files: [archivo] } })
}

test('solo ofrece los formatos fijos', async () => {
  stubFetch(() => ok(importacion(true)))
  render(<ImportacionPage />)

  const selector = await screen.findByLabelText('Formato')
  await screen.findByRole('option', { name: 'Séxtuples' })
  expect(within(selector).queryByRole('option', { name: 'LED' })).toBeNull()
})

test('los botones esperan el formato y el archivo', async () => {
  stubFetch(() => ok(importacion(true)))
  render(<ImportacionPage />)

  expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Simular' }).disabled).toBe(true)
  await elegirArchivo()
  expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Simular' }).disabled).toBe(false)
})

test('simular manda el archivo y muestra el resumen y el reporte', async () => {
  const fetchMock = stubFetch(() => ok(importacion(true)))
  render(<ImportacionPage />)
  await elegirArchivo()

  fireEvent.click(screen.getByRole('button', { name: 'Simular' }))

  expect((await screen.findByRole('status')).textContent).toContain('no se guardó nada')
  const envio = fetchMock.mock.calls.find(([input]) => input === URL)
  expect(envio?.[1]?.method).toBe('POST')
  const form = envio?.[1]?.body as FormData
  expect(form.get('formato')).toBe('3')
  expect(form.get('simular')).toBe('1')
  expect((form.get('archivo') as File).name).toBe('sextuples.csv')
  const resumen = screen.getByLabelText('Resumen de la importación')
  expect(within(resumen).getByText('Se crearían')).toBeDefined()
  expect(within(resumen).getByText('1 incompletas')).toBeDefined()
  expect(screen.getByText('Falta la zona.')).toBeDefined()
  const tabla = screen.getByRole('table')
  expect(within(tabla).getByText('En revisión')).toBeDefined()
  expect(within(tabla).getByText('Rechazada')).toBeDefined()
})

test('importar manda simular en 0 y avisa que terminó', async () => {
  const fetchMock = stubFetch(() => ok(importacion(false)))
  render(<ImportacionPage />)
  await elegirArchivo()

  fireEvent.click(screen.getByRole('button', { name: 'Importar' }))

  expect((await screen.findByRole('status')).textContent).toBe('Importación terminada.')
  const envio = fetchMock.mock.calls.find(([input]) => input === URL)
  const form = envio?.[1]?.body as FormData | undefined
  expect(form?.get('simular')).toBe('0')
  expect(
    within(screen.getByLabelText('Resumen de la importación')).getByText('Creadas'),
  ).toBeDefined()
})

test('descargar reporte baja el CSV con las columnas de la plantilla', async () => {
  stubFetch(() => ok(importacion(true)))
  render(<ImportacionPage />)
  await elegirArchivo()
  fireEvent.click(screen.getByRole('button', { name: 'Simular' }))

  fireEvent.click(await screen.findByRole('button', { name: 'Descargar reporte' }))

  const [nombre, columnas, filas] = vi.mocked(descargarCsv).mock.calls[0]
  expect(nombre).toBe('simulacion-importacion.csv')
  expect(columnas).toEqual([
    'fila',
    'ref_origen',
    'resultado',
    'campo',
    'motivo',
    'cartel_coincidente',
  ])
  expect(filas[1]).toEqual([3, '', 'rechazada', 'zona', 'Falta la zona.', ''])
})

test('un error del archivo se muestra junto al campo', async () => {
  stubFetch(() =>
    fail(400, {
      archivo: ['El archivo usa punto y coma como separador: guardalo separado por comas.'],
    }),
  )
  render(<ImportacionPage />)
  await elegirArchivo()

  fireEvent.click(screen.getByRole('button', { name: 'Simular' }))

  expect(await screen.findByText(/usa punto y coma/)).toBeDefined()
  expect(screen.queryByRole('status')).toBeNull()
})

test('un error sin campo se muestra como alerta', async () => {
  stubFetch(() => fail(403, { detail: 'No tenés permiso para realizar esta acción.' }))
  render(<ImportacionPage />)
  await elegirArchivo()

  fireEvent.click(screen.getByRole('button', { name: 'Importar' }))

  expect((await screen.findByRole('alert')).textContent).toBe(
    'No tenés permiso para realizar esta acción.',
  )
})

test('si no cargan los formatos avisa', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => fail(500, {})),
  )
  render(<ImportacionPage />)

  expect((await screen.findByRole('alert')).textContent).toBe('No se pudieron cargar los formatos.')
})
