import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, apiGet } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { vigentes } from '../../shared/opciones'
import type { Cliente, Contacto } from '../clientes/types'
import type { Campania, Interaccion, TipoInteraccion } from './types'
import { TIPOS_INTERACCION } from './types'

export type InteraccionInput = {
  tipo: TipoInteraccion
  asunto: string
  fecha: string
  notas: string
  cliente: number | null
  contacto: number | null
  campania: number | null
}

type Props = {
  interaccion?: Interaccion | null
  clientes: Cliente[]
  onSave: (input: InteraccionInput) => Promise<void>
  onCancel: () => void
}

type Opciones = { cliente: string; contactos: Contacto[]; campanias: Campania[] }

function hoy(): string {
  const ahora = new Date()
  const dos = (numero: number) => String(numero).padStart(2, '0')
  return `${ahora.getFullYear()}-${dos(ahora.getMonth() + 1)}-${dos(ahora.getDate())}`
}

/** Alta y edición de una interacción comercial (HU-020). */
export default function InteraccionForm({ interaccion, clientes, onSave, onCancel }: Props) {
  const [tipo, setTipo] = useState<TipoInteraccion>(interaccion?.tipo ?? 'llamada')
  const [asunto, setAsunto] = useState(interaccion?.asunto ?? '')
  const [fecha, setFecha] = useState(interaccion?.fecha ?? hoy())
  const [notas, setNotas] = useState(interaccion?.notas ?? '')
  const [cliente, setCliente] = useState(String(interaccion?.cliente ?? ''))
  const [contacto, setContacto] = useState(String(interaccion?.contacto ?? ''))
  const [campania, setCampania] = useState(String(interaccion?.campania ?? ''))
  const [opciones, setOpciones] = useState<Opciones>({ cliente: '', contactos: [], campanias: [] })
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [generalError, setGeneralError] = useState('')
  const [saving, setSaving] = useState(false)

  const clienteElegido = clientes.find((item) => String(item.id) === cliente)
  const esFormal = clienteElegido?.tipo === 'intermediario_formal'

  // Contactos activos y campañas del cliente elegido.
  useEffect(() => {
    if (!cliente) return
    let active = true
    void Promise.all([
      esFormal
        ? apiGet<Contacto[]>(`/api/clientes/contactos/?cliente=${cliente}`)
        : Promise.resolve([]),
      apiGet<Campania[]>(`/api/campanias/campanias/?cliente=${cliente}`),
    ])
      .then(([contactos, campanias]) => {
        if (active) setOpciones({ cliente, contactos, campanias })
      })
      .catch(() => {
        if (active) setOpciones({ cliente, contactos: [], campanias: [] })
      })
    return () => {
      active = false
    }
  }, [cliente, esFormal])

  const cargadas = opciones.cliente === cliente ? opciones : { contactos: [], campanias: [] }
  // El contacto que ya tenía la interacción se muestra aunque después se haya inactivado.
  const contactoGuardado =
    interaccion?.contacto != null &&
    String(interaccion.cliente) === cliente &&
    !cargadas.contactos.some((item) => item.id === interaccion.contacto)
      ? [{ id: interaccion.contacto, nombre: `${interaccion.contacto_nombre ?? ''} (inactivo)` }]
      : []
  const opcionesContacto = [...cargadas.contactos, ...contactoGuardado]

  function elegirCliente(valor: string) {
    setCliente(valor)
    setContacto('')
    setCampania('')
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors({})
    setGeneralError('')
    setSaving(true)
    try {
      await onSave({
        tipo,
        asunto: asunto.trim(),
        fecha,
        notas: notas.trim(),
        cliente: cliente ? Number(cliente) : null,
        contacto: contacto ? Number(contacto) : null,
        campania: campania ? Number(campania) : null,
      })
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
      setGeneralError(cause instanceof Error ? cause.message : 'No se pudo guardar la interacción.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      className="card edit-form"
      aria-label="Formulario de interacción"
      noValidate
      onSubmit={(event) => void submit(event)}
    >
      <div className="form-heading">
        <h3>{interaccion ? 'Editar interacción' : 'Nueva interacción'}</h3>
        <button type="button" className="button-ghost" onClick={onCancel}>
          Cancelar
        </button>
      </div>
      <div className="form-grid">
        <label>
          Cliente
          <select value={cliente} onChange={(event) => elegirCliente(event.target.value)}>
            <option value="">Seleccionar</option>
            {vigentes(clientes, interaccion?.cliente).map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre_visible}
                {item.activo ? '' : ' (inactivo)'}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.cliente} />
        </label>
        <label>
          Tipo
          <select value={tipo} onChange={(event) => setTipo(event.target.value as TipoInteraccion)}>
            {TIPOS_INTERACCION.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.tipo} />
        </label>
        <label>
          Fecha
          <input type="date" value={fecha} onChange={(event) => setFecha(event.target.value)} />
          <FieldErrors messages={errors.fecha} />
        </label>
        <label>
          Asunto
          <input value={asunto} onChange={(event) => setAsunto(event.target.value)} />
          <FieldErrors messages={errors.asunto} />
        </label>
        {esFormal && (
          <label>
            Contacto
            <select value={contacto} onChange={(event) => setContacto(event.target.value)}>
              <option value="">Sin contacto</option>
              {opcionesContacto.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nombre}
                </option>
              ))}
            </select>
            <FieldErrors messages={errors.contacto} />
          </label>
        )}
        <label>
          Campaña (opcional)
          <select
            value={campania}
            disabled={!cliente}
            onChange={(event) => setCampania(event.target.value)}
          >
            <option value="">Sin campaña</option>
            {cargadas.campanias.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre || `Campaña #${item.id}`}
              </option>
            ))}
            {interaccion?.campania != null &&
              String(interaccion.cliente) === cliente &&
              !cargadas.campanias.some((item) => item.id === interaccion.campania) && (
                <option value={interaccion.campania}>{interaccion.campania_nombre}</option>
              )}
          </select>
          <FieldErrors messages={errors.campania} />
        </label>
      </div>
      <label>
        Notas
        <textarea rows={3} value={notas} onChange={(event) => setNotas(event.target.value)} />
        <FieldErrors messages={errors.notas} />
      </label>
      {generalError && (
        <p className="error" role="alert">
          {generalError}
        </p>
      )}
      <button type="submit" className="button-primary" disabled={saving}>
        {saving ? 'Guardando…' : 'Guardar interacción'}
      </button>
    </form>
  )
}
