import { useState } from 'react'
import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import CampoFecha from './CampoFecha'
import { FECHA_INVALIDA, MENSAJE_FECHA_INVALIDA } from './fechas'

afterEach(cleanup)

function campo() {
  return screen.getByLabelText('Fecha de inicio') as HTMLInputElement
}

function botonCalendario() {
  return screen.getByRole('button', { name: 'Abrir calendario: Fecha de inicio' })
}

test('CampoFecha_valorIso_seMuestraComoDiaMesAnio', () => {
  render(<CampoFecha label="Fecha de inicio" value="2026-11-01" onChange={vi.fn()} />)
  expect(campo().value).toBe('01/11/2026')
  expect(campo().placeholder).toBe('dd/mm/aaaa')
})

test('CampoFecha_escribeFechaValida_emiteIso', () => {
  const onChange = vi.fn()
  render(<CampoFecha label="Fecha de inicio" value="" onChange={onChange} />)
  fireEvent.change(campo(), { target: { value: '15/11/2026' } })
  expect(onChange).toHaveBeenLastCalledWith('2026-11-15')
})

test('CampoFecha_escribeFechaInexistente_emiteInvalidaYMuestraErrorAlSalir', () => {
  const onChange = vi.fn()
  render(<CampoFecha label="Fecha de inicio" value="" onChange={onChange} />)
  fireEvent.change(campo(), { target: { value: '31/02/2026' } })
  expect(onChange).toHaveBeenLastCalledWith(FECHA_INVALIDA)
  expect(screen.queryByText(MENSAJE_FECHA_INVALIDA)).toBeNull()
  fireEvent.blur(campo())
  expect(screen.getByText(MENSAJE_FECHA_INVALIDA)).toBeDefined()
  expect(campo().getAttribute('aria-invalid')).toBe('true')
})

test('CampoFecha_borraElTexto_emiteVacio', () => {
  const onChange = vi.fn()
  render(<CampoFecha label="Fecha de inicio" value="2026-11-01" onChange={onChange} />)
  fireEvent.change(campo(), { target: { value: '' } })
  expect(onChange).toHaveBeenLastCalledWith('')
})

test('CampoFecha_eligeDiaEnCalendario_emiteIsoYCierra', () => {
  const onChange = vi.fn()
  render(<CampoFecha label="Fecha de inicio" value="2026-11-01" onChange={onChange} />)
  fireEvent.click(botonCalendario())
  const calendario = screen.getByRole('dialog', { name: 'Calendario: Fecha de inicio' })
  const mes = within(calendario).getByRole('grid', { name: /noviembre 2026/i })
  fireEvent.click(within(mes).getByText('15'))
  expect(onChange).toHaveBeenLastCalledWith('2026-11-15')
  expect(screen.queryByRole('dialog')).toBeNull()
})

test('CampoFecha_escape_cierraElCalendario', () => {
  render(<CampoFecha label="Fecha de inicio" value="" onChange={vi.fn()} />)
  fireEvent.click(botonCalendario())
  expect(botonCalendario().getAttribute('aria-expanded')).toBe('true')
  fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
  expect(screen.queryByRole('dialog')).toBeNull()
})

test('CampoFecha_clicAfuera_cierraElCalendario', () => {
  render(
    <div>
      <p>Afuera</p>
      <CampoFecha label="Fecha de inicio" value="" onChange={vi.fn()} />
    </div>,
  )
  fireEvent.click(botonCalendario())
  fireEvent.mouseDown(screen.getByText('Afuera'))
  expect(screen.queryByRole('dialog')).toBeNull()
})

test('CampoFecha_botonDelCalendario_alternaAbiertoYCerrado', () => {
  render(<CampoFecha label="Fecha de inicio" value="" onChange={vi.fn()} />)
  fireEvent.click(botonCalendario())
  fireEvent.click(botonCalendario())
  expect(screen.queryByRole('dialog')).toBeNull()
})

test('CampoFecha_cambioDeValorDesdeAfuera_actualizaElTexto', () => {
  const { rerender } = render(
    <CampoFecha label="Fecha de inicio" value="2026-11-01" onChange={vi.fn()} />,
  )
  rerender(<CampoFecha label="Fecha de inicio" value="2026-12-24" onChange={vi.fn()} />)
  expect(campo().value).toBe('24/12/2026')
})

test('CampoFecha_controladoPorElPadre_mantieneElTextoMientrasSeEscribe', () => {
  function Padre() {
    const [valor, setValor] = useState('')
    return <CampoFecha label="Fecha de inicio" value={valor} onChange={setValor} />
  }
  render(<Padre />)
  fireEvent.change(campo(), { target: { value: '15/1' } })
  expect(campo().value).toBe('15/1')
  fireEvent.change(campo(), { target: { value: '15/11/2026' } })
  expect(campo().value).toBe('15/11/2026')
})

test('CampoFecha_erroresDeLaApi_seMuestranSinRepetir', () => {
  render(
    <CampoFecha
      label="Fecha de inicio"
      value=""
      onChange={vi.fn()}
      errores={['Este campo es requerido.', MENSAJE_FECHA_INVALIDA]}
    />,
  )
  fireEvent.change(campo(), { target: { value: '99/99/2026' } })
  fireEvent.blur(campo())
  expect(screen.getByText('Este campo es requerido.')).toBeDefined()
  expect(screen.getAllByText(MENSAJE_FECHA_INVALIDA)).toHaveLength(1)
})
