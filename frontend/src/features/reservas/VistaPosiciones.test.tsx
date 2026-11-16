import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import VistaPosiciones from './VistaPosiciones'
import { COLOR_SIN_MARCA, PALETA_MARCAS, colorDeMarca, contraste } from './colores'
import type { CartelTanda, FilaPosiciones, Ocupante } from './types'

afterEach(cleanup)

function ocupante(marca: string | null, extra: Partial<Ocupante> = {}): Ocupante {
  return {
    reserva_id: 1,
    marca_id: marca === null ? null : marca.length,
    marca_nombre: marca,
    campania_id: 50,
    campania_nombre: `Campaña ${marca ?? ''}`,
    es_esta_campania: false,
    estado: 'confirmada',
    fecha_inicio: '2026-11-01',
    fecha_fin: '2026-11-30',
    ...extra,
  }
}

function fila(id: number, extra: Partial<FilaPosiciones> = {}): FilaPosiciones {
  const capacidad = extra.capacidad ?? 2
  return {
    id,
    nombre_visible: `Av. Prueba ${id} · ${capacidad} slots`,
    direccion: `Av. Prueba ${id}`,
    zona_nombre: 'Ciudad',
    proveedor_nombre: null,
    tarifa_lista: '1000.00',
    capacidad,
    ocupados: 0,
    lleno: false,
    tentativas: 0,
    en_campania: false,
    slots: Array.from({ length: capacidad }, () => []),
    tentativas_detalle: [],
    ...extra,
  }
}

function renderizar(filas: FilaPosiciones[], seleccion = new Map<number, CartelTanda>()) {
  const onAlternar = vi.fn()
  render(<VistaPosiciones filas={filas} seleccion={seleccion} onAlternar={onAlternar} />)
  return onAlternar
}

function filaDe(direccion: string) {
  return screen.getByRole('row', { name: new RegExp(direccion) })
}

test('colorDeMarca es estable, usa la paleta y tiene un neutro para sin marca', () => {
  expect(PALETA_MARCAS).toHaveLength(12)
  expect(colorDeMarca(7)).toEqual(colorDeMarca(7))
  expect(colorDeMarca(13)).toEqual(PALETA_MARCAS[1])
  expect(colorDeMarca(null)).toEqual(COLOR_SIN_MARCA)
})

test('todos los colores de marca tienen texto legible', () => {
  for (const color of [...PALETA_MARCAS, COLOR_SIN_MARCA]) {
    expect(contraste(color.fondo, color.texto)).toBeGreaterThanOrEqual(4.5)
  }
})

test('muestra dirección, departamento, cantidad y un casillero por slot', () => {
  const ocupados = [[ocupante('Schervosky')], [ocupante('Fravega')], [ocupante('Matias')]]
  renderizar([fila(1, { capacidad: 8, ocupados: 3, slots: [...ocupados, [], [], [], [], []] })])

  const tabla = screen.getByRole('table', { name: 'Posiciones' })
  expect(within(tabla).getByRole('columnheader', { name: 'Departamento' })).toBeTruthy()
  const fila1 = filaDe('Av. Prueba 1')
  expect(within(fila1).getByText('Ciudad')).toBeTruthy()
  expect(within(fila1).getByText('8')).toBeTruthy()
  expect(within(fila1).getByText('Schervosky')).toBeTruthy()
  expect(within(fila1).getAllByRole('button', { name: /Elegir slot libre/ })).toHaveLength(5)
})

test('el casillero ocupado lleva el color de la marca y las fechas en el tooltip', () => {
  const marca = ocupante('Kamet', { marca_id: 4 })
  renderizar([fila(1, { ocupados: 1, slots: [[marca], []] })])

  const casillero = screen.getByText('Kamet')
  expect(casillero.closest('[title]')?.getAttribute('title')).toContain('01/11/2026')
  expect((casillero.closest('.posiciones-slot') as HTMLElement).style.background).toBeTruthy()
})

test('reservas sucesivas se ven en el mismo casillero', () => {
  renderizar([fila(1, { ocupados: 1, slots: [[ocupante('A'), ocupante('B')], []] })])
  expect(screen.getByText('A · B')).toBeTruthy()
})

test('una campaña sin marca se ve como Sin marca', () => {
  renderizar([fila(1, { ocupados: 1, slots: [[ocupante(null)], []] })])
  expect(screen.getByText('Sin marca')).toBeTruthy()
})

test('un cartel lleno se atenúa, dice Lleno y no tiene botones', () => {
  renderizar([fila(1, { capacidad: 1, ocupados: 1, lleno: true, slots: [[ocupante('X')]] })])
  const fila1 = filaDe('Av. Prueba 1')
  expect(fila1.className).toContain('lleno')
  expect(within(fila1).getByText('Lleno')).toBeTruthy()
  expect(within(fila1).queryByRole('button')).toBeNull()
})

test('la reserva propia en su casillero dice Esta campaña', () => {
  const propia = ocupante('Propia', { es_esta_campania: true })
  renderizar([
    fila(1, { capacidad: 1, ocupados: 1, lleno: true, en_campania: true, slots: [[propia]] }),
  ])
  expect(within(filaDe('Av. Prueba 1')).getByText('Esta campaña')).toBeTruthy()
})

test('click en un slot libre elige el cartel', () => {
  const datos = fila(1)
  const onAlternar = renderizar([datos])
  fireEvent.click(screen.getAllByRole('button', { name: /Elegir slot libre en Av. Prueba 1/ })[0])
  expect(onAlternar).toHaveBeenCalledWith(datos)
})

test('un cartel elegido muestra Esta campaña en el primer libre y se puede quitar', () => {
  const datos = fila(1, { ocupados: 1, slots: [[ocupante('X')], []] })
  const onAlternar = renderizar([datos], new Map([[1, datos]]))
  const quitar = screen.getByRole('button', { name: 'Quitar Av. Prueba 1 · 2 slots' })
  expect(quitar.textContent).toBe('Esta campaña')
  expect(quitar.className).toContain('es-seleccion')
  fireEvent.click(quitar)
  expect(onAlternar).toHaveBeenCalledWith(datos)
})

test('un cartel ya en la campaña no se puede elegir', () => {
  const pendiente = ocupante('Propia', { es_esta_campania: true, estado: 'pendiente' })
  renderizar([fila(1, { en_campania: true, tentativas_detalle: [pendiente] })])
  const fila1 = filaDe('Av. Prueba 1')
  expect(within(fila1).queryByRole('button')).toBeNull()
  expect(within(fila1).getByText('Esta campaña (pendiente)')).toBeTruthy()
})

test('las tentativas de otras campañas se muestran como chip con su marca', () => {
  const tentativa = ocupante('Kamet', { estado: 'pendiente' })
  renderizar([fila(1, { tentativas: 1, tentativas_detalle: [tentativa] })])
  const chip = within(filaDe('Av. Prueba 1')).getByText('· 1 tentativas')
  expect(chip.getAttribute('title')).toContain('Kamet')
})

test('doce slots se renderizan dentro del contenedor con scroll', () => {
  renderizar([fila(1, { capacidad: 12 })])
  const fila1 = filaDe('Av. Prueba 1')
  const scroll = fila1.querySelector('.posiciones-scroll') as HTMLElement
  expect(scroll).toBeTruthy()
  expect(within(scroll).getAllByRole('button')).toHaveLength(12)
})

test('mientras carga o sin carteles lo avisa', () => {
  render(<VistaPosiciones filas={null} seleccion={new Map()} onAlternar={vi.fn()} />)
  expect(screen.getByText('Cargando carteles…')).toBeTruthy()
  cleanup()
  renderizar([])
  expect(screen.getByText('No hay carteles con estos filtros.')).toBeTruthy()
})

test('las tentativas van junto a la dirección, fuera de la tira de slots', () => {
  const tentativa = ocupante('Kamet', { estado: 'pendiente' })
  const propia = ocupante('Propia', { es_esta_campania: true, estado: 'pendiente' })
  renderizar([
    fila(1, { capacidad: 12, tentativas: 1, tentativas_detalle: [tentativa] }),
    fila(2, { capacidad: 12, en_campania: true, tentativas_detalle: [propia] }),
  ])
  const direccion1 = within(filaDe('Av. Prueba 1')).getAllByRole('cell')[0]
  expect(within(direccion1).getByText('· 1 tentativas')).toBeTruthy()
  const direccion2 = within(filaDe('Av. Prueba 2')).getAllByRole('cell')[0]
  expect(within(direccion2).getByText('Esta campaña (pendiente)')).toBeTruthy()
})
