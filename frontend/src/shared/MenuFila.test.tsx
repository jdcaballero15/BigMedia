import { afterEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import MenuFila from './MenuFila'
import { PuedeEditarContext } from './sesion'

afterEach(cleanup)

function abrir() {
  fireEvent.click(screen.getByRole('button', { name: 'Más acciones' }))
}

test('menuFila_clicEnTresPuntos_muestraYOcultaLasAcciones', () => {
  render(<MenuFila acciones={[{ etiqueta: 'Editar', onClick: vi.fn() }]} />)

  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
  abrir()
  expect(screen.getByRole('button', { name: 'Más acciones' }).getAttribute('aria-expanded')).toBe(
    'true',
  )
  expect(screen.getByRole('button', { name: 'Editar' })).toBeDefined()
  abrir()
  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
})

test('menuFila_eligeUnaAccion_laEjecutaYCierra', () => {
  const editar = vi.fn()
  render(<MenuFila acciones={[{ etiqueta: 'Editar', onClick: editar }]} />)

  abrir()
  fireEvent.click(screen.getByRole('button', { name: 'Editar' }))

  expect(editar).toHaveBeenCalledOnce()
  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
})

test('menuFila_escapeOClicAfuera_cierra', () => {
  render(
    <>
      <p>Afuera</p>
      <MenuFila acciones={[{ etiqueta: 'Editar', onClick: vi.fn() }]} />
    </>,
  )

  abrir()
  fireEvent.keyDown(document, { key: 'Enter' })
  expect(screen.getByRole('button', { name: 'Editar' })).toBeDefined()
  fireEvent.keyDown(document, { key: 'Escape' })
  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()

  abrir()
  fireEvent.mouseDown(screen.getByRole('button', { name: 'Editar' }))
  expect(screen.getByRole('button', { name: 'Editar' })).toBeDefined()
  fireEvent.mouseDown(screen.getByText('Afuera'))
  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
})

test('menuFila_scrollDeLaPagina_cierra', () => {
  render(<MenuFila acciones={[{ etiqueta: 'Editar', onClick: vi.fn() }]} />)

  abrir()
  fireEvent.scroll(window)

  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
})

test('menuFila_lectura_noVeLasAccionesDeEdicion', () => {
  render(
    <PuedeEditarContext value={false}>
      <MenuFila
        acciones={[
          { etiqueta: 'Costos', onClick: vi.fn() },
          { etiqueta: 'Editar', onClick: vi.fn(), edicion: true },
          false,
        ]}
      />
    </PuedeEditarContext>,
  )

  abrir()

  expect(screen.getByRole('button', { name: 'Costos' })).toBeDefined()
  expect(screen.queryByRole('button', { name: 'Editar' })).toBeNull()
})

test('menuFila_sinAccionesVisibles_noMuestraLosTresPuntos', () => {
  render(
    <PuedeEditarContext value={false}>
      <MenuFila acciones={[{ etiqueta: 'Editar', onClick: vi.fn(), edicion: true }, null]} />
    </PuedeEditarContext>,
  )

  expect(screen.queryByRole('button', { name: 'Más acciones' })).toBeNull()
})
