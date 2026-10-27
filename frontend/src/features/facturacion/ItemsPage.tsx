import { useEffect, useState } from 'react'
import { ApiError, apiGet, apiWrite } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { usePuedeEditar } from '../../shared/sesion'
import type { Campania } from '../campanias/types'
import type { Cliente, Marca } from '../clientes/types'
import ItemForm from './ItemForm'
import type { ItemInput } from './ItemForm'
import { formatearMonto } from './montos'
import type { CatalogosFacturacion, ItemFacturacion, TotalesMes } from './types'
import { ESTADOS_ITEM, etiquetaEstadoItem, mesActual } from './types'

const ITEMS = '/api/facturacion/items/'
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

/** Ítems a facturar del mes con sus totales y estados (HU-060, HU-061, HU-065). */
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
    if (editando === 'nuevo') await apiWrite(ITEMS, 'POST', input)
    else await apiWrite(`${ITEMS}${editando.id}/`, 'PATCH', input)
    setEditando(null)
    recargar()
  }

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
        <p className="costos-total" aria-label="Totales del mes">
          {totales.cantidad} ítems · Neto <strong>{formatearMonto(totales.neto)}</strong> · IVA{' '}
          {formatearMonto(totales.iva)} · Total <strong>{formatearMonto(totales.total)}</strong>{' '}
          <small className="muted">(sin anulados)</small>
        </p>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {items === null ? (
        !error && <p className="empty">Cargando ítems…</p>
      ) : items.length === 0 ? (
        <p className="empty">No hay ítems en este mes.</p>
      ) : (
        <TablaItems
          items={items}
          puedeEditar={puedeEditar}
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
  onEditar: (item: ItemFacturacion) => void
  onCambio: () => void
}

function TablaItems({ items, puedeEditar, onEditar, onCambio }: TablaProps) {
  return (
    <div className="card table-wrap">
      <table aria-label="Ítems a facturar">
        <thead>
          <tr>
            <th>Cliente</th>
            <th>Descripción</th>
            <th>Neto</th>
            <th>IVA</th>
            <th>Total</th>
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
  onEditar: () => void
  onCambio: () => void
}

function FilaItem({ item, puedeEditar, onEditar, onCambio }: FilaProps) {
  const [facturando, setFacturando] = useState(false)
  const [numero, setNumero] = useState('')
  const [errores, setErrores] = useState<Record<string, string[]>>({})

  async function cambiarEstado(datos: Record<string, string>) {
    try {
      await apiWrite(`${ITEMS}${item.id}/`, 'PATCH', datos)
      setFacturando(false)
      onCambio()
    } catch (cause) {
      const campos = cause instanceof ApiError ? cause.fields : {}
      setErrores(
        Object.keys(campos).length ? campos : { estado: ['No se pudo cambiar el estado.'] },
      )
    }
  }

  const anulado = item.estado === 'anulado'
  return (
    <tr className={anulado ? 'muted' : undefined}>
      <td className="primary-cell">
        {item.cliente_nombre ?? 'Sin cliente'}
        {item.cuit_facturacion && <small className="muted"> · CUIT {item.cuit_facturacion}</small>}
      </td>
      <td>{item.descripcion || '—'}</td>
      <td>{monto(item.neto)}</td>
      <td>{monto(item.iva)}</td>
      <td>{monto(item.total)}</td>
      <td>
        {etiquetaEstadoItem(item.estado)}
        {item.numero_factura && <small className="muted"> · {item.numero_factura}</small>}
        <FieldErrors messages={errores.estado ?? errores.numero_factura} />
      </td>
      {puedeEditar && (
        <td className="row-actions">
          {item.estado === 'borrador' && (
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
          {(item.estado === 'borrador' || item.estado === 'enviado') && (
            <button
              className="button-ghost"
              onClick={() => void cambiarEstado({ estado: 'anulado' })}
            >
              Anular
            </button>
          )}
        </td>
      )}
    </tr>
  )
}
