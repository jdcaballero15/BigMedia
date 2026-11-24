import { FieldErrors } from '../../shared/FieldErrors'
import type { PdfOrdenCompra } from './types'
import { urlPdfOrdenCompra } from './types'

type Props = {
  itemId: number | null
  /** El PDF que ya tiene el ítem guardado. */
  pdf: PdfOrdenCompra | null
  /** El PDF elegido que se sube al guardar el ítem. */
  archivo: File | null
  onElegir: (archivo: File | null) => void
  errores?: string[]
}

/** Orden de publicidad del ítem (HU-062): se adjunta o reemplaza y viaja al guardar el ítem. */
export default function OrdenPublicidadItem({ itemId, pdf, archivo, onElegir, errores }: Props) {
  return (
    <fieldset className="wide">
      <legend>Orden de publicidad</legend>
      {itemId !== null && pdf && (
        <p>
          <a href={urlPdfOrdenCompra(itemId)} target="_blank" rel="noreferrer">
            Abrir {pdf.nombre}
          </a>
        </p>
      )}
      {!pdf && !archivo && <p className="muted">El ítem no tiene orden de publicidad.</p>}
      <label>
        {pdf ? 'Reemplazar PDF' : 'Adjuntar PDF'}
        <input
          type="file"
          accept="application/pdf,.pdf"
          onChange={(event) => {
            onElegir(event.target.files?.[0] ?? null)
            event.target.value = ''
          }}
        />
      </label>
      {archivo && (
        <p>
          Se adjunta al guardar: <strong>{archivo.name}</strong>{' '}
          <button type="button" className="button-ghost" onClick={() => onElegir(null)}>
            No adjuntar
          </button>
        </p>
      )}
      <FieldErrors messages={errores} />
    </fieldset>
  )
}
