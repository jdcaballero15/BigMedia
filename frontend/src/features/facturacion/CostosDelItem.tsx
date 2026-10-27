import { useEffect, useState } from 'react'
import { ApiError, apiGet, apiWrite } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { TIPOS_COSTO } from '../costos/types'
import type { Proveedor } from '../inventario/types'
import { formatearMonto, sumarMontos } from './montos'
import type { CostoDelItem } from './types'
import { urlCostosDelItem } from './types'

type Props = {
  itemId: number | null
  campania: number | null
  onCambio: () => void
}

type Errores = Record<string, string[]>

const NUEVO = { tipo: 'comision', modo: 'monto', valor: '', proveedor: '', destinatario: '' }

function aQuien(costo: CostoDelItem): string {
  return costo.proveedor_nombre ?? (costo.destinatario || '—')
}

function importe(costo: CostoDelItem): string {
  const monto = formatearMonto(costo.monto)
  return costo.porcentaje ? `${monto} (${costo.porcentaje} %)` : monto
}

function errores(cause: unknown, general: string): Errores {
  const campos = cause instanceof ApiError ? cause.fields : {}
  return Object.keys(campos).length ? campos : { general: [general] }
}

/** Costos de un ítem guardado (HU-063): fijos o en porcentaje del neto, y de reservas vinculadas. */
export default function CostosDelItem({ itemId, campania, onCambio }: Props) {
  const [costos, setCostos] = useState<CostoDelItem[] | null>(null)
  const [vinculables, setVinculables] = useState<CostoDelItem[]>([])
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [nuevo, setNuevo] = useState(NUEVO)
  const [vincular, setVincular] = useState('')
  const [anulando, setAnulando] = useState<{ id: number; motivo: string } | null>(null)
  const [fallas, setFallas] = useState<Errores>({})
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    if (itemId === null) return
    let active = true
    const url = urlCostosDelItem(itemId)
    void Promise.all([
      apiGet<CostoDelItem[]>(url),
      campania === null ? Promise.resolve([]) : apiGet<CostoDelItem[]>(`${url}vinculables/`),
      apiGet<Proveedor[]>('/api/inventario/proveedores/'),
    ])
      .then(([lista, deReservas, activos]) => {
        if (!active) return
        setCostos(lista)
        setVinculables(deReservas)
        setProveedores(activos)
      })
      .catch(() => {
        if (active) setFallas({ general: ['No se pudieron cargar los costos del ítem.'] })
      })
    return () => {
      active = false
    }
  }, [itemId, campania, revision])

  if (itemId === null) {
    return <p className="muted wide">Guardá el ítem para cargar sus costos.</p>
  }
  const url = urlCostosDelItem(itemId)

  async function escribir(path: string, body: unknown, general: string) {
    setFallas({})
    try {
      await apiWrite(path, 'POST', body)
    } catch (cause) {
      setFallas(errores(cause, general))
      return false
    }
    setRevision((actual) => actual + 1)
    onCambio()
    return true
  }

  async function agregar() {
    const { modo, valor, proveedor, destinatario, tipo } = nuevo
    const cuerpo = {
      tipo,
      [modo]: valor.trim() || null,
      proveedor: proveedor ? Number(proveedor) : null,
      destinatario: destinatario.trim(),
    }
    if (await escribir(url, cuerpo, 'No se pudo cargar el costo.')) setNuevo(NUEVO)
  }

  async function anular() {
    if (anulando === null) return
    const cuerpo = { motivo: anulando.motivo }
    if (await escribir(`${url}${anulando.id}/anular/`, cuerpo, 'No se pudo anular el costo.')) {
      setAnulando(null)
    }
  }

  const cambiar = (campo: keyof typeof NUEVO, valor: string) =>
    setNuevo((actual) => ({ ...actual, [campo]: valor }))
  const vigentes = (costos ?? []).filter((costo) => !costo.anulado).map((costo) => costo.monto)

  return (
    <fieldset className="wide">
      <legend>Costos del ítem</legend>
      {costos?.length === 0 && <p className="muted">El ítem no tiene costos.</p>}
      {costos && costos.length > 0 && (
        <table aria-label="Costos del ítem">
          <thead>
            <tr>
              <th>Tipo</th>
              <th>A quién se le paga</th>
              <th>Importe</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {costos.map((costo) => (
              <tr key={costo.id} className={costo.anulado ? 'muted' : undefined}>
                <td>
                  {costo.tipo_nombre}
                  {costo.cartel_nombre && (
                    <small className="muted"> · Reserva · {costo.cartel_nombre}</small>
                  )}
                </td>
                <td>{aQuien(costo)}</td>
                <td>{importe(costo)}</td>
                <td>
                  {costo.anulado && `Anulado: ${costo.motivo_anulacion}`}
                  {!costo.anulado && costo.reserva !== null && (
                    <small className="muted">Se anula desde Costos</small>
                  )}
                  {!costo.anulado && costo.reserva === null && (
                    <button
                      type="button"
                      className="button-ghost"
                      onClick={() => setAnulando({ id: costo.id, motivo: '' })}
                    >
                      Anular
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p aria-label="Costo total del ítem">
        Costo total <strong>{formatearMonto(sumarMontos(vigentes))}</strong>{' '}
        <small className="muted">(sin anulados)</small>
      </p>
      {anulando && (
        <p>
          <label>
            Motivo de la anulación
            <input
              value={anulando.motivo}
              onChange={(event) => setAnulando({ ...anulando, motivo: event.target.value })}
            />
          </label>
          <FieldErrors messages={fallas.motivo ?? fallas.costo} />
          <button type="button" className="button-primary" onClick={() => void anular()}>
            Confirmar anulación
          </button>
          <button type="button" className="button-ghost" onClick={() => setAnulando(null)}>
            Cancelar anulación
          </button>
        </p>
      )}
      <div className="form-grid">
        <label>
          Tipo de costo
          <select value={nuevo.tipo} onChange={(event) => cambiar('tipo', event.target.value)}>
            {TIPOS_COSTO.map((tipo) => (
              <option key={tipo.value} value={tipo.value}>
                {tipo.label}
              </option>
            ))}
          </select>
          <FieldErrors messages={fallas.tipo} />
        </label>
        <label>
          Cómo se calcula
          <select value={nuevo.modo} onChange={(event) => cambiar('modo', event.target.value)}>
            <option value="monto">Monto fijo</option>
            <option value="porcentaje">Porcentaje del neto</option>
          </select>
        </label>
        <label>
          {nuevo.modo === 'monto' ? 'Monto fijo' : 'Porcentaje del neto'}
          <input
            inputMode="decimal"
            value={nuevo.valor}
            onChange={(event) => cambiar('valor', event.target.value)}
          />
          <FieldErrors messages={fallas.monto ?? fallas.porcentaje} />
        </label>
        <label>
          Proveedor
          <select
            value={nuevo.proveedor}
            onChange={(event) => cambiar('proveedor', event.target.value)}
          >
            <option value="">Sin proveedor</option>
            {proveedores.map((proveedor) => (
              <option key={proveedor.id} value={proveedor.id}>
                {proveedor.nombre}
              </option>
            ))}
          </select>
          <FieldErrors messages={fallas.proveedor} />
        </label>
        <label>
          A quién se le paga
          <input
            value={nuevo.destinatario}
            placeholder="Si no es un proveedor"
            onChange={(event) => cambiar('destinatario', event.target.value)}
          />
        </label>
      </div>
      <button type="button" className="button-ghost" onClick={() => void agregar()}>
        Agregar costo
      </button>
      {vinculables.length > 0 && (
        <p>
          <label>
            Costo de una reserva de la campaña
            <select value={vincular} onChange={(event) => setVincular(event.target.value)}>
              <option value="">Elegí un costo</option>
              {vinculables.map((costo) => (
                <option key={costo.id} value={costo.id}>
                  {`${costo.cartel_nombre ?? 'Reserva'} · ${costo.tipo_nombre} · ${formatearMonto(costo.monto)}`}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="button-ghost"
            disabled={!vincular}
            onClick={() =>
              void escribir(
                `${url}vincular/`,
                { costo: Number(vincular) },
                'No se pudo vincular el costo.',
              ).then((hecho) => hecho && setVincular(''))
            }
          >
            Vincular
          </button>
          <FieldErrors messages={fallas.costo ?? fallas.campania} />
        </p>
      )}
      <FieldErrors messages={fallas.general ?? fallas.estado} />
    </fieldset>
  )
}
