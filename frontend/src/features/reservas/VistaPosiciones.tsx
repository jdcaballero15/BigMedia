import { formatearFecha } from '../../shared/fechas'
import { colorDeMarca } from './colores'
import type { CartelTanda, FilaPosiciones, Ocupante } from './types'

type Props = {
  filas: FilaPosiciones[] | null
  seleccion: Map<number, CartelTanda>
  onAlternar: (fila: CartelTanda) => void
}

function nombreDe(ocupante: Ocupante): string {
  if (ocupante.es_esta_campania) return 'Esta campaña'
  return ocupante.marca_nombre ?? 'Sin marca'
}

function detalle(ocupante: Ocupante): string {
  const campania = ocupante.campania_nombre || `Campaña #${ocupante.campania_id}`
  const fechas = `${formatearFecha(ocupante.fecha_inicio)}–${formatearFecha(ocupante.fecha_fin)}`
  return `${ocupante.marca_nombre ?? 'Sin marca'} — ${campania} (${fechas})`
}

function SlotOcupado({ ocupantes }: { ocupantes: Ocupante[] }) {
  const propio = ocupantes.some((o) => o.es_esta_campania)
  const color = colorDeMarca(ocupantes[0].marca_id)
  return (
    <span
      className={`posiciones-slot${propio ? ' es-propia' : ''}`}
      style={propio ? undefined : { background: color.fondo, color: color.texto }}
      title={ocupantes.map(detalle).join('\n')}
    >
      {ocupantes.map(nombreDe).join(' · ')}
    </span>
  )
}

type SlotsProps = { fila: FilaPosiciones; elegido: boolean; onAlternar: Props['onAlternar'] }

function Slots({ fila, elegido, onAlternar }: SlotsProps) {
  const elegible = !fila.lleno && !fila.en_campania
  const primerLibre = fila.slots.findIndex((slot) => slot.length === 0)
  return fila.slots.map((slot, indice) => {
    if (slot.length > 0) return <SlotOcupado key={indice} ocupantes={slot} />
    if (elegido && indice === primerLibre) {
      return (
        <button
          key={indice}
          type="button"
          className="posiciones-slot es-seleccion"
          aria-label={`Quitar ${fila.nombre_visible}`}
          onClick={() => onAlternar(fila)}
        >
          Esta campaña
        </button>
      )
    }
    if (!elegible || elegido) return <span key={indice} className="posiciones-slot libre" />
    return (
      <button
        key={indice}
        type="button"
        className="posiciones-slot libre"
        aria-label={`Elegir slot libre en ${fila.nombre_visible}`}
        onClick={() => onAlternar(fila)}
      />
    )
  })
}

function Tentativas({ fila }: { fila: FilaPosiciones }) {
  const ajenas = fila.tentativas_detalle.filter((t) => !t.es_esta_campania)
  const propia = fila.tentativas_detalle.some((t) => t.es_esta_campania)
  return (
    <>
      {propia && <span className="posiciones-chip es-propia">Esta campaña (pendiente)</span>}
      {ajenas.length > 0 && (
        <span className="posiciones-chip" title={ajenas.map(detalle).join('\n')}>
          · {ajenas.length} tentativas
        </span>
      )}
    </>
  )
}

/** Vista Posiciones de "Agregar carteles", con el aspecto de la planilla de posiciones (HU-071). */
export default function VistaPosiciones({ filas, seleccion, onAlternar }: Props) {
  if (filas === null) return <p className="empty">Cargando carteles…</p>
  if (filas.length === 0) return <p className="empty">No hay carteles con estos filtros.</p>
  return (
    <div className="posiciones-tabla">
      <table aria-label="Posiciones">
        <thead>
          <tr>
            <th>Dirección</th>
            <th>Departamento</th>
            <th>Cantidad</th>
            <th>Slots</th>
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => (
            <tr
              key={fila.id}
              aria-label={fila.nombre_visible}
              className={fila.lleno ? 'lleno' : ''}
            >
              <td className="primary-cell">
                {fila.direccion}
                {fila.lleno && <small className="muted posiciones-lleno">Lleno</small>}
                <Tentativas fila={fila} />
              </td>
              <td>{fila.zona_nombre}</td>
              <td>{fila.capacidad}</td>
              <td>
                <div className="posiciones-scroll">
                  <Slots fila={fila} elegido={seleccion.has(fila.id)} onAlternar={onAlternar} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
