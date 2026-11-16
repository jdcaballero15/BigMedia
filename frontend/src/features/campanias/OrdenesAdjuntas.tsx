import { FieldErrors } from '../../shared/FieldErrors'

type Props = {
  archivos: File[]
  onCambio: (archivos: File[]) => void
  errores?: string[]
}

/** PDF de la orden de publicidad que se guardan junto con la campaña (HU-069). */
export default function OrdenesAdjuntas({ archivos, onCambio, errores }: Props) {
  return (
    <div className="wide">
      <label>
        Orden de publicidad (PDF)
        <input
          type="file"
          accept="application/pdf,.pdf"
          multiple
          onChange={(event) => {
            onCambio([...archivos, ...Array.from(event.target.files ?? [])])
            event.target.value = ''
          }}
        />
      </label>
      {archivos.length > 0 && (
        <ul aria-label="Órdenes de publicidad a adjuntar">
          {archivos.map((archivo, indice) => (
            <li key={`${archivo.name}-${indice}`}>
              {archivo.name}{' '}
              <button
                type="button"
                className="button-ghost"
                onClick={() => onCambio(archivos.filter((_, otro) => otro !== indice))}
              >
                Sacar {archivo.name}
              </button>
            </li>
          ))}
        </ul>
      )}
      <FieldErrors messages={errores} />
    </div>
  )
}
