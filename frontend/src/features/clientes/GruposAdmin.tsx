import CatalogoAdmin from './CatalogoAdmin'
import type { GrupoEconomico } from './types'

type Props = {
  grupos: GrupoEconomico[]
  onChanged: () => void
}

/** Catálogo de grupos económicos (RN-016): marcas de un mismo dueño, las facture quien las facture. */
export default function GruposAdmin({ grupos, onChanged }: Props) {
  return (
    <CatalogoAdmin
      ruta="/api/clientes/grupos/"
      titulo="Grupos económicos"
      descripcion="Agrupan marcas de un mismo dueño, aunque las facturen clientes distintos."
      singular="grupo económico"
      items={grupos}
      onChanged={onChanged}
    />
  )
}
