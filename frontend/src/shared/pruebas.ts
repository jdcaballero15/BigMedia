import { fireEvent, within } from '@testing-library/react'

/** Abre el menú de tres puntos de una fila (o de lo que la contenga) para llegar a sus acciones. */
export function abrirAcciones(fila: HTMLElement) {
  fireEvent.click(within(fila).getByRole('button', { name: 'Más acciones' }))
}
