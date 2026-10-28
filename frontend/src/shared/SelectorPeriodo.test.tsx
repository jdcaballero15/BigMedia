import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import SelectorPeriodo from './SelectorPeriodo'

afterEach(cleanup)

function elegir(etiqueta: string, valor: string) {
  fireEvent.change(screen.getByLabelText(etiqueta), { target: { value: valor } })
}

test('selectorPeriodo_cambiaMesYAnio_armaAAAAMM', () => {
  const onCambiar = vi.fn()
  render(<SelectorPeriodo desde="2026-01" hasta="2026-12" onCambiar={onCambiar} />)

  expect(screen.getByRole('option', { name: 'Enero', selected: true })).toBeDefined()
  elegir('Mes desde', '3')
  expect(onCambiar).toHaveBeenLastCalledWith('2026-03', '2026-12')
  elegir('Mes hasta', '6')
  expect(onCambiar).toHaveBeenLastCalledWith('2026-01', '2026-06')
  elegir('Año desde', '2025')
  expect(onCambiar).toHaveBeenLastCalledWith('2025-01', '2026-12')
})

test('selectorPeriodo_inicioPasaAlFin_elFinLoAcompania', () => {
  const onCambiar = vi.fn()
  render(<SelectorPeriodo desde="2026-01" hasta="2026-03" onCambiar={onCambiar} />)

  elegir('Mes desde', '8')
  expect(onCambiar).toHaveBeenLastCalledWith('2026-08', '2026-08')
  elegir('Año desde', '2027')
  expect(onCambiar).toHaveBeenLastCalledWith('2027-01', '2027-01')
})

test('selectorPeriodo_fin_noPermiteAnteriorAlInicio', () => {
  const onCambiar = vi.fn()
  render(<SelectorPeriodo desde="2026-05" hasta="2026-08" onCambiar={onCambiar} />)

  const marzo = screen.getAllByRole('option', { name: 'Marzo' })[1] as HTMLOptionElement
  expect(marzo.disabled).toBe(true)
  const mayo = screen.getAllByRole('option', { name: 'Mayo' })[1] as HTMLOptionElement
  expect(mayo.disabled).toBe(false)
  const anterior = screen.getAllByRole('option', { name: '2025' })[1] as HTMLOptionElement
  expect(anterior.disabled).toBe(true)
  // Si igual llega un fin anterior (por ejemplo, otro año), queda en el inicio.
  elegir('Mes hasta', '2')
  expect(onCambiar).toHaveBeenLastCalledWith('2026-05', '2026-05')
})

test('selectorPeriodo_periodoFueraDelRango_ampliaLosAnios', () => {
  render(<SelectorPeriodo desde="2010-01" hasta="2040-12" onCambiar={vi.fn()} />)

  expect(screen.getAllByRole('option', { name: '2010' })).toHaveLength(2)
  expect(screen.getAllByRole('option', { name: '2040' })).toHaveLength(2)
})
