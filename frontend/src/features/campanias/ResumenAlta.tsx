import type { ResultadoAlta } from './altaConPosiciones'

type Props = { resultado: ResultadoAlta; onCerrar: () => void }

/** Resumen del alta con líneas y carteles: qué se creó y qué falló, con su motivo (HU-056). */
export default function ResumenAlta({ resultado, onCerrar }: Props) {
  const { campania, reservasCreadas, lineasFallidas, cartelesFallidos } = resultado
  const nombre = campania || 'sin nombre'
  return (
    <div className="card section-gap" role="status" aria-label="Resultado del alta">
      <div className="form-heading">
        <p>
          Se creó la campaña «{nombre}» con {reservasCreadas}{' '}
          {reservasCreadas === 1 ? 'reserva' : 'reservas'}.
        </p>
        <button type="button" className="button-ghost" onClick={onCerrar}>
          Cerrar
        </button>
      </div>
      {lineasFallidas.length > 0 && (
        <>
          <p className="error">No se pudieron guardar estas líneas de formato:</p>
          <ul aria-label="Líneas fallidas">
            {lineasFallidas.map((item) => (
              <li key={item.formato}>
                {item.formato}: {item.motivo}
              </li>
            ))}
          </ul>
        </>
      )}
      {cartelesFallidos.length > 0 && (
        <>
          <p className="error">No se pudieron reservar estos carteles:</p>
          <ul aria-label="Carteles fallidos">
            {cartelesFallidos.map((item) => (
              <li key={item.cartel}>
                {item.cartel}: {item.motivo}
              </li>
            ))}
          </ul>
          <p className="muted">Podés agregarlos después desde el detalle de la campaña.</p>
        </>
      )}
    </div>
  )
}
