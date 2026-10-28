/** "Agencia Cordillera" → "AC"; "Ana" → "A". Para los círculos de la ficha. */
export function iniciales(nombre: string): string {
  return nombre
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((palabra) => palabra[0].toUpperCase())
    .join('')
}
