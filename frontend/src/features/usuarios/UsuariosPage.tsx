import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import UsuarioForm from './UsuarioForm'
import type { UsuarioInput } from './UsuarioForm'
import { ETIQUETAS_ROL } from './types'
import type { Usuario } from './types'

const URL = '/api/usuarios/usuarios/'

type Link = { username: string; link: string }

function nombreCompleto(usuario: Usuario): string {
  return `${usuario.first_name} ${usuario.last_name}`.trim() || '—'
}

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState<Usuario | 'new' | null>(null)
  const [link, setLink] = useState<Link | null>(null)
  const [copiado, setCopiado] = useState(false)
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let active = true
    void apiGet<Usuario[]>(URL)
      .then((rows) => {
        if (active) {
          setUsuarios(rows)
          setError('')
        }
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los usuarios.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [revision])

  async function guardar(input: UsuarioInput) {
    if (editing === null) return
    const nuevo = editing === 'new'
    const guardado = await apiWrite<Usuario>(
      nuevo ? URL : `${URL}${editing.id}/`,
      nuevo ? 'POST' : 'PATCH',
      input,
    )
    setEditing(null)
    setRevision((current) => current + 1)
    // Un usuario nuevo no tiene contraseña: se le genera el link para que la defina.
    if (nuevo) await generarLink(guardado)
  }

  async function cambiarActivo(usuario: Usuario, activo: boolean) {
    const pregunta = activo
      ? `¿Reactivar a ${usuario.username}?`
      : `¿Inactivar a ${usuario.username}? No podrá ingresar, pero su historial se conserva.`
    if (!window.confirm(pregunta)) return
    try {
      await apiWrite(`${URL}${usuario.id}/`, 'PATCH', { activo })
      setRevision((current) => current + 1)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudo cambiar el usuario.')
    }
  }

  async function generarLink(usuario: Usuario) {
    if (
      usuario.tiene_clave &&
      !window.confirm(
        `¿Restablecer la contraseña de ${usuario.username}? La actual deja de servir y se cierra su sesión.`,
      )
    )
      return
    try {
      const respuesta = await apiWrite<{ link: string }>(`${URL}${usuario.id}/link-clave/`, 'POST')
      setCopiado(false)
      setLink({ username: usuario.username, link: respuesta.link })
      setRevision((current) => current + 1)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudo generar el link.')
    }
  }

  async function copiar(texto: string) {
    try {
      await navigator.clipboard.writeText(texto)
      setCopiado(true)
    } catch {
      setError('No se pudo copiar: seleccioná el link y copialo a mano.')
    }
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Administración</p>
          <h2>Usuarios</h2>
          <p className="muted">Quién usa el sistema, con qué rol, y su acceso.</p>
        </div>
        <button className="button-primary" onClick={() => setEditing('new')}>
          Nuevo usuario
        </button>
      </div>
      {editing !== null && (
        <UsuarioForm
          key={editing === 'new' ? 'new' : editing.id}
          usuario={editing === 'new' ? null : editing}
          onSave={guardar}
          onCancel={() => setEditing(null)}
        />
      )}
      {link && (
        <div className="card section-gap" role="status" aria-label="Link de contraseña">
          <p>
            Mandale este link a <strong>{link.username}</strong> para que defina su contraseña.
            Sirve una sola vez y vence.
          </p>
          <input readOnly value={link.link} aria-label="Link" onFocus={(e) => e.target.select()} />
          <div className="row-actions">
            <button className="button-ghost" onClick={() => void copiar(link.link)}>
              {copiado ? 'Copiado' : 'Copiar'}
            </button>
            <button className="button-ghost" onClick={() => setLink(null)}>
              Cerrar
            </button>
          </div>
        </div>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="card table-wrap section-gap">
        {loading ? (
          <p className="empty">Cargando usuarios…</p>
        ) : usuarios.length === 0 ? (
          <p className="empty">No hay usuarios.</p>
        ) : (
          <table aria-label="Usuarios">
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Gerencia</th>
                <th>Contraseña</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((item) => (
                <tr key={item.id}>
                  <td className="primary-cell">{item.username}</td>
                  <td>{nombreCompleto(item)}</td>
                  <td>{item.email || '—'}</td>
                  <td>{ETIQUETAS_ROL[item.rol]}</td>
                  <td>{item.es_gerencia ? 'Sí' : 'No'}</td>
                  <td>{item.tiene_clave ? 'Definida' : 'Pendiente'}</td>
                  <td>{item.activo ? 'Activo' : 'Inactivo'}</td>
                  <td className="row-actions">
                    <button className="button-ghost" onClick={() => setEditing(item)}>
                      Editar
                    </button>
                    <button className="button-ghost" onClick={() => void generarLink(item)}>
                      {item.tiene_clave ? 'Restablecer contraseña' : 'Link de contraseña'}
                    </button>
                    <button
                      className="button-ghost"
                      onClick={() => void cambiarActivo(item, !item.activo)}
                    >
                      {item.activo ? 'Inactivar' : 'Reactivar'}
                    </button>
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
