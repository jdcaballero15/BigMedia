import { useCallback, useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import type { Cliente, Marca, Rubro } from '../clientes/types'
import type { MarcaInput } from '../clientes/MarcaForm'
import CampaniaForm from './CampaniaForm'
import type { CampaniaInput } from './CampaniaForm'
import CampaniaDetalle from './CampaniaDetalle'
import MoverPendientes from '../reservas/MoverPendientes'
import type { Campania } from './types'
import { ESTADOS_CAMPANIA, etiquetaEstado } from './types'
import { usePuedeEditar } from '../../shared/sesion'
import MenuFila from '../../shared/MenuFila'

type CambioDeFechas = {
  campaniaId: number
  inicioAnterior: string
  finAnterior: string
  inicioNuevo: string
  finNuevo: string
}

/** Cambio de fechas que puede arrastrar Pendientes (HU-058): ambas fechas, antes y después. */
function detectarCambioDeFechas(anterior: Campania, guardada: Campania): CambioDeFechas | null {
  const { fecha_inicio: inicioAnterior, fecha_fin: finAnterior } = anterior
  const { fecha_inicio: inicioNuevo, fecha_fin: finNuevo } = guardada
  if (!inicioAnterior || !finAnterior || !inicioNuevo || !finNuevo) return null
  if (inicioAnterior === inicioNuevo && finAnterior === finNuevo) return null
  return { campaniaId: guardada.id, inicioAnterior, finAnterior, inicioNuevo, finNuevo }
}

export default function CampaniasPage() {
  const puedeEditar = usePuedeEditar()
  const [campanias, setCampanias] = useState<Campania[]>([])
  const [marcas, setMarcas] = useState<Marca[]>([])
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [rubros, setRubros] = useState<Rubro[]>([])
  const [estado, setEstado] = useState('')
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [errorCatalogos, setErrorCatalogos] = useState('')
  const [editing, setEditing] = useState<Campania | 'new' | null>(null)
  const [viendo, setViendo] = useState<Campania | null>(null)
  const [revision, setRevision] = useState(0)
  const [cambioDeFechas, setCambioDeFechas] = useState<CambioDeFechas | null>(null)
  const terminarCambioDeFechas = useCallback(() => setCambioDeFechas(null), [])

  useEffect(() => {
    let active = true
    void Promise.all([
      apiGet<Marca[]>('/api/clientes/marcas/?incluir_inactivos=1'),
      apiGet<Cliente[]>('/api/clientes/clientes/?incluir_inactivos=1'),
      apiGet<Rubro[]>('/api/clientes/rubros/?incluir_inactivos=1'),
    ])
      .then(([marcasRows, clientesRows, rubrosRows]) => {
        if (!active) return
        setMarcas(marcasRows)
        setClientes(clientesRows)
        setRubros(rubrosRows)
      })
      .catch(() => {
        if (active) setErrorCatalogos('No se pudieron cargar marcas o clientes.')
      })
    return () => {
      active = false
    }
  }, [revision])

  useEffect(() => {
    let active = true
    const params = new URLSearchParams()
    if (estado) params.set('estado', estado)
    if (q.trim()) params.set('q', q.trim())
    const suffix = params.toString() ? `?${params}` : ''
    void apiGet<Campania[]>(`/api/campanias/campanias/${suffix}`)
      .then((rows) => {
        if (active) {
          setCampanias(rows)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar las campañas.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [estado, q, revision])

  async function saveCampania(input: CampaniaInput) {
    if (editing === null) return
    const path =
      editing === 'new' ? '/api/campanias/campanias/' : `/api/campanias/campanias/${editing.id}/`
    const guardada = await apiWrite<Campania>(path, editing === 'new' ? 'POST' : 'PATCH', input)
    if (editing !== 'new') setCambioDeFechas(detectarCambioDeFechas(editing, guardada))
    setEditing(null)
    setRevision((current) => current + 1)
  }

  async function crearMarca(input: MarcaInput): Promise<Marca> {
    const creada = await apiWrite<Marca>('/api/clientes/marcas/', 'POST', input)
    setMarcas((actuales) => [...actuales, creada])
    return creada
  }

  function cambiarFiltro(apply: () => void) {
    setLoading(true)
    apply()
  }

  if (viendo) {
    return (
      <CampaniaDetalle
        campania={viendo}
        onEditar={() => {
          setEditing(viendo)
          setViendo(null)
        }}
        onVolver={() => setViendo(null)}
      />
    )
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Comercial</p>
          <h2>Campañas</h2>
          <p className="muted">Agrupá las ventas de un cliente y marca; cargá reservas después.</p>
        </div>
        {puedeEditar && (
          <button className="button-primary" onClick={() => setEditing('new')}>
            Nueva campaña
          </button>
        )}
      </div>
      {editing !== null && (
        <CampaniaForm
          key={editing === 'new' ? 'new' : editing.id}
          campania={editing === 'new' ? null : editing}
          marcas={marcas}
          clientes={clientes}
          rubros={rubros}
          onSave={saveCampania}
          onCrearMarca={crearMarca}
          onCancel={() => setEditing(null)}
        />
      )}
      {cambioDeFechas && (
        <MoverPendientes
          key={`${cambioDeFechas.campaniaId}-${cambioDeFechas.inicioNuevo}-${cambioDeFechas.finNuevo}`}
          {...cambioDeFechas}
          onListo={terminarCambioDeFechas}
        />
      )}
      <div className="filters card" role="search" aria-label="Filtros de campañas">
        <label>
          Estado
          <select
            value={estado}
            onChange={(event) => cambiarFiltro(() => setEstado(event.target.value))}
          >
            <option value="">Todos</option>
            {ESTADOS_CAMPANIA.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Buscar
          <input
            value={q}
            onChange={(event) => cambiarFiltro(() => setQ(event.target.value))}
            placeholder="Nombre de la campaña"
          />
        </label>
      </div>
      {errorCatalogos && (
        <p className="error" role="alert">
          {errorCatalogos}
        </p>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="card table-wrap section-gap">
        {loading ? (
          <p className="empty">Cargando campañas…</p>
        ) : campanias.length === 0 ? (
          <p className="empty">No hay campañas para estos filtros.</p>
        ) : (
          <table aria-label="Campañas">
            <thead>
              <tr>
                <th>Campaña</th>
                <th>Marca</th>
                <th>Cliente que factura</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {campanias.map((item) => (
                <tr key={item.id}>
                  <td className="primary-cell">{item.nombre || `Campaña #${item.id}`}</td>
                  <td>{item.marca_nombre ?? 'Sin marca'}</td>
                  <td>{item.cliente_factura_nombre || 'Sin definir'}</td>
                  <td>{etiquetaEstado(item.estado)}</td>
                  <td className="row-actions">
                    <button className="button-ghost" onClick={() => setViendo(item)}>
                      Ver
                    </button>
                    <MenuFila
                      acciones={[
                        { etiqueta: 'Editar', onClick: () => setEditing(item), edicion: true },
                      ]}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}
