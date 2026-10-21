export type Periodo = { mes: string; etiqueta: string }

export type MarcaFila = {
  marca: number | null
  nombre: string
  total: string
  por_mes: Record<string, string>
}

export type ClienteFila = {
  cliente: number | null
  nombre: string
  total: string
  por_mes: Record<string, string>
  marcas: MarcaFila[]
}

export type ReporteIngresos = {
  periodos: Periodo[]
  clientes: ClienteFila[]
  total: string
}
