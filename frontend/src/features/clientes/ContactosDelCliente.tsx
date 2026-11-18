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

function ordenarContactos(contactos: Contacto[]): Contacto[] {
  const planificadores = contactos
    .filter((contacto) => contacto.rol !== 'asistente')
    .sort((a, b) => Number(b.principal) - Number(a.principal))
  const asistentes = contactos.filter((contacto) => contacto.rol === 'asistente')
  const vinculados = new Set<number>()
  const ordenados = planificadores.flatMap((planificador) => {
    const propios = asistentes.filter((asistente) => asistente.planificador === planificador.id)
    propios.forEach((asistente) => vinculados.add(asistente.id))
    return [planificador, ...propios]
  })
  return [...ordenados, ...asistentes.filter((asistente) => !vinculados.has(asistente.id))]
}

/** Planificadores y asistentes de una central de medios. */
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
  const [viendo, setViendo] = useState<Contacto | null>(null)
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
          planificadores={carga.contactos.filter((contacto) => contacto.rol !== 'asistente')}
          onSave={guardar}
          onCancel={() => setEditing(null)}
        />
      )}
      {viendo && (
        <div
          className="contacto-detalle-fondo"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setViendo(null)
          }}
        >
          <section
            className="contacto-detalle"
            role="dialog"
            aria-modal="true"
            aria-labelledby="contacto-detalle-titulo"
          >
            <div className="form-heading">
              <div>
                <h3 id="contacto-detalle-titulo">{viendo.nombre}</h3>
                <p>{viendo.rol === 'asistente' ? 'Asistente' : 'Planificador'}</p>
              </div>
              <button
                type="button"
                className="button-ghost"
                aria-label="Cerrar detalle"
                onClick={() => setViendo(null)}
              >
                Cerrar
              </button>
            </div>
            <dl className="contacto-detalle-datos">
              <div>
                <dt>Cargo</dt>
                <dd>{viendo.cargo || '—'}</dd>
              </div>
              <div>
                <dt>Correo</dt>
                <dd>{viendo.correo || '—'}</dd>
              </div>
              <div>
                <dt>Teléfono</dt>
                <dd>{viendo.telefono || '—'}</dd>
              </div>
              <div>
                <dt>Estado</dt>
                <dd>{estadoDe(viendo)}</dd>
              </div>
              {viendo.rol === 'asistente' && (
                <div>
                  <dt>Planificador</dt>
                  <dd>
                    {carga.contactos.find((item) => item.id === viendo.planificador)?.nombre ??
                      'No disponible'}
                  </dd>
                </div>
              )}
              {viendo.notas && (
                <div className="contacto-detalle-notas">
                  <dt>Notas</dt>
                  <dd>{viendo.notas}</dd>
                </div>
              )}
              {viendo.rol === 'planificador' && (
                <div className="contacto-detalle-notas">
                  <dt>Asistentes</dt>
                  <dd>
                    {carga.contactos
                      .filter((item) => item.rol === 'asistente' && item.planificador === viendo.id)
                      .map((item) => item.nombre)
                      .join(', ') || 'Sin asistentes asignados'}
                  </dd>
                </div>
              )}
            </dl>
            {puedeEditar && (
              <div className="form-actions">
                <button
                  type="button"
                  className="button-primary"
                  onClick={() => {
                    setViendo(null)
                    setEditing(viendo)
                  }}
                >
                  Editar contacto
                </button>
              </div>
            )}
          </section>
        </div>
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
          {ordenarContactos(carga.contactos).map((contacto) => (
            <li
              key={contacto.id}
              className={[
                contacto.rol === 'asistente' ? 'asistente' : '',
                contacto.activo ? '' : 'inactivo',
              ].join(' ')}
            >
              <span className="avatar" aria-hidden="true">
                {iniciales(contacto.nombre)}
              </span>
              <div className="lista-contactos-datos">
                <button
                  type="button"
                  className="contacto-nombre"
                  onClick={() => setViendo(contacto)}
                  aria-label={`Ver detalles de ${contacto.nombre}`}
                >
                  <strong>{contacto.nombre}</strong>
                </button>
                <small>
                  {contacto.rol === 'asistente'
                    ? `Asistente de ${carga.contactos.find((item) => item.id === contacto.planificador)?.nombre ?? 'planificador inactivo'}`
                    : 'Planificador'}
                </small>
                <small>{contacto.cargo || '—'}</small>
                <small>
                  {[contacto.correo, contacto.telefono].filter(Boolean).join(' · ') || '—'}
                </small>
              </div>
              <span className={contacto.principal ? 'etiqueta etiqueta-azul' : 'etiqueta'}>
                {estadoDe(contacto)}
              </span>
              <span className="row-actions">
                <button type="button" className="button-ghost" onClick={() => setViendo(contacto)}>
                  Ver detalles
                </button>
                {puedeEditar && (
                  <button className="button-ghost" onClick={() => setEditing(contacto)}>
                    Editar
                  </button>
                )}
                {puedeEditar && (
                  <MenuFila
                    acciones={[
                      contacto.rol !== 'asistente' &&
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
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
