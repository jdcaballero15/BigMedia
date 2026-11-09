import { useState } from 'react'
import { apiWrite } from '../../shared/api'
import { formatearFecha } from '../../shared/fechas'
import { usePuedeEditar } from '../../shared/sesion'
import type { OrdenPublicidad } from './types'
import { urlArchivoOrdenPublicidad } from './types'

type Props = {
  ordenes: OrdenPublicidad[]
}

/** Órdenes de publicidad de la campaña: abrir y dar de baja (HU-069). */
export default function OrdenesPublicidad({ ordenes: iniciales }: Props) {
  const puedeEditar = usePuedeEditar()
  const [ordenes, setOrdenes] = useState(iniciales)
  const [error, setError] = useState('')
  const vigentes = ordenes.filter((orden) => orden.activa)
  const dadasDeBaja = ordenes.filter((orden) => !orden.activa)

  async function darDeBaja(orden: OrdenPublicidad) {
    if (!window.confirm(`¿Dar de baja la orden ${orden.nombre}? Seguirá en el histórico.`)) return
    setError('')
    try {
      const actualizada = await apiWrite<OrdenPublicidad>(
        `/api/campanias/ordenes-publicidad/${orden.id}/dar-de-baja/`,
        'POST',
      )
      setOrdenes((actuales) =>
        actuales.map((item) => (item.id === actualizada.id ? actualizada : item)),
      )
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudo dar de baja la orden.')
    }
  }

  function datos(orden: OrdenPublicidad) {
    return (
      <>
        <a href={urlArchivoOrdenPublicidad(orden.id)} target="_blank" rel="noreferrer">
          {orden.nombre}
        </a>{' '}
        · {orden.subida_por_nombre} · {formatearFecha(orden.subida_en.slice(0, 10))}
      </>
    )
  }

  return (
    <section className="card section-gap" aria-label="Órdenes de publicidad">
      <div className="card-heading">
        <h3>Órdenes de publicidad</h3>
      </div>
      <div className="card-cuerpo">
        {vigentes.length === 0 ? (
          <p className="muted">Sin órdenes de publicidad.</p>
        ) : (
          <ul>
            {vigentes.map((orden) => (
              <li key={orden.id}>
                {datos(orden)}
                {puedeEditar && (
                  <>
                    {' '}
                    <button
                      type="button"
                      className="button-ghost"
                      onClick={() => void darDeBaja(orden)}
                    >
                      Dar de baja {orden.nombre}
                    </button>
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
        {dadasDeBaja.length > 0 && (
          <details>
            <summary>Dadas de baja ({dadasDeBaja.length})</summary>
            <ul>
              {dadasDeBaja.map((orden) => (
                <li key={orden.id}>{datos(orden)}</li>
              ))}
            </ul>
          </details>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </div>
    </section>
  )
}
