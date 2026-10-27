import { useState } from 'react'
import ReservasCampania from '../reservas/ReservasCampania'
import RentabilidadCampania from '../costos/RentabilidadCampania'
import InteraccionesLista from './InteraccionesLista'
import PosicionesPorFormato from './PosicionesPorFormato'
import type { Campania } from './types'
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
          {puedeEditar && (
            <button className="button-primary" onClick={onEditar}>
              Editar
            </button>
          )}
        </div>
      </div>
      <div className="card">
        <dl className="detail-grid">
          <div>
            <dt>Estado</dt>
            <dd>{etiquetaEstado(campania.estado)}</dd>
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
