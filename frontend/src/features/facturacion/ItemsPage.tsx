import { useEffect, useState } from 'react'
import { ApiError, apiGet, apiWrite } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { usePuedeEditar } from '../../shared/sesion'
import type { Cliente } from '../clientes/types'
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
import { ESTADOS_ITEM, mesActual, urlPdfOrdenCompra } from './types'
import Cifras from '../../shared/Cifras'
import MenuFila from '../../shared/MenuFila'

const ITEMS = '/api/facturacion/items/'
const GRUPOS = '/api/facturacion/grupos/'
const SIN_CATALOGOS: CatalogosFacturacion = { sectores: [], tipos_venta: [] }

type Referencias = {
  clientes: Cliente[]
  catalogos: CatalogosFacturacion
}

function monto(valor: string | null): string {
  return valor === null ? '—' : formatearMonto(valor)
}

type AvisoOrdenCompra = { numero: string; items: AvisosItem['orden_compra'] }

/** Facturación: ítems del mes, totales, estados, OC y grupos (HU-060 a HU-065) y su Excel (HU-070). */
export default function ItemsPage() {
  const puedeEditar = usePuedeEditar()
  const [mes, setMes] = useState(mesActual())
  const [estado, setEstado] = useState('')
  const [items, setItems] = useState<ItemFacturacion[] | null>(null)
  const [totales, setTotales] = useState<TotalesMes | null>(null)
  const [referencias, setReferencias] = useState<Referencias>({
    clientes: [],
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
      apiGet<CatalogosFacturacion>('/api/facturacion/catalogos/'),
    ])
      .then(([clientes, catalogos]) => {
        if (active) setReferencias({ clientes, catalogos })
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los clientes o los catálogos.')
      })
    return () => {
      active = false
    }
  }, [])

  const filtro = new URLSearchParams({ mes, ...(estado && { estado }) }).toString()

  useEffect(() => {
    if (!mes) return
    let active = true
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
  }, [mes, filtro, revision])

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
          <p className="eyebrow">Comercial</p>
          <h2>Facturación</h2>
          <p className="muted">
            Cargá cada ítem cuando llega la orden de compra y descargá el Excel para Administración.
          </p>
        </div>
        <div className="row-actions">
          <a className="button-ghost" href={`${ITEMS}planilla/?${filtro}`} download>
            Descargar Excel
          </a>
          {puedeEditar && (
            <button className="button-primary" onClick={() => setEditando('nuevo')}>
              Nuevo ítem
            </button>
          )}
        </div>
      </div>
      {editando !== null && (
        <ItemForm
          key={editando === 'nuevo' ? 'nuevo' : editando.id}
          item={editando === 'nuevo' ? null : editando}
          mes={mes}
          {...referencias}
          onSave={guardar}
          onCancel={() => setEditando(null)}
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
            <th>Cliente (razón social)</th>
            <th>Importe neto total</th>
            <th>Costos incluidos</th>
            <th>Detalle costo</th>
            <th>Tipo de venta</th>
            <th>Gob/Priv</th>
            <th>Tipo</th>
            {puedeEditar && <th aria-label="Acciones" />}
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

type Pedido = 'facturar' | 'reabrir' | 'anular-facturado'

/** Las acciones que piden un dato antes de confirmarse: qué se pide y a dónde va. */
const PEDIDOS: Record<Pedido, { campo: string; confirmar: string }> = {
  facturar: { campo: 'Número de factura', confirmar: 'Confirmar' },
  reabrir: { campo: 'Motivo de la reapertura', confirmar: 'Confirmar reapertura' },
  'anular-facturado': { campo: 'Motivo de la anulación', confirmar: 'Confirmar anulación' },
}

/** Una fila con las siete columnas de la planilla (RN-024) y sus acciones en el menú ⋯. */
function FilaItem(props: FilaProps) {
  const { item, puedeEditar, seleccionado, onAlternar, onEditar, onCambio } = props
  const [pedido, setPedido] = useState<Pedido | null>(null)
  const [texto, setTexto] = useState('')
  const [errores, setErrores] = useState<Record<string, string[]>>({})

  async function escribir(url: string, method: 'POST' | 'PATCH', datos?: Record<string, string>) {
    try {
      await apiWrite(url, method, datos)
      setPedido(null)
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

  function pedir(accion: Pedido) {
    setTexto('')
    setErrores({})
    setPedido(accion)
  }

  function confirmar() {
    if (pedido === 'facturar') void cambiarEstado({ estado: 'facturado', numero_factura: texto })
    else if (pedido === 'reabrir')
      void escribir(`${ITEMS}${item.id}/reabrir/`, 'POST', { motivo: texto })
    else void escribir(`${ITEMS}${item.id}/anular-facturado/`, 'POST', { motivo: texto })
  }

  const borrador = item.estado === 'borrador'
  const enviado = item.estado === 'enviado'
  const mensajes = errores.estado ?? errores.numero_factura ?? errores.motivo ?? errores.grupo
  return (
    <tr className={item.estado === 'anulado' ? 'muted' : undefined}>
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
      <td className="primary-cell">{item.cliente_razon_social ?? 'Sin cliente'}</td>
      <td>{monto(item.neto)}</td>
      <td>{monto(item.costos_incluidos)}</td>
      <td>{item.detalle_costo || '—'}</td>
      <td>{item.tipo_venta_nombre ?? '—'}</td>
      <td>{item.sector_nombre ?? '—'}</td>
      <td>{item.tipo_soporte || '—'}</td>
      {puedeEditar && (
        <td className="row-actions">
          <MenuFila
            acciones={[
              borrador && { etiqueta: 'Editar', onClick: onEditar },
              enviado && { etiqueta: 'Marcar facturado', onClick: () => pedir('facturar') },
              enviado && { etiqueta: 'Reabrir', onClick: () => pedir('reabrir') },
              (borrador || enviado) && {
                etiqueta: 'Anular',
                onClick: () => void cambiarEstado({ estado: 'anulado' }),
              },
              item.estado === 'facturado' && {
                etiqueta: 'Anular',
                onClick: () => pedir('anular-facturado'),
              },
              borrador &&
                item.grupo_codigo !== null && {
                  etiqueta: 'Quitar del grupo',
                  onClick: () => void escribir(`${ITEMS}${item.id}/quitar-del-grupo/`, 'POST'),
                },
              item.orden_compra_pdf !== null && {
                etiqueta: 'Ver PDF de la OC',
                onClick: () => window.open(urlPdfOrdenCompra(item.id), '_blank', 'noreferrer'),
              },
            ]}
          />
          {pedido !== null && (
            <>
              <input
                aria-label={PEDIDOS[pedido].campo}
                value={texto}
                onChange={(event) => setTexto(event.target.value)}
              />
              <button className="button-primary" onClick={confirmar}>
                {PEDIDOS[pedido].confirmar}
              </button>
            </>
          )}
          <FieldErrors messages={mensajes} />
        </td>
      )}
    </tr>
  )
}
