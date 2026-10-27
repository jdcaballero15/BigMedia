export type TipoCosto = 'alquiler' | 'impresion' | 'fijacion' | 'comision' | 'otro'

export const TIPOS_COSTO: { value: TipoCosto; label: string }[] = [
  { value: 'impresion', label: 'Impresión' },
  { value: 'fijacion', label: 'Fijación' },
  { value: 'alquiler', label: 'Alquiler' },
  { value: 'comision', label: 'Comisión' },
  { value: 'otro', label: 'Otro' },
]

export type Costo = {
  id: number
  reserva: number
  tipo: TipoCosto
  tipo_nombre: string
  proveedor: number | null
  proveedor_nombre: string | null
  monto: string
  fecha: string
  anulado: boolean
  motivo_anulacion: string
}

export type Margen = {
  ingreso: string
  costo: string
  margen: string
  porcentaje: number | null
}

export type CostoListado = Costo & {
  cartel_nombre: string
  campania: number
  campania_nombre: string
}
