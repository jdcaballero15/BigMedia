import { useEffect, useState } from 'react'
import { ApiError, apiGet, apiWrite } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { usePuedeEditar } from '../../shared/sesion'
import type { Campania } from '../campanias/types'
import type { Cliente, Marca } from '../clientes/types'
import EnviosDelMes from './EnviosDelMes'
import ItemForm from './ItemForm'
import type { ItemInput } from './ItemForm'
import { formatearMonto } from './montos'
import type {
  AvisosItem,
  CatalogosFacturacion,
  ItemFacturacion,
  ItemGuardado,
  TotalesMes,
} from './types'
import { ESTADOS_ITEM, etiquetaEstadoItem, mesActual, urlPdfOrdenCompra } from './types'
import Cifras from '../../shared/Cifras'

const ITEMS = '/api/facturacion/items/'
const GRUPOS = '/api/facturacion/grupos/'
const SIN_CATALOGOS: CatalogosFacturacion = { sectores: [], tipos_venta: [] }

type Referencias = {
  clientes: Cliente[]
  marcas: Marca[]
  campanias: Campania[]
  catalogos: CatalogosFacturacion
}

function monto(valor: string | null): string {
  return valor === null ? '—' : formatearMonto(valor)
}

type AvisoOrdenCompra = { numero: string; items: AvisosItem['orden_compra'] }

/** Ítems a facturar del mes con totales, estados, OC y grupos (HU-060 a HU-065). */
export default function ItemsPage() {
  const puedeEditar = usePuedeEditar()
  const [mes, setMes] = useState(mesActual())
  const [estado, setEstado] = useState('')
  const [items, setItems] = useState<ItemFacturacion[] | null>(null)
  const [totales, setTotales] = useState<TotalesMes | null>(null)
  const [referencias, setReferencias] = useState<Referencias>({
    clientes: [],
    marcas: [],
    campanias: [],
    catalogos: SIN_CATALOGOS,
  })
  const [error, setError] = useState('')
  const [editando, setEditando] = useState<ItemFacturacion | 'nuevo' | null>(null)
  const [revision, setRevision] = useState(0)
  const [aviso, setAviso] = useState<AvisoOrdenCompra | null>(null)
  const [seleccion, setSeleccion] = useState<number[]>([])
  const [errorGrupo, setErrorGrupo] = useState('')

  useEffect(() => {
    let active = true
    void Promise.all([
      apiGet<Cliente[]>('/api/clientes/clientes/?incluir_inactivos=1'),
      apiGet<Marca[]>('/api/clientes/marcas/?incluir_inactivos=1'),
      apiGet<Campania[]>('/api/campanias/campanias/'),
      apiGet<CatalogosFacturacion>('/api/facturacion/catalogos/'),
    ])
      .then(([clientes, marcas, campanias, catalogos]) => {
        if (active) setReferencias({ clientes, marcas, campanias, catalogos })
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar clientes, marcas o campañas.')
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!mes) return
    let active = true
    const filtro = new URLSearchParams({ mes, ...(estado && { estado }) }).toString()
    void Promise.all([
      apiGet<ItemFacturacion[]>(`${ITEMS}?${filtro}`),
      apiGet<TotalesMes>(`${ITEMS}totales/?mes=${mes}`),
    ])
      .then(([filas, suma]) => {
        if (!active) return
        setItems(filas)
        setTotales(suma)
        setError('')
        setSeleccion([])
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los ítems del mes.')
      })
    return () => {
      active = false
    }
  }, [mes, estado, revision])

  const recargar = () => setRevision((actual) => actual + 1)

  async function guardar(input: ItemInput) {
    if (editando === null) return
    const guardado =
      editando === 'nuevo'
        ? await apiWrite<ItemGuardado>(ITEMS, 'POST', input)
        : await apiWrite<ItemGuardado>(`${ITEMS}${editando.id}/`, 'PATCH', input)
    const coincidentes = guardado.avisos.orden_compra
    setAviso(
      coincidentes.length ? { numero: guardado.orden_compra_numero, items: coincidentes } : null,
    )
    setEditando(null)
    recargar()
  }

  async function agrupar() {
    setErrorGrupo('')
    try {
      await apiWrite(GRUPOS, 'POST', { items: seleccion })
      recargar()
    } catch (cause) {
      const campos = cause instanceof ApiError ? cause.fields : {}
      setErrorGrupo(campos.items?.join(' ') ?? 'No se pudieron agrupar los ítems.')
    }
  }

  const alternar = (id: number) =>
    setSeleccion((actual) =>
      actual.includes(id) ? actual.filter((otro) => otro !== id) : [...actual, id],
    )

  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Facturación</p>
          <h2>Ítems a facturar</h2>
          <p className="muted">Cargá cada ítem cuando llega la orden de compra.</p>
        </div>
        {puedeEditar && (
          <button className="button-primary" onClick={() => setEditando('nuevo')}>
            Nuevo ítem
          </button>
        )}
      </div>
      {editando !== null && (
        <ItemForm
          key={editando === 'nuevo' ? 'nuevo' : editando.id}
          item={editando === 'nuevo' ? null : editando}
          {...referencias}
          onSave={guardar}
          onCancel={() => setEditando(null)}
          onPdfCambiado={recargar}
          onCostosCambiados={recargar}
        />
      )}
      <div className="filters card" role="search" aria-label="Filtros de ítems">
        <label>
          Mes
          <input type="month" value={mes} onChange={(event) => setMes(event.target.value)} />
        </label>
        <label>
          Estado
          <select value={estado} onChange={(event) => setEstado(event.target.value)}>
            <option value="">Todos</option>
            {ESTADOS_ITEM.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      {totales && (
        <Cifras
          titulo="Totales del mes"
          cifras={[
            { etiqueta: 'Ítems', valor: totales.cantidad, detalle: 'sin anulados' },
            { etiqueta: 'Neto', valor: formatearMonto(totales.neto) },
            { etiqueta: 'IVA', valor: formatearMonto(totales.iva) },
            { etiqueta: 'Total', valor: formatearMonto(totales.total), tono: 'principal' },
            { etiqueta: 'Costos', valor: formatearMonto(totales.costos) },
            { etiqueta: 'Neto final', valor: formatearMonto(totales.neto_final) },
          ]}
        />
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {aviso && (
        <p className="card" role="status" aria-label="Aviso de orden de compra">
          La orden de compra {aviso.numero} ya está cargada en:{' '}
          {aviso.items.map((otro) => `#${otro.id} (${otro.descripcion})`).join(', ')}. El ítem se
          guardó igual.{' '}
          <button className="button-ghost" onClick={() => setAviso(null)}>
            Entendido
          </button>
        </p>
      )}
      {puedeEditar && (items ?? []).length > 0 && (
        <div className="row-actions">
          <button
            className="button-ghost"
            disabled={seleccion.length < 2}
            onClick={() => void agrupar()}
          >
            Agrupar en una factura ({seleccion.length})
          </button>
          {errorGrupo && (
            <span className="error" role="alert">
              {errorGrupo}
            </span>
          )}
        </div>
      )}
      <EnviosDelMes
        mes={mes}
        puedeEditar={puedeEditar}
        hayBorradores={estado !== '' || (items ?? []).some((item) => item.estado === 'borrador')}
        onEnviado={recargar}
      />
      {items === null ? (
        !error && <p className="empty">Cargando ítems…</p>
      ) : items.length === 0 ? (
        <p className="empty">No hay ítems en este mes.</p>
      ) : (
        <TablaItems
          items={items}
          puedeEditar={puedeEditar}
          seleccion={seleccion}
          onAlternar={alternar}
          onEditar={setEditando}
          onCambio={recargar}
        />
      )}
    </section>
  )
}

type TablaProps = {
  items: ItemFacturacion[]
  puedeEditar: boolean
  seleccion: number[]
  onAlternar: (id: number) => void
  onEditar: (item: ItemFacturacion) => void
  onCambio: () => void
}

function TablaItems(props: TablaProps) {
  const { items, puedeEditar, seleccion, onAlternar, onEditar, onCambio } = props
  return (
    <div className="card table-wrap">
      <table aria-label="Ítems a facturar">
        <thead>
          <tr>
            {puedeEditar && <th aria-label="Selección" />}
            <th>Cliente</th>
            <th>Descripción</th>
            <th>Neto</th>
            <th>IVA</th>
            <th>Total</th>
            <th>Costos</th>
            <th>Neto final</th>
            <th>Grupo</th>
            <th>Estado</th>
            {puedeEditar && <th>Acciones</th>}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <FilaItem
              key={item.id}
              item={item}
              puedeEditar={puedeEditar}
              seleccionado={seleccion.includes(item.id)}
              onAlternar={() => onAlternar(item.id)}
              onEditar={() => onEditar(item)}
              onCambio={onCambio}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}

type FilaProps = {
  item: ItemFacturacion
  puedeEditar: boolean
  seleccionado: boolean
  onAlternar: () => void
  onEditar: () => void
  onCambio: () => void
}

function FilaItem(props: FilaProps) {
  const { item, puedeEditar, seleccionado, onAlternar, onEditar, onCambio } = props
  const [facturando, setFacturando] = useState(false)
  const [numero, setNumero] = useState('')
  const [reabriendo, setReabriendo] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [anulando, setAnulando] = useState(false)
  const [motivoAnulacion, setMotivoAnulacion] = useState('')
  const [errores, setErrores] = useState<Record<string, string[]>>({})

  async function escribir(url: string, method: 'POST' | 'PATCH', datos?: Record<string, string>) {
    try {
      await apiWrite(url, method, datos)
      setFacturando(false)
      setReabriendo(false)
      setAnulando(false)
      onCambio()
    } catch (cause) {
      const campos = cause instanceof ApiError ? cause.fields : {}
      setErrores(
        Object.keys(campos).length ? campos : { estado: ['No se pudo guardar el cambio.'] },
      )
    }
  }
  const cambiarEstado = (datos: Record<string, string>) =>
    escribir(`${ITEMS}${item.id}/`, 'PATCH', datos)

  const anulado = item.estado === 'anulado'
  const borrador = item.estado === 'borrador'
  return (
    <tr className={anulado ? 'muted' : undefined}>
      {puedeEditar && (
        <td>
          {borrador && (
            <input
              type="checkbox"
              aria-label={`Seleccionar ítem ${item.id}`}
              checked={seleccionado}
              onChange={onAlternar}
            />
          )}
        </td>
      )}
      <td className="primary-cell">
        {item.cliente_nombre ?? 'Sin cliente'}
        {item.cuit_facturacion && <small className="muted"> · CUIT {item.cuit_facturacion}</small>}
      </td>
      <td>
        {item.descripcion || '—'}
        {item.orden_compra_numero && (
          <small className="muted"> · OC {item.orden_compra_numero}</small>
        )}
        {item.orden_compra_pdf && (
          <>
            {' '}
            <a href={urlPdfOrdenCompra(item.id)} target="_blank" rel="noreferrer">
              PDF
            </a>
          </>
        )}
      </td>
      <td>{monto(item.neto)}</td>
      <td>{monto(item.iva)}</td>
      <td>{monto(item.total)}</td>
      <td>{monto(item.costo_total)}</td>
      <td>{monto(item.neto_final)}</td>
      <td>
        {item.grupo_codigo ?? '—'}
        {item.grupo_codigo && puedeEditar && borrador && (
          <button
            className="button-ghost"
            onClick={() => void escribir(`${ITEMS}${item.id}/quitar-del-grupo/`, 'POST')}
          >
            Quitar del grupo
          </button>
        )}
        <FieldErrors messages={errores.grupo} />
      </td>
      <td>
        {etiquetaEstadoItem(item.estado)}
        {item.numero_factura && <small className="muted"> · {item.numero_factura}</small>}
        {item.reenviado && <small className="muted"> · Reenviado</small>}
        {borrador && item.reabierto_en && (
          <small className="muted"> · Reabierto: {item.motivo_reapertura}</small>
        )}
        {anulado && item.anulado_en && (
          <small className="muted"> · Anulado: {item.motivo_anulacion}</small>
        )}
        <FieldErrors messages={errores.estado ?? errores.numero_factura ?? errores.motivo} />
      </td>
      {puedeEditar && (
        <td className="row-actions">
          {borrador && (
            <button className="button-ghost" onClick={onEditar}>
              Editar
            </button>
          )}
          {item.estado === 'enviado' &&
            (facturando ? (
              <>
                <input
                  aria-label="Número de factura"
                  value={numero}
                  onChange={(event) => setNumero(event.target.value)}
                />
                <button
                  className="button-primary"
                  onClick={() =>
                    void cambiarEstado({ estado: 'facturado', numero_factura: numero })
                  }
                >
                  Confirmar
                </button>
              </>
            ) : (
              <button className="button-ghost" onClick={() => setFacturando(true)}>
                Marcar facturado
              </button>
            ))}
          {item.estado === 'enviado' &&
            (reabriendo ? (
              <>
                <input
                  aria-label="Motivo de la reapertura"
                  value={motivo}
                  onChange={(event) => setMotivo(event.target.value)}
                />
                <button
                  className="button-primary"
                  onClick={() => void escribir(`${ITEMS}${item.id}/reabrir/`, 'POST', { motivo })}
                >
                  Confirmar reapertura
                </button>
              </>
            ) : (
              <button className="button-ghost" onClick={() => setReabriendo(true)}>
                Reabrir
              </button>
            ))}
          {(item.estado === 'borrador' || item.estado === 'enviado') && (
            <button
              className="button-ghost"
              onClick={() => void cambiarEstado({ estado: 'anulado' })}
            >
              Anular
            </button>
          )}
          {item.estado === 'facturado' &&
            (anulando ? (
              <>
                <input
                  aria-label="Motivo de la anulación"
                  value={motivoAnulacion}
                  onChange={(event) => setMotivoAnulacion(event.target.value)}
                />
                <button
                  className="button-primary"
                  onClick={() =>
                    void escribir(`${ITEMS}${item.id}/anular-facturado/`, 'POST', {
                      motivo: motivoAnulacion,
                    })
                  }
                >
                  Confirmar anulación
                </button>
              </>
            ) : (
              <button className="button-ghost" onClick={() => setAnulando(true)}>
                Anular
              </button>
            ))}
        </td>
      )}
    </tr>
  )
}
