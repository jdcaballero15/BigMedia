import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import { formatearFecha } from '../../shared/fechas'
import type { Proveedor } from '../inventario/types'
import type { CostoListado, TipoCosto } from './types'
import { TIPOS_COSTO } from './types'
import { sumarMontos } from './montos'

export default function CostosPage() {
  const [costos, setCostos] = useState<CostoListado[]>([])
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [tipo, setTipo] = useState<TipoCosto | ''>('')
  const [proveedor, setProveedor] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    void apiGet<Proveedor[]>('/api/inventario/proveedores/?incluir_inactivos=1')
      .then((data) => {
        if (active) setProveedores(data)
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los proveedores.')
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    const params = new URLSearchParams()
    if (tipo) params.set('tipo', tipo)
    if (proveedor) params.set('proveedor', proveedor)
    const query = params.toString()
    void apiGet<CostoListado[]>(`/api/costos/costos/${query ? `?${query}` : ''}`)
      .then((data) => {
        if (active) {
          setCostos(data)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los costos.')
      })
    return () => {
      active = false
    }
  }, [tipo, proveedor])

  const total = sumarMontos(costos.filter((costo) => !costo.anulado).map((costo) => costo.monto))

  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Operación</p>
          <h2>Costos</h2>
          <p className="muted">
            Todos los costos cargados. Se agregan y anulan desde cada reserva.
          </p>
        </div>
      </div>
      <div className="card filters">
        <label>
          Tipo
          <select value={tipo} onChange={(event) => setTipo(event.target.value as TipoCosto | '')}>
            <option value="">Todos</option>
            {TIPOS_COSTO.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Proveedor
          <select value={proveedor} onChange={(event) => setProveedor(event.target.value)}>
            <option value="">Todos</option>
            {proveedores.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
              </option>
            ))}
          </select>
        </label>
        <p className="costos-total">
          Total vigente <strong>{total}</strong>
        </p>
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Campaña</th>
              <th>Cartel</th>
              <th>Tipo</th>
              <th>Proveedor</th>
              <th>Monto</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {costos.map((costo) => (
              <tr key={costo.id}>
                <td>{formatearFecha(costo.fecha)}</td>
                <td className="primary-cell">{costo.campania_nombre}</td>
                <td>{costo.cartel_nombre}</td>
                <td>{costo.tipo_nombre}</td>
                <td>{costo.proveedor_nombre ?? '—'}</td>
                <td>{costo.monto}</td>
                <td>
                  {costo.anulado ? 'Anulado' : 'Vigente'}
                  {costo.anulado && costo.motivo_anulacion && (
                    <span className="cell-detail">{costo.motivo_anulacion}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {costos.length === 0 && <p className="empty">No hay costos cargados.</p>}
      </div>
    </section>
  )
}
