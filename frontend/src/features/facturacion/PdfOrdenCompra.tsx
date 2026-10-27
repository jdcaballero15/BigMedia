import { useState } from 'react'
import { ApiError, apiUpload, apiWrite } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import type { PdfOrdenCompra as Pdf } from './types'
import { urlPdfOrdenCompra } from './types'

type Props = {
  itemId: number | null
  pdf: Pdf | null
  onCambio: () => void
}

/** Adjuntar, abrir y quitar el PDF de la orden de compra de un ítem guardado (HU-062). */
export default function PdfOrdenCompra({ itemId, pdf: inicial, onCambio }: Props) {
  const [pdf, setPdf] = useState<Pdf | null>(inicial)
  const [errores, setErrores] = useState<string[]>([])
  const [ocupado, setOcupado] = useState(false)

  if (itemId === null) {
    return <p className="muted wide">Guardá el ítem para adjuntar el PDF de la orden de compra.</p>
  }
  const url = urlPdfOrdenCompra(itemId)

  async function operar(accion: () => Promise<Pdf | null>) {
    setErrores([])
    setOcupado(true)
    try {
      setPdf(await accion())
      onCambio()
    } catch (cause) {
      const campos = cause instanceof ApiError ? cause.fields : {}
      setErrores(campos.archivo ?? campos.estado ?? ['No se pudo actualizar el PDF.'])
    } finally {
      setOcupado(false)
    }
  }

  function subir(archivo: File | undefined) {
    if (!archivo) return
    const form = new FormData()
    form.append('archivo', archivo)
    void operar(() => apiUpload<Pdf>(url, form))
  }

  return (
    <div className="wide">
      <label>
        PDF de la orden de compra
        <input
          type="file"
          accept="application/pdf,.pdf"
          disabled={ocupado}
          onChange={(event) => {
            subir(event.target.files?.[0])
            event.target.value = ''
          }}
        />
      </label>
      {pdf && (
        <p>
          <a href={url} target="_blank" rel="noreferrer">
            Abrir {pdf.nombre}
          </a>{' '}
          <button
            type="button"
            className="button-ghost"
            disabled={ocupado}
            onClick={() =>
              void operar(async () => {
                await apiWrite(url, 'DELETE')
                return null
              })
            }
          >
            Quitar PDF
          </button>
        </p>
      )}
      {ocupado && <p className="muted">Actualizando el PDF…</p>}
      <FieldErrors messages={errores} />
    </div>
  )
}
