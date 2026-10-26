import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import AvisoDuplicados from './AvisoDuplicados'
import { TIPOS_CLIENTE } from './types'
import type { Cliente, TipoCliente } from './types'

export type ClienteInput = {
  nombre: string
  razon_social: string
  cuit: string
  tipo: TipoCliente | ''
  telefono: string
  correo: string
  activo: boolean
  confirmar_distinta?: boolean
}

type Props = {
  cliente?: Cliente | null
  onSave: (input: ClienteInput) => Promise<void>
  onCancel: () => void
}

export default function ClienteForm({ cliente, onSave, onCancel }: Props) {
  const [nombre, setNombre] = useState(cliente?.nombre ?? '')
  const [razonSocial, setRazonSocial] = useState(cliente?.razon_social ?? '')
  const [cuit, setCuit] = useState(cliente?.cuit ?? '')
  const [tipo, setTipo] = useState<TipoCliente | ''>(cliente?.tipo ?? '')
  const [telefono, setTelefono] = useState(cliente?.telefono ?? '')
  const [correo, setCorreo] = useState(cliente?.correo ?? '')
  const [activo, setActivo] = useState(cliente?.activo ?? true)
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [generalError, setGeneralError] = useState('')
  const [saving, setSaving] = useState(false)
  const [duplicados, setDuplicados] = useState<string[]>([])

  async function guardar(confirmarDistinta: boolean) {
    setErrors({})
    setDuplicados([])
    setGeneralError('')
    setSaving(true)
    try {
      await onSave({
        nombre: nombre.trim(),
        razon_social: razonSocial.trim(),
        cuit: cuit.trim(),
        tipo,
        telefono: telefono.trim(),
        correo: correo.trim(),
        activo,
        ...(confirmarDistinta && { confirmar_distinta: true }),
      })
    } catch (cause) {
      // El alta de un cliente directo avisa si su marca homónima se parece a otra (HU-019).
      if (cause instanceof ApiError && cause.fields.posible_duplicado) {
        setDuplicados(cause.fields.posible_duplicado)
        return
      }
      if (cause instanceof ApiError) setErrors(cause.fields)
      setGeneralError(cause instanceof Error ? cause.message : 'No se pudo guardar el cliente.')
    } finally {
      setSaving(false)
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void guardar(false)
  }

  return (
    <form
      className="card edit-form"
      aria-label="Formulario de cliente"
      noValidate
      onSubmit={submit}
    >
      <div className="form-heading">
        <h3>{cliente ? 'Editar cliente' : 'Nuevo cliente'}</h3>
        <button type="button" className="button-ghost" onClick={onCancel}>
          Cancelar
        </button>
      </div>
      <div className="form-grid">
        <label>
          Nombre
          <input
            value={nombre}
            onChange={(event) => {
              setNombre(event.target.value)
              setDuplicados([])
            }}
          />
          <FieldErrors messages={errors.nombre} />
        </label>
        <label>
          Razón social
          <input value={razonSocial} onChange={(event) => setRazonSocial(event.target.value)} />
          <FieldErrors messages={errors.razon_social} />
        </label>
        <label>
          CUIT
          <input
            value={cuit}
            onChange={(event) => setCuit(event.target.value)}
            placeholder="20-12345678-6"
            inputMode="numeric"
          />
          <FieldErrors messages={errors.cuit} />
        </label>
        <label>
          Tipo
          <select
            value={tipo}
            onChange={(event) => setTipo(event.target.value as TipoCliente | '')}
          >
            <option value="">Sin tipo</option>
            {TIPOS_CLIENTE.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.tipo} />
        </label>
        <label>
          Teléfono
          <input value={telefono} onChange={(event) => setTelefono(event.target.value)} />
          <FieldErrors messages={errors.telefono} />
        </label>
        <label>
          Correo
          <input type="email" value={correo} onChange={(event) => setCorreo(event.target.value)} />
          <FieldErrors messages={errors.correo} />
        </label>
        <label className="checkline">
          <input
            type="checkbox"
            checked={activo}
            onChange={(event) => setActivo(event.target.checked)}
          />
          Activo
        </label>
      </div>
      {!cliente && tipo === 'directo' && (
        <p className="muted">
          Si tiene nombre, al guardarlo se crea también una marca con ese nombre.
        </p>
      )}
      <AvisoDuplicados
        coincidentes={duplicados}
        saving={saving}
        onConfirmar={() => void guardar(true)}
      />
      {generalError && (
        <p className="error" role="alert">
          {generalError}
        </p>
      )}
      <button type="submit" className="button-primary" disabled={saving}>
        {saving ? 'Guardando…' : 'Guardar cliente'}
      </button>
    </form>
  )
}
