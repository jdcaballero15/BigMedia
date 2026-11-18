import { useState } from 'react'
import { apiWrite } from '../../shared/api'
import ReservasCampania from '../reservas/ReservasCampania'
import RentabilidadCampania from '../costos/RentabilidadCampania'
import InteraccionesLista from './InteraccionesLista'
import OrdenesPublicidad from './OrdenesPublicidad'
import PosicionesPorFormato from './PosicionesPorFormato'
import type { Campania, EstadoCampania } from './types'
import { etiquetaEstado } from './types'
import { formatearFecha } from '../../shared/fechas'
import { usePuedeEditar } from '../../shared/sesion'

type Props = {
  campania: Campania
  onEditar: () => void
  onVolver: () => void
}

export default function CampaniaDetalle({ campania, onEditar, onVolver }: Props) {
  const puedeEditar = usePuedeEditar()
  // Las posiciones y la lista de reservas se recargan cuando la otra crea o edita reservas.
  const [revisionPosiciones, setRevisionPosiciones] = useState(0)
  const [revisionReservas, setRevisionReservas] = useState(0)
  // Cancelar cambia el estado acá mismo, sin volver a la lista (HU-024).
  const [estado, setEstado] = useState<EstadoCampania>(campania.estado)
  const [errorCancelar, setErrorCancelar] = useState('')
  const [cancelando, setCancelando] = useState(false)
  const cancelada = estado === 'cancelada'

  async function cancelar() {
    const aviso =
      '¿Cancelar la campaña? Sus reservas que no empezaron se cancelan y las que están en ' +
      'exhibición terminan hoy. No se puede volver a confirmar.'
    if (!window.confirm(aviso)) return
    setCancelando(true)
    try {
      await apiWrite('/api/reservas/reservas/cancelar-campania/', 'POST', {
        campania: campania.id,
      })
      setEstado('cancelada')
      setErrorCancelar('')
      setRevisionReservas((actual) => actual + 1)
      setRevisionPosiciones((actual) => actual + 1)
    } catch (cause) {
      setErrorCancelar(cause instanceof Error ? cause.message : 'No se pudo cancelar la campaña.')
    } finally {
      setCancelando(false)
    }
  }
  const periodo =
    campania.fecha_inicio && campania.fecha_fin
      ? `${formatearFecha(campania.fecha_inicio)} → ${formatearFecha(campania.fecha_fin)}`
      : 'Sin fechas planificadas'

  return (
    <section aria-label="Detalle de campaña">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Campaña</p>
          <h2>{campania.nombre || `Campaña #${campania.id}`}</h2>
          <p className="muted">El contenedor comercial: desde acá se cargarán reservas y costos.</p>
        </div>
        <div className="row-actions">
          <button className="button-ghost" onClick={onVolver}>
            Volver
          </button>
          {puedeEditar && !cancelada && (
            <button className="button-ghost" onClick={() => void cancelar()} disabled={cancelando}>
              Cancelar campaña
            </button>
          )}
          {puedeEditar && (
            <button className="button-primary" onClick={onEditar}>
              Editar
            </button>
          )}
        </div>
      </div>
      {errorCancelar && (
        <p className="error" role="alert">
          {errorCancelar}
        </p>
      )}
      <div className="card card-cuerpo section-gap">
        <dl className="detail-grid">
          <div>
            <dt>Estado</dt>
            <dd>{etiquetaEstado(estado)}</dd>
          </div>
          <div>
            <dt>Marca</dt>
            <dd>{campania.marca_nombre ?? 'Sin marca'}</dd>
          </div>
          <div>
            <dt>Cliente que factura</dt>
            <dd>{campania.cliente_factura_nombre || 'Sin definir'}</dd>
          </div>
          <div>
            <dt>Período planificado</dt>
            <dd>{periodo}</dd>
          </div>
        </dl>
      </div>
      <OrdenesPublicidad ordenes={campania.ordenes_publicidad} />
      <PosicionesPorFormato
        campaniaId={campania.id}
        fechaInicio={campania.fecha_inicio}
        fechaFin={campania.fecha_fin}
        revisionReservas={revisionPosiciones}
        onReservasCreadas={() => setRevisionReservas((actual) => actual + 1)}
      />
      <ReservasCampania
        campaniaId={campania.id}
        revisionExterna={revisionReservas}
        campaniaCancelada={cancelada}
        onCambio={() => setRevisionPosiciones((actual) => actual + 1)}
      />
      <RentabilidadCampania campaniaId={campania.id} />
      <InteraccionesLista
        filtro={{ campania: campania.id }}
        titulo="Interacciones de la campaña"
        ocultar="campania"
      />
    </section>
  )
}
