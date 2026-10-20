import ReservasCampania from '../reservas/ReservasCampania'
import RentabilidadCampania from '../costos/RentabilidadCampania'
import type { Campania } from './types'
import { etiquetaEstado } from './types'

type Props = {
  campania: Campania
  onEditar: () => void
  onVolver: () => void
}

export default function CampaniaDetalle({ campania, onEditar, onVolver }: Props) {
  const periodo =
    campania.fecha_inicio && campania.fecha_fin
      ? `${campania.fecha_inicio} → ${campania.fecha_fin}`
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
          <button className="button-primary" onClick={onEditar}>
            Editar
          </button>
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
      <ReservasCampania campaniaId={campania.id} />
      <RentabilidadCampania campaniaId={campania.id} />
    </section>
  )
}
