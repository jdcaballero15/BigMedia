import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../shared/api'
import { FieldErrors } from '../../shared/FieldErrors'
import { vigentes } from '../../shared/opciones'
import AvisoDuplicados from './AvisoDuplicados'
import type { Cliente, GrupoEconomico, Marca, Rubro } from './types'

export type MarcaInput = {
  nombre: string
  cliente: number | null
  rubro: number | null
  grupo: number | null
  activo: boolean
  confirmar_distinta?: boolean
}

type Props = {
  marca?: Marca | null
  clientes: Cliente[]
  rubros: Rubro[]
  /** Sin la lista no se ofrece el grupo (el alta rápida desde una campaña). */
  grupos?: GrupoEconomico[]
  onSave: (input: MarcaInput) => Promise<void>
  onCancel: () => void
}

export default function MarcaForm({ marca, clientes, rubros, grupos, onSave, onCancel }: Props) {
  const [nombre, setNombre] = useState(marca?.nombre ?? '')
  const [cliente, setCliente] = useState(String(marca?.cliente ?? ''))
  const [rubro, setRubro] = useState(String(marca?.rubro ?? ''))
  const [grupo, setGrupo] = useState(String(marca?.grupo ?? ''))
  const [activo, setActivo] = useState(marca?.activo ?? true)
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
        cliente: cliente ? Number(cliente) : null,
        rubro: rubro ? Number(rubro) : null,
        grupo: grupo ? Number(grupo) : null,
        activo,
        ...(confirmarDistinta && { confirmar_distinta: true }),
      })
    } catch (cause) {
      if (cause instanceof ApiError && cause.fields.posible_duplicado) {
        setDuplicados(cause.fields.posible_duplicado)
        return
      }
      if (cause instanceof ApiError) setErrors(cause.fields)
      setGeneralError(cause instanceof Error ? cause.message : 'No se pudo guardar la marca.')
    } finally {
      setSaving(false)
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void guardar(false)
  }

  return (
    <form className="card edit-form" aria-label="Formulario de marca" noValidate onSubmit={submit}>
      <div className="form-heading">
        <h3>{marca ? 'Editar marca' : 'Nueva marca'}</h3>
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
            required
          />
          <FieldErrors messages={errors.nombre} />
        </label>
        <label>
          Cliente
          <select value={cliente} onChange={(event) => setCliente(event.target.value)} required>
            <option value="">Seleccionar</option>
            {vigentes(clientes, marca?.cliente).map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre_visible}
                {item.activo ? '' : ' (inactivo)'}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.cliente} />
        </label>
        <label>
          Rubro
          <select value={rubro} onChange={(event) => setRubro(event.target.value)}>
            <option value="">Sin rubro</option>
            {vigentes(rubros, marca?.rubro).map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
                {item.activo ? '' : ' (inactivo)'}
              </option>
            ))}
          </select>
          <FieldErrors messages={errors.rubro} />
        </label>
        {grupos && (
          <label>
            Grupo económico
            <select value={grupo} onChange={(event) => setGrupo(event.target.value)}>
              <option value="">Sin grupo</option>
              {vigentes(grupos, marca?.grupo).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nombre}
                  {item.activo ? '' : ' (inactivo)'}
                </option>
              ))}
            </select>
            <FieldErrors messages={errors.grupo} />
          </label>
        )}
        <label className="checkline">
          <input
            type="checkbox"
            checked={activo}
            onChange={(event) => setActivo(event.target.checked)}
          />
          Activa
        </label>
      </div>
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
        {saving ? 'Guardando…' : 'Guardar marca'}
      </button>
    </form>
  )
}
