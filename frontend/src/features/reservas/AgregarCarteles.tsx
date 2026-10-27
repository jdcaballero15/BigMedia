import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import CampoFecha from '../../shared/CampoFecha'
import { FECHA_INVALIDA } from '../../shared/fechas'
import { formatearMonto, sumarMontos } from '../facturacion/montos'
import type { Catalogo } from '../inventario/types'
import type { CartelTanda, ResultadoTanda } from './types'

/** Carteles por pedido: la pantalla manda la selección por lotes para mostrar el avance. */
export const TAMANO_LOTE = 25

export type LineaTanda = {
  formato: number
  formato_nombre: string
  solicitadas: number | null
  reservadas: number
}

type Props = {
  campaniaId: number
  /** Fechas de la campaña, "" si no las tiene: entonces se piden para la tanda. */
  fechaInicio: string
  fechaFin: string
  linea: LineaTanda
  onCerrar: () => void
  /** Se llama cuando se crearon reservas, para recargar el seguimiento y la lista. */
  onCreadas: () => void
}

type Filtros = { zona: string; proveedor: string; q: string }
type Fase = { tipo: 'eligiendo' } | { tipo: 'creando'; hechos: number; total: number }

function fechaValida(valor: string): boolean {
  return valor !== '' && valor !== FECHA_INVALIDA
}

function textoAvance(linea: LineaTanda, seleccionados: number): string {
  if (linea.solicitadas === null) return `${linea.formato_nombre}: ${seleccionados} seleccionados`
  const total = linea.reservadas + seleccionados
  return `${linea.formato_nombre} ${total} de ${linea.solicitadas}`
}

/** Crea las reservas de a lotes y junta los resúmenes; un lote que falla entero va a fallidas. */
async function crearPorLotes(
  base: { campania: number; fecha_inicio: string; fecha_fin: string },
  carteles: number[],
  onAvance: (hechos: number) => void,
): Promise<ResultadoTanda> {
  const total: ResultadoTanda = { creadas: [], existentes: [], fallidas: [] }
  for (let desde = 0; desde < carteles.length; desde += TAMANO_LOTE) {
    const lote = carteles.slice(desde, desde + TAMANO_LOTE)
    try {
      const parcial = await apiWrite<ResultadoTanda>('/api/reservas/reservas/en-bloque/', 'POST', {
        ...base,
        carteles: lote,
      })
      total.creadas.push(...parcial.creadas)
      total.existentes.push(...parcial.existentes)
      total.fallidas.push(...parcial.fallidas)
    } catch {
      const motivo = 'No se pudo completar el pedido. Reintentá.'
      total.fallidas.push(...lote.map((cartel) => ({ cartel, motivo })))
    }
    onAvance(desde + lote.length)
  }
  return total
}

/** "Agregar carteles" desde una línea de formato (HU-056) y creación en bloque (HU-057). */
export default function AgregarCarteles(props: Props) {
  const { campaniaId, linea, onCerrar, onCreadas } = props
  const [desde, setDesde] = useState(props.fechaInicio)
  const [hasta, setHasta] = useState(props.fechaFin)
  const [filtros, setFiltros] = useState<Filtros>({ zona: '', proveedor: '', q: '' })
  const [zonas, setZonas] = useState<Catalogo[]>([])
  const [proveedores, setProveedores] = useState<Catalogo[]>([])
  const [filas, setFilas] = useState<CartelTanda[] | null>(null)
  const [error, setError] = useState('')
  const [seleccion, setSeleccion] = useState<Map<number, CartelTanda>>(new Map())
  const [aviso, setAviso] = useState(false)
  const [fase, setFase] = useState<Fase>({ tipo: 'eligiendo' })
  const [resultado, setResultado] = useState<ResultadoTanda | null>(null)
  // Después de una tanda se recarga la lista: lo creado pasa a "ya en la campaña".
  const [recarga, setRecarga] = useState(0)
  const fechasListas = fechaValida(desde) && fechaValida(hasta)

  useEffect(() => {
    let active = true
    void Promise.all([
      apiGet<Catalogo[]>('/api/inventario/zonas/'),
      apiGet<Catalogo[]>('/api/inventario/proveedores/'),
    ])
      .then(([zonasRows, proveedoresRows]) => {
        if (active) {
          setZonas(zonasRows)
          setProveedores(proveedoresRows)
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los filtros.')
      })
    return () => {
      active = false
    }
  }, [])

  const consulta = new URLSearchParams({
    campania: String(campaniaId),
    formato: String(linea.formato),
    desde,
    hasta,
    ...(filtros.zona && { zona: filtros.zona }),
    ...(filtros.proveedor && { proveedor: filtros.proveedor }),
    ...(filtros.q.trim() && { q: filtros.q.trim() }),
  }).toString()

  useEffect(() => {
    if (!fechasListas) return
    let active = true
    void apiGet<CartelTanda[]>(`/api/reservas/carteles-para-tanda/?${consulta}`)
      .then((rows) => {
        if (active) {
          setFilas(rows)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los carteles.')
      })
    return () => {
      active = false
    }
  }, [consulta, fechasListas, recarga])

  function cambiarFecha(campo: 'desde' | 'hasta', valor: string) {
    // Con otras fechas cambia qué carteles están libres: la selección empieza de nuevo.
    setSeleccion(new Map())
    setFilas(null)
    if (campo === 'desde') setDesde(valor)
    else setHasta(valor)
  }

  function alternar(fila: CartelTanda) {
    setSeleccion((actual) => {
      const nueva = new Map(actual)
      if (nueva.has(fila.id)) nueva.delete(fila.id)
      else nueva.set(fila.id, fila)
      return nueva
    })
  }

  function seleccionarFiltrados() {
    setSeleccion((actual) => {
      const nueva = new Map(actual)
      for (const fila of filas ?? []) if (!fila.en_campania) nueva.set(fila.id, fila)
      return nueva
    })
  }

  async function crear(carteles: number[]) {
    setAviso(false)
    setFase({ tipo: 'creando', hechos: 0, total: carteles.length })
    const base = { campania: campaniaId, fecha_inicio: desde, fecha_fin: hasta }
    const total = await crearPorLotes(base, carteles, (hechos) =>
      setFase({ tipo: 'creando', hechos, total: carteles.length }),
    )
    setFase({ tipo: 'eligiendo' })
    setSeleccion(new Map())
    setResultado(total)
    setRecarga((actual) => actual + 1)
    if (total.creadas.length > 0) onCreadas()
  }

  function confirmar() {
    const esperado = linea.solicitadas
    if (esperado !== null && linea.reservadas + seleccion.size !== esperado && !aviso) {
      setAviso(true)
      return
    }
    void crear([...seleccion.keys()])
  }

  const nombres = new Map((filas ?? []).map((fila) => [fila.id, fila.nombre_visible]))
  for (const [id, fila] of seleccion) nombres.set(id, fila.nombre_visible)
  const monto = sumarMontos([...seleccion.values()].map((fila) => fila.tarifa_lista ?? '0'))

  return (
    <section className="card edit-form section-gap" aria-label="Agregar carteles">
      <div className="form-heading">
        <h3>Agregar carteles · {linea.formato_nombre}</h3>
        <button type="button" className="button-ghost" onClick={onCerrar}>
          Cerrar
        </button>
      </div>
      <div className="form-grid">
        <CampoFecha label="Desde" value={desde} onChange={(v) => cambiarFecha('desde', v)} />
        <CampoFecha label="Hasta" value={hasta} onChange={(v) => cambiarFecha('hasta', v)} />
      </div>
      {!fechasListas && (
        <p className="notice">Indicá las fechas de la tanda para ver los carteles libres.</p>
      )}
      <div className="filters">
        <label>
          Zona
          <select
            value={filtros.zona}
            onChange={(event) => setFiltros({ ...filtros, zona: event.target.value })}
          >
            <option value="">Todas</option>
            {zonas.map((zona) => (
              <option key={zona.id} value={zona.id}>
                {zona.nombre}
              </option>
            ))}
          </select>
        </label>
        <label>
          Proveedor
          <select
            value={filtros.proveedor}
            onChange={(event) => setFiltros({ ...filtros, proveedor: event.target.value })}
          >
            <option value="">Todos</option>
            {proveedores.map((proveedor) => (
              <option key={proveedor.id} value={proveedor.id}>
                {proveedor.nombre}
              </option>
            ))}
          </select>
        </label>
        <label>
          Dirección
          <input
            value={filtros.q}
            placeholder="Buscar dirección"
            onChange={(event) => setFiltros({ ...filtros, q: event.target.value })}
          />
        </label>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {resultado && (
        <Resumen
          resultado={resultado}
          nombres={nombres}
          onReintentar={() => void crear(resultado.fallidas.map((item) => item.cartel))}
          deshabilitado={fase.tipo === 'creando'}
        />
      )}
      {fase.tipo === 'creando' ? (
        <p className="muted" role="status">
          Creando reservas… {fase.hechos} de {fase.total}
          <progress value={fase.hechos} max={fase.total} />
        </p>
      ) : (
        <div className="section-heading">
          <p className="costos-total">
            <strong>{textoAvance(linea, seleccion.size)}</strong> · Monto estimado{' '}
            {formatearMonto(monto)}
          </p>
          <div className="row-actions">
            <button
              type="button"
              className="button-ghost"
              onClick={seleccionarFiltrados}
              disabled={!filas?.length}
            >
              Seleccionar todos los filtrados
            </button>
            <button
              type="button"
              className="button-primary"
              onClick={confirmar}
              disabled={seleccion.size === 0 || !fechasListas}
            >
              {aviso ? 'Crear igual' : 'Crear reservas'}
            </button>
          </div>
        </div>
      )}
      {aviso && (
        <p className="notice" role="alert">
          La selección no coincide con lo solicitado ({linea.reservadas + seleccion.size} de{' '}
          {linea.solicitadas}). Podés crear igual o ajustar la selección.
        </p>
      )}
      {fechasListas && <TablaTanda filas={filas} seleccion={seleccion} onAlternar={alternar} />}
    </section>
  )
}

type TablaProps = {
  filas: CartelTanda[] | null
  seleccion: Map<number, CartelTanda>
  onAlternar: (fila: CartelTanda) => void
}

function TablaTanda({ filas, seleccion, onAlternar }: TablaProps) {
  if (filas === null) return <p className="empty">Cargando carteles…</p>
  if (filas.length === 0) return <p className="empty">No hay carteles libres con estos filtros.</p>
  return (
    <table aria-label="Carteles libres">
      <thead>
        <tr>
          <th>Elegir</th>
          <th>Cartel</th>
          <th>Zona</th>
          <th>Proveedor</th>
          <th>Cupo</th>
          <th>Tarifa de lista</th>
        </tr>
      </thead>
      <tbody>
        {filas.map((fila) => (
          <tr key={fila.id}>
            <td>
              <input
                type="checkbox"
                aria-label={`Elegir ${fila.nombre_visible}`}
                checked={seleccion.has(fila.id)}
                disabled={fila.en_campania}
                onChange={() => onAlternar(fila)}
              />
            </td>
            <td className="primary-cell">
              {fila.nombre_visible}
              {fila.en_campania && <small className="muted"> · ya en la campaña</small>}
              {fila.tentativas > 0 && (
                <small className="notice"> · {fila.tentativas} tentativas</small>
              )}
            </td>
            <td>{fila.zona_nombre}</td>
            <td>{fila.proveedor_nombre ?? '—'}</td>
            <td>
              {fila.ocupados} de {fila.capacidad}
            </td>
            <td>
              {fila.tarifa_lista === null ? (
                <span className="notice">Sin tarifa</span>
              ) : (
                formatearMonto(fila.tarifa_lista)
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

type ResumenProps = {
  resultado: ResultadoTanda
  nombres: Map<number, string>
  onReintentar: () => void
  deshabilitado: boolean
}

function Resumen({ resultado, nombres, onReintentar, deshabilitado }: ResumenProps) {
  const { creadas, existentes, fallidas } = resultado
  return (
    <div className="card" role="status" aria-label="Resumen de la tanda">
      <p>
        Se crearon {creadas.length} reservas Pendientes.
        {existentes.length > 0 && ` ${existentes.length} ya existían y no se duplicaron.`}
      </p>
      {fallidas.length > 0 && (
        <>
          <p className="error">Fallaron {fallidas.length}:</p>
          <ul aria-label="Reservas fallidas">
            {fallidas.map((item) => (
              <li key={item.cartel}>
                {nombres.get(item.cartel) ?? `Cartel #${item.cartel}`}: {item.motivo}
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="button-primary"
            onClick={onReintentar}
            disabled={deshabilitado}
          >
            Reintentar fallidas
          </button>
        </>
      )}
    </div>
  )
}
