import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, apiGet } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import type { Cliente, Contacto, Marca } from '../clientes/types'
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
  marca: number | null
  recordatorio_fecha: string | null
  recordatorio_texto: string
}

type Props = {
  interaccion?: Interaccion | null
  /** El cliente de la ficha: viene fijo y no se puede cambiar. */
  cliente: Cliente
  onSave: (input: InteraccionInput) => Promise<void>
  onCancel: () => void
}

type Opciones = { contactos: Contacto[]; campanias: Campania[]; marcas: Marca[] }

const SIN_OPCIONES: Opciones = { contactos: [], campanias: [], marcas: [] }

function hoy(): string {
  const ahora = new Date()
  const dos = (numero: number) => String(numero).padStart(2, '0')
  return `${ahora.getFullYear()}-${dos(ahora.getMonth() + 1)}-${dos(ahora.getDate())}`
}

/** Alta y edición de una interacción comercial desde la ficha del cliente (HU-020). */
export default function InteraccionForm({ interaccion, cliente, onSave, onCancel }: Props) {
  const [tipo, setTipo] = useState<TipoInteraccion>(interaccion?.tipo ?? 'llamada')
  const [asunto, setAsunto] = useState(interaccion?.asunto ?? '')
  const [fecha, setFecha] = useState(interaccion?.fecha ?? hoy())
  const [notas, setNotas] = useState(interaccion?.notas ?? '')
  const [contacto, setContacto] = useState(String(interaccion?.contacto ?? ''))
  const [campania, setCampania] = useState(String(interaccion?.campania ?? ''))
  const [marca, setMarca] = useState(String(interaccion?.marca ?? ''))
  const [recordatorioFecha, setRecordatorioFecha] = useState(interaccion?.recordatorio_fecha ?? '')
  const [recordatorioTexto, setRecordatorioTexto] = useState(interaccion?.recordatorio_texto ?? '')
  const [opciones, setOpciones] = useState<Opciones>(SIN_OPCIONES)
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [generalError, setGeneralError] = useState('')
  const [saving, setSaving] = useState(false)

  const esFormal = cliente.tipo === 'intermediario_formal'

  // Contactos activos, campañas y marcas activas del cliente.
  useEffect(() => {
    let active = true
    void Promise.all([
      esFormal
        ? apiGet<Contacto[]>(`/api/clientes/contactos/?cliente=${cliente.id}`)
        : Promise.resolve([]),
      apiGet<Campania[]>(`/api/campanias/campanias/?cliente=${cliente.id}`),
      apiGet<Marca[]>(`/api/clientes/marcas/?cliente=${cliente.id}`),
    ])
      .then(([contactos, campanias, marcas]) => {
        if (active) setOpciones({ contactos, campanias, marcas })
      })
      .catch(() => {
        if (active) setOpciones(SIN_OPCIONES)
      })
    return () => {
      active = false
    }
  }, [cliente.id, esFormal])

  // El contacto que ya tenía la interacción se muestra aunque después se haya inactivado.
  const contactoGuardado =
    interaccion?.contacto != null &&
    !opciones.contactos.some((item) => item.id === interaccion.contacto)
      ? [{ id: interaccion.contacto, nombre: `${interaccion.contacto_nombre ?? ''} (inactivo)` }]
      : []
  const opcionesContacto = [...opciones.contactos, ...contactoGuardado]
  // Igual con la marca; y con una marca elegida, solo sus campañas (RN-018).
  const marcaGuardada =
    interaccion?.marca != null && !opciones.marcas.some((item) => item.id === interaccion.marca)
      ? [{ id: interaccion.marca, nombre: `${interaccion.marca_nombre ?? ''} (inactiva)` }]
      : []
  const opcionesMarca = [...opciones.marcas, ...marcaGuardada]
  const opcionesCampania = marca
    ? opciones.campanias.filter((item) => String(item.marca) === marca)
    : opciones.campanias

  function elegirMarca(valor: string) {
    setMarca(valor)
    const elegida = opciones.campanias.find((item) => String(item.id) === campania)
    if (valor && elegida && String(elegida.marca) !== valor) setCampania('')
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
        cliente: cliente.id,
        contacto: contacto ? Number(contacto) : null,
        campania: campania ? Number(campania) : null,
        marca: marca ? Number(marca) : null,
        recordatorio_fecha: recordatorioFecha || null,
        recordatorio_texto: recordatorioTexto.trim(),
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
          <input value={cliente.nombre_visible} readOnly />
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
          Asunto (opcional)
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
          Marca (opcional)
          <select value={marca} onChange={(event) => elegirMarca(event.target.value)}>
            <option value="">Sin marca</option>
            {opcionesMarca.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.marca} />
        </label>
        <label>
          Campaña (opcional)
          <select value={campania} onChange={(event) => setCampania(event.target.value)}>
            <option value="">Sin campaña</option>
            {opcionesCampania.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre || `Campaña #${item.id}`}
              </option>
            ))}
            {interaccion?.campania != null &&
              !opciones.campanias.some((item) => item.id === interaccion.campania) && (
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
      <fieldset className="form-grid">
        <legend>Recordatorio (opcional)</legend>
        <label>
          Fecha de recordatorio
          <input
            type="date"
            value={recordatorioFecha}
            onChange={(event) => setRecordatorioFecha(event.target.value)}
          />
          <FieldErrors messages={errors.recordatorio_fecha} />
        </label>
        <label>
          Qué hacer
          <input
            value={recordatorioTexto}
            placeholder="Por ejemplo, enviar presupuesto"
            onChange={(event) => setRecordatorioTexto(event.target.value)}
          />
          <FieldErrors messages={errors.recordatorio_texto} />
        </label>
      </fieldset>
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
