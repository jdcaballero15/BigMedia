import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import type { RegistroAuditoria, UsuarioAuditoria } from './types'

function toIsoDate(d: Date): string {
  // `en-CA` formatea como AAAA-MM-DD en hora local (evita el corrimiento de un día de UTC en UTC-3).
  return d.toLocaleDateString('en-CA')
}

const _ahora = new Date()
const _hace30 = new Date(_ahora)
_hace30.setDate(_hace30.getDate() - 30)

const FECHA_DESDE_DEFAULT = toIsoDate(_hace30)
const FECHA_HASTA_DEFAULT = toIsoDate(_ahora)

const ETIQUETAS_ENTIDAD: Record<string, string> = {
  reserva: 'Reserva',
  campania: 'Campaña',
  cartel: 'Cartel',
  usuario: 'Usuario',
  parametros: 'Parámetros',
}

function etiquetaEntidad(entidad: string): string {
  return ETIQUETAS_ENTIDAD[entidad] ?? entidad.charAt(0).toUpperCase() + entidad.slice(1)
}

export default function AuditoriaPage() {
  const [usuario, setUsuario] = useState('')
  const [desde, setDesde] = useState(FECHA_DESDE_DEFAULT)
  const [hasta, setHasta] = useState(FECHA_HASTA_DEFAULT)
  const [entidad, setEntidad] = useState('')
  const [usuarios, setUsuarios] = useState<UsuarioAuditoria[]>([])
  const [registros, setRegistros] = useState<RegistroAuditoria[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    void apiGet<UsuarioAuditoria[]>('/api/auditoria/usuarios/')
      .then((filas) => {
        if (active) setUsuarios(filas)
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los usuarios.')
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    const params = new URLSearchParams()
    if (usuario) params.set('usuario', usuario)
    if (desde) params.set('desde', desde)
    if (hasta) params.set('hasta', hasta)
    if (entidad) params.set('entidad', entidad)
    const query = params.toString() ? `?${params.toString()}` : ''
    void apiGet<RegistroAuditoria[]>(`/api/auditoria/registros/${query}`)
      .then((filas) => {
        if (active) {
          setRegistros(filas)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudo cargar el registro de auditoría.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [usuario, desde, hasta, entidad])

  function cambiar(apply: () => void) {
    setLoading(true)
    apply()
  }

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Administración</p>
          <h2>Auditoría</h2>
        </div>
      </div>
      <div className="filters card">
        <label>
          Usuario
          <select
            value={usuario}
            onChange={(event) => cambiar(() => setUsuario(event.target.value))}
          >
            <option value="">Todos</option>
            {usuarios.map((u) => (
              <option key={u.id} value={u.id}>
                {u.nombre}
              </option>
            ))}
          </select>
        </label>
        <label>
          Desde
          <input
            type="date"
            value={desde}
            onChange={(event) => cambiar(() => setDesde(event.target.value))}
          />
        </label>
        <label>
          Hasta
          <input
            type="date"
            value={hasta}
            onChange={(event) => cambiar(() => setHasta(event.target.value))}
          />
        </label>
        <label>
          Entidad
          <select
            value={entidad}
            onChange={(event) => cambiar(() => setEntidad(event.target.value))}
          >
            <option value="">Todas</option>
            <option value="reserva">Reserva</option>
            <option value="campania">Campaña</option>
            <option value="cartel">Cartel</option>
            <option value="usuario">Usuario</option>
            <option value="parametros">Parámetros</option>
          </select>
        </label>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="card table-wrap">
        {loading ? (
          <p className="empty">Cargando auditoría…</p>
        ) : registros.length === 0 ? (
          <p className="empty">Sin cambios registrados para estos filtros.</p>
        ) : (
          <table aria-label="Registros de auditoría">
            <thead>
              <tr>
                <th>Momento</th>
                <th>Usuario</th>
                <th>Entidad</th>
                <th>Campo</th>
                <th>Valor anterior</th>
                <th>Valor nuevo</th>
              </tr>
            </thead>
            <tbody>
              {registros.map((reg) => (
                <tr key={reg.id}>
                  <td>{new Date(reg.momento).toLocaleString('es-AR')}</td>
                  <td>{reg.usuario_nombre}</td>
                  <td>
                    {etiquetaEntidad(reg.entidad)} #{reg.entidad_id}
                  </td>
                  <td>{reg.campo}</td>
                  <td>{reg.valor_anterior ?? '—'}</td>
                  <td>{reg.valor_nuevo ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
