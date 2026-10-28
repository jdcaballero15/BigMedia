import { useEffect, useState } from 'react'
import { apiGet, apiWrite } from '../../shared/api'
import { usePuedeEditar } from '../../shared/sesion'
import ContactoForm from './ContactoForm'
import type { ContactoInput } from './ContactoForm'
import type { Cliente, Contacto } from './types'
import MenuFila from '../../shared/MenuFila'
import { iniciales } from './iniciales'

const URL = '/api/clientes/contactos/'

type Carga = { estado: 'cargando' | 'error' | 'listo'; contactos: Contacto[] }

function estadoDe(contacto: Contacto): string {
  if (!contacto.activo) return 'Inactivo'
  return contacto.principal ? 'Principal' : 'Activo'
}

/** Contactos de un intermediario formal, en su ficha (HU-068). */
export default function ContactosDelCliente({
  cliente,
  onCargados,
}: {
  cliente: Cliente
  /** Avisa cuántos contactos trajo, para el contador de la ficha. */
  onCargados?: (cantidad: number) => void
}) {
  const puedeEditar = usePuedeEditar()
  const [carga, setCarga] = useState<Carga>({ estado: 'cargando', contactos: [] })
  const [editing, setEditing] = useState<Contacto | 'new' | null>(null)
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let active = true
    void apiGet<Contacto[]>(`${URL}?cliente=${cliente.id}&incluir_inactivos=1`)
      .then((contactos) => {
        if (!active) return
        setCarga({ estado: 'listo', contactos })
        onCargados?.(contactos.length)
      })
      .catch(() => {
        if (active) setCarga({ estado: 'error', contactos: [] })
      })
    return () => {
      active = false
    }
  }, [cliente.id, revision, onCargados])

  async function guardar(input: ContactoInput) {
    if (editing === null) return
    if (editing === 'new') await apiWrite(URL, 'POST', { ...input, cliente: cliente.id })
    else await apiWrite(`${URL}${editing.id}/`, 'PATCH', input)
    setEditing(null)
    setRevision((current) => current + 1)
  }

  async function cambiar(contacto: Contacto, cambios: Partial<Contacto>) {
    setError('')
    try {
      await apiWrite(`${URL}${contacto.id}/`, 'PATCH', cambios)
      setRevision((current) => current + 1)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'No se pudo cambiar el contacto.')
    }
  }

  const titulo = `Contactos de ${cliente.nombre_visible}`
  return (
    <section className="card edit-form section-gap contactos" aria-label={titulo}>
      <div className="form-heading">
        <h3>Contactos</h3>
        {puedeEditar && (
          <button type="button" className="button-primary" onClick={() => setEditing('new')}>
            Nuevo contacto
          </button>
        )}
      </div>
      {editing !== null && (
        <ContactoForm
          key={editing === 'new' ? 'nuevo' : editing.id}
          contacto={editing === 'new' ? null : editing}
          onSave={guardar}
          onCancel={() => setEditing(null)}
        />
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {carga.estado === 'cargando' ? (
        <p className="empty">Cargando contactos…</p>
      ) : carga.estado === 'error' ? (
        <p className="error" role="alert">
          No se pudieron cargar los contactos.
        </p>
      ) : carga.contactos.length === 0 ? (
        <p className="empty">Este cliente todavía no tiene contactos.</p>
      ) : (
        <ul className="lista-contactos" aria-label="Contactos">
          {carga.contactos.map((contacto) => (
            <li key={contacto.id} className={contacto.activo ? '' : 'inactivo'}>
              <span className="avatar" aria-hidden="true">
                {iniciales(contacto.nombre)}
              </span>
              <div className="lista-contactos-datos">
                <strong>{contacto.nombre}</strong>
                <small>{contacto.cargo || '—'}</small>
                <small>
                  {[contacto.correo, contacto.telefono].filter(Boolean).join(' · ') || '—'}
                </small>
              </div>
              <span className={contacto.principal ? 'etiqueta etiqueta-azul' : 'etiqueta'}>
                {estadoDe(contacto)}
              </span>
              {puedeEditar && (
                <span className="row-actions">
                  <button className="button-ghost" onClick={() => setEditing(contacto)}>
                    Editar
                  </button>
                  <MenuFila
                    acciones={[
                      contacto.activo &&
                        !contacto.principal && {
                          etiqueta: 'Marcar como principal',
                          onClick: () => void cambiar(contacto, { principal: true }),
                        },
                      {
                        etiqueta: contacto.activo ? 'Inactivar' : 'Reactivar',
                        onClick: () => void cambiar(contacto, { activo: !contacto.activo }),
                      },
                    ]}
                  />
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
