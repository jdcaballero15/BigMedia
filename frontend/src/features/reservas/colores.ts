/** Colores de marca de la vista Posiciones (HU-071): cada marca tiene siempre el mismo. */
export type ColorMarca = { fondo: string; texto: string }

export const PALETA_MARCAS: readonly ColorMarca[] = [
  { fondo: '#ad1457', texto: '#ffffff' },
  { fondo: '#1565c0', texto: '#ffffff' },
  { fondo: '#2e7d32', texto: '#ffffff' },
  { fondo: '#ffb300', texto: '#1a1a1a' },
  { fondo: '#6a1b9a', texto: '#ffffff' },
  { fondo: '#00838f', texto: '#ffffff' },
  { fondo: '#c62828', texto: '#ffffff' },
  { fondo: '#9ccc65', texto: '#1a1a1a' },
  { fondo: '#4e342e', texto: '#ffffff' },
  { fondo: '#f48fb1', texto: '#1a1a1a' },
  { fondo: '#4fc3f7', texto: '#1a1a1a' },
  { fondo: '#455a64', texto: '#ffffff' },
]

export const COLOR_SIN_MARCA: ColorMarca = { fondo: '#e3e9f4', texto: '#4a5d7e' }

export function colorDeMarca(marcaId: number | null): ColorMarca {
  if (marcaId === null) return COLOR_SIN_MARCA
  return PALETA_MARCAS[marcaId % PALETA_MARCAS.length]
}

function luminancia(hex: string): number {
  const canales = [1, 3, 5].map((inicio) => parseInt(hex.slice(inicio, inicio + 2), 16) / 255)
  const [r, g, b] = canales.map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

/** Contraste WCAG entre dos colores "#rrggbb". */
export function contraste(a: string, b: string): number {
  const [claro, oscuro] = [luminancia(a), luminancia(b)].sort((x, y) => y - x)
  return (claro + 0.05) / (oscuro + 0.05)
}
