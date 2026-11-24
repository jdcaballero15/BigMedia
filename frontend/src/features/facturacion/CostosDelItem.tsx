import { useEffect, useState } from 'react'
import type { KeyboardEvent, ReactNode } from 'react'
import { apiGet } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { detalleElegidos, formatearMonto, sumaElegidos } from './montos'
import type { CostoElegible } from './types'
import { URL_COSTOS_ELEGIBLES } from './types'

type Props = {
  elegidos: CostoElegible[]
  onCambiar: (elegidos: CostoElegible[]) => void
  errores?: string[]
}

function Origen({ costo }: { costo: CostoElegible }) {
  if (costo.propio) return <>Propio del ítem</>
  return (
    <>
      {costo.campania_nombre}
      {costo.cartel_nombre && <small className="muted"> · {costo.cartel_nombre}</small>}
    </>
  )
}

type FilaProps = { costo: CostoElegible; accion: ReactNode }

function Fila({ costo, accion }: FilaProps) {
  return (
    <tr className={costo.anulado ? 'muted' : undefined}>
      <td>
        {costo.tipo_nombre}
        {costo.anulado && <small> (anulado)</small>}
      </td>
      <td>
        <Origen costo={costo} />
      </td>
      <td>{costo.a_quien || '—'}</td>
      <td>{formatearMonto(costo.monto)}</td>
      <td>{accion}</td>
    </tr>
  )
}

function Tabla({ nombre, children }: { nombre: string; children: ReactNode }) {
  return (
    <table aria-label={nombre}>
      <thead>
        <tr>
          <th>Tipo</th>
          <th>Campaña y cartel</th>
          <th>A quién se le paga</th>
          <th>Monto</th>
          <th></th>
        </tr>
      </thead>
      <tbody>{children}</tbody>
    </table>
  )
}

/** Costos del ítem (HU-063): se eligen entre los cargados de cualquier campaña y viajan al
 * guardar el ítem. Un costo propio del ítem no se quita: se anula desde Costos. */
export default function CostosDelItem({ elegidos, onCambiar, errores }: Props) {
  const [busqueda, setBusqueda] = useState('')
  const [consulta, setConsulta] = useState('')
  const [resultados, setResultados] = useState<CostoElegible[] | null>(null)
  const [falla, setFalla] = useState('')

  useEffect(() => {
    let active = true
    const url = consulta
      ? `${URL_COSTOS_ELEGIBLES}?q=${encodeURIComponent(consulta)}`
      : URL_COSTOS_ELEGIBLES
    apiGet<CostoElegible[]>(url)
      .then((lista) => {
        if (!active) return
        setResultados(lista)
        setFalla('')
      })
      .catch(() => {
        if (active) setFalla('No se pudieron buscar los costos.')
      })
    return () => {
      active = false
    }
  }, [consulta])

  // Enter busca sin mandar el formulario del ítem.
  function alTeclear(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== 'Enter') return
    event.preventDefault()
    setConsulta(busqueda.trim())
  }

  const ids = new Set(elegidos.map((costo) => costo.id))
  const disponibles = (resultados ?? []).filter((costo) => !ids.has(costo.id))
  const suma = sumaElegidos(elegidos)

  return (
    <fieldset className="wide">
      <legend>Costos del ítem</legend>
      {elegidos.length === 0 && <p className="muted">El ítem no tiene costos elegidos.</p>}
      {elegidos.length > 0 && (
        <Tabla nombre="Costos elegidos">
          {elegidos.map((costo) => (
            <Fila
              key={costo.id}
              costo={costo}
              accion={
                costo.propio ? (
                  <small className="muted">Se anula desde Costos</small>
                ) : (
                  <button
                    type="button"
                    className="button-ghost"
                    onClick={() => onCambiar(elegidos.filter((otro) => otro.id !== costo.id))}
                  >
                    Quitar
                  </button>
                )
              }
            />
          ))}
        </Tabla>
      )}
      {suma !== null && (
        <p aria-label="Suma de los costos elegidos">
          Costos incluidos <strong>{formatearMonto(suma)}</strong>{' '}
          <small className="muted">({detalleElegidos(elegidos)})</small>
        </p>
      )}
      <FieldErrors messages={errores} />
      <label>
        Buscar costos
        <input
          type="search"
          value={busqueda}
          placeholder="Campaña, cartel, tipo o a quién se le paga"
          onChange={(event) => setBusqueda(event.target.value)}
          onKeyDown={alTeclear}
        />
      </label>
      <button type="button" className="button-ghost" onClick={() => setConsulta(busqueda.trim())}>
        Buscar
      </button>
      {falla && <p className="error">{falla}</p>}
      {resultados !== null && disponibles.length === 0 && !falla && (
        <p className="muted">No hay costos para elegir con esa búsqueda.</p>
      )}
      {disponibles.length > 0 && (
        <Tabla nombre="Costos para elegir">
          {disponibles.map((costo) => (
            <Fila
              key={costo.id}
              costo={costo}
              accion={
                <button
                  type="button"
                  className="button-ghost"
                  onClick={() => onCambiar([...elegidos, costo])}
                >
                  Elegir
                </button>
              }
            />
          ))}
        </Tabla>
      )}
    </fieldset>
  )
}
