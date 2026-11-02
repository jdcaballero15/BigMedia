type Props = {
  coincidentes: string[]
  saving: boolean
  onConfirmar: () => void
}

/** Aviso de marcas con un nombre igual o muy parecido, con la opción de guardar igual (HU-019). */
export default function AvisoDuplicados({ coincidentes, saving, onConfirmar }: Props) {
  if (coincidentes.length === 0) return null
  return (
    <div role="alert" aria-label="Posible marca duplicada">
      <p className="notice">Ya hay una marca con un nombre igual o muy parecido:</p>
      <ul>
        {coincidentes.map((texto) => (
          <li key={texto}>{texto}</li>
        ))}
      </ul>
      <button type="button" className="button-ghost" disabled={saving} onClick={onConfirmar}>
        Es otra marca, guardar igual
      </button>
    </div>
  )
}
