import type { ReactNode } from 'react'

export type Cifra = {
  etiqueta: string
  valor: ReactNode
  detalle?: ReactNode
  /** `principal`: la cifra que se entra a ver (azul lleno). `alerta`: pendiente o vencimiento. */
  tono?: 'principal' | 'alerta'
}

/** Fila de cifras al tope de una pantalla. */
export default function Cifras({ cifras, titulo }: { cifras: Cifra[]; titulo: string }) {
  return (
    <dl className="cifras" aria-label={titulo}>
      {cifras.map((cifra) => (
        <div key={cifra.etiqueta} className={cifra.tono ? `cifra cifra-${cifra.tono}` : 'cifra'}>
          <dt>{cifra.etiqueta}</dt>
          <dd>
            <strong>{cifra.valor}</strong>
            {cifra.detalle && <small>{cifra.detalle}</small>}
          </dd>
        </div>
      ))}
    </dl>
  )
}
