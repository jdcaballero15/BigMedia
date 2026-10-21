import { expect, test } from 'vitest'
import { construirCsv } from './csv'

test('arma encabezados y filas con separador punto y coma y coma decimal', () => {
  const csv = construirCsv(['Cliente', 'Total'], [['Agencia A', 1500.5]])
  expect(csv).toBe('"Cliente";"Total"\r\n"Agencia A";1500,5')
})

test('escapa las comillas internas duplicándolas', () => {
  const csv = construirCsv(['Nombre'], [['Agencia "Norte"']])
  expect(csv).toBe('"Nombre"\r\n"Agencia ""Norte"""')
})

test('un texto con punto y coma queda contenido entre comillas', () => {
  const csv = construirCsv(['X'], [['a;b']])
  expect(csv).toBe('"X"\r\n"a;b"')
})
