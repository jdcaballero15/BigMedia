import CatalogoAdmin from './CatalogoAdmin'
import type { Rubro } from './types'

type Props = {
  rubros: Rubro[]
  onChanged: () => void
}

export default function RubrosAdmin({ rubros, onChanged }: Props) {
  return (
    <CatalogoAdmin
      ruta="/api/clientes/rubros/"
      titulo="Rubros"
      descripcion="Catálogo para clasificar las marcas."
      singular="rubro"
      items={rubros}
      onChanged={onChanged}
    />
  )
}
