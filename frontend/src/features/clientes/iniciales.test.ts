import { expect, test } from 'vitest'
import { iniciales } from './iniciales'

test('iniciales_nombreDeVariasPalabras_tomaLasDosPrimeras', () => {
  expect(iniciales('Agencia Cordillera Sur')).toBe('AC')
  expect(iniciales(' ana ')).toBe('A')
  expect(iniciales('')).toBe('')
})
