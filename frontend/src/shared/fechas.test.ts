import { expect, test } from 'vitest'
import {
  FECHA_INVALIDA,
  MENSAJE_FECHA_INVALIDA,
  dateAIso,
  erroresDeFechas,
  formatearFecha,
  formatearPeriodo,
  isoADate,
  parsearFecha,
} from './fechas'

test('formatearFecha_iso_devuelveDiaMesAnio', () => {
  expect(formatearFecha('2026-11-01')).toBe('01/11/2026')
})

test('formatearFecha_vacioONulo_devuelveVacio', () => {
  expect(formatearFecha('')).toBe('')
  expect(formatearFecha(null)).toBe('')
  expect(formatearFecha(undefined)).toBe('')
})

test('formatearFecha_textoQueNoEsIso_loDevuelveIgual', () => {
  expect(formatearFecha('mañana')).toBe('mañana')
})

test('formatearPeriodo_anioMes_devuelveMesAnio', () => {
  expect(formatearPeriodo('2026-11')).toBe('11/2026')
  expect(formatearPeriodo('')).toBe('')
})

test('parsearFecha_diaMesAnio_devuelveIso', () => {
  expect(parsearFecha('01/11/2026')).toBe('2026-11-01')
  expect(parsearFecha(' 1/2/2026 ')).toBe('2026-02-01')
})

test('parsearFecha_bisiesto_aceptaElVeintinueve', () => {
  expect(parsearFecha('29/02/2028')).toBe('2028-02-29')
})

test('parsearFecha_diaInexistente_devuelveNull', () => {
  expect(parsearFecha('31/02/2026')).toBeNull()
  expect(parsearFecha('29/02/2026')).toBeNull()
  expect(parsearFecha('00/10/2026')).toBeNull()
  expect(parsearFecha('10/13/2026')).toBeNull()
})

test('parsearFecha_incompletoOMalFormado_devuelveNull', () => {
  expect(parsearFecha('01/11')).toBeNull()
  expect(parsearFecha('01/11/26')).toBeNull()
  expect(parsearFecha('2026-11-01')).toBeNull()
  expect(parsearFecha('')).toBeNull()
})

test('isoADate_iso_devuelveDiaLocalSinCorrimiento', () => {
  const fecha = isoADate('2026-11-01')
  expect(fecha?.getFullYear()).toBe(2026)
  expect(fecha?.getMonth()).toBe(10)
  expect(fecha?.getDate()).toBe(1)
})

test('isoADate_vacioOInvalido_devuelveUndefined', () => {
  expect(isoADate('')).toBeUndefined()
  expect(isoADate(FECHA_INVALIDA)).toBeUndefined()
})

test('erroresDeFechas_algunaInvalida_devuelveSoloEsasConElMensaje', () => {
  expect(
    erroresDeFechas({ fecha_inicio: FECHA_INVALIDA, fecha_fin: '2026-11-30', otra: '' }),
  ).toEqual({ fecha_inicio: [MENSAJE_FECHA_INVALIDA] })
})

test('erroresDeFechas_todasValidasOVacias_devuelveVacio', () => {
  expect(erroresDeFechas({ fecha_inicio: '2026-11-01', fecha_fin: '' })).toEqual({})
})

test('dateAIso_fechaLocal_devuelveIso', () => {
  expect(dateAIso(new Date(2026, 0, 9))).toBe('2026-01-09')
})
