import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, apiGet, apiWrite } from '../../shared/api'

type Categoria = 'zonas' | 'proveedores' | 'formatos' | 'estados'
type Registro = {
  id: number
  nombre: string
  activo: boolean
  servicio?: string
  modalidad?: 'fija' | 'digital'
  capacidad_predeterminada?: number
  ancho?: string | null
  alto?: string | null
  operativo?: boolean
  es_baja?: boolean
}

const categoryLabels: Record<Categoria, string> = {
  zonas: 'Departamentos', proveedores: 'Proveedores', formatos: 'Formatos', estados: 'Estados físicos',
}
const singularLabels: Record<Categoria, string> = {
  zonas: 'departamento', proveedores: 'proveedor', formatos: 'formato', estados: 'estado',
}

export default function CatalogosPage() {
  const [categoria, setCategoria] = useState<Categoria>('zonas')
  const [rows, setRows] = useState<Registro[]>([])
  const [editing, setEditing] = useState<Registro | 'new' | null>(null)
  const [nombre, setNombre] = useState('')
  const [servicio, setServicio] = useState('')
  const [modalidad, setModalidad] = useState<'fija' | 'digital'>('fija')
  const [capacidad, setCapacidad] = useState('1')
  const [ancho, setAncho] = useState('')
  const [alto, setAlto] = useState('')
  const [operativo, setOperativo] = useState(false)
  const [esBaja, setEsBaja] = useState(false)
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true
    void apiGet<Registro[]>(`/api/inventario/${categoria}/?incluir_inactivos=1`)
      .then((data) => { if (active) { setRows(data); setError('') } })
      .catch(() => { if (active) setError('No se pudo cargar el catálogo.') })
    return () => { active = false }
  }, [categoria, revision])

  function openForm(record: Registro | 'new') {
    setEditing(record)
    setNombre(record === 'new' ? '' : record.nombre)
    setServicio(record === 'new' ? '' : record.servicio ?? '')
    setModalidad(record === 'new' ? 'fija' : record.modalidad ?? 'fija')
    setCapacidad(String(record === 'new' ? 1 : record.capacidad_predeterminada ?? 1))
    setAncho(record === 'new' ? '' : record.ancho ?? '')
    setAlto(record === 'new' ? '' : record.alto ?? '')
    setOperativo(record === 'new' ? false : record.operativo ?? false)
    setEsBaja(record === 'new' ? false : record.es_baja ?? false)
    setErrors({})
    setError('')
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (editing === null) return
    const data: Record<string, unknown> = { nombre: nombre.trim() }
    if (categoria === 'proveedores') data.servicio = servicio.trim()
    if (categoria === 'formatos') {
      data.modalidad = modalidad
      data.capacidad_predeterminada = Number(capacidad)
      data.ancho = ancho ? ancho : null
      data.alto = alto ? alto : null
    }
    if (categoria === 'estados') { data.operativo = operativo; data.es_baja = esBaja }
    const path = editing === 'new'
      ? `/api/inventario/${categoria}/`
      : `/api/inventario/${categoria}/${editing.id}/`
    setSaving(true)
    setErrors({})
    setError('')
    try {
      await apiWrite(path, editing === 'new' ? 'POST' : 'PATCH', data)
      setEditing(null)
      setRevision((current) => current + 1)
    } catch (cause) {
      if (cause instanceof ApiError) setErrors(cause.fields)
      setError(cause instanceof Error ? cause.message : 'No se pudo guardar.')
    } finally { setSaving(false) }
  }

  async function inactivate(record: Registro) {
    if (!window.confirm(`¿Inactivar ${record.nombre}? Seguirá en el historial.`)) return
    try {
      await apiWrite(`/api/inventario/${categoria}/${record.id}/`, 'PATCH', { activo: false })
      setRevision((current) => current + 1)
    } catch { setError('No se pudo inactivar el registro.') }
  }

  const fieldError = (name: string) => errors[name]?.map((message) => <small className="error" key={message}>{message}</small>)

  return (
    <section>
      <div className="section-heading"><div><p className="eyebrow">Inventario</p><h2>Catálogos</h2><p className="muted">Administrá departamentos, proveedores, formatos y estados.</p></div></div>
      <div className="tabs">{(Object.keys(categoryLabels) as Categoria[]).map((item) => <button key={item} className={item === categoria ? 'active' : ''} onClick={() => { setCategoria(item); setEditing(null) }}>{categoryLabels[item] === 'Proveedores' ? 'Proveedores' : categoryLabels[item]}</button>)}</div>
      <div className="section-heading"><h3>{categoryLabels[categoria]}</h3><button className="button-primary" onClick={() => openForm('new')}>Nuevo {singularLabels[categoria]}</button></div>
      {editing !== null && <form className="card edit-form" aria-label="Formulario de catálogo" onSubmit={(event) => void save(event)}>
        <div className="form-heading"><h3>{editing === 'new' ? 'Nuevo' : 'Editar'} {singularLabels[categoria]}</h3><button className="button-ghost" type="button" onClick={() => setEditing(null)}>Cancelar</button></div>
        <div className="form-grid">
          <label>Nombre<input value={nombre} onChange={(event) => setNombre(event.target.value)} required />{fieldError('nombre')}</label>
          {categoria === 'proveedores' && <label>Servicio<input value={servicio} onChange={(event) => setServicio(event.target.value)} />{fieldError('servicio')}</label>}
          {categoria === 'formatos' && <><label>Modalidad<select value={modalidad} onChange={(event) => setModalidad(event.target.value as 'fija' | 'digital')}><option value="fija">Fija</option><option value="digital">Digital</option></select></label><label>Capacidad predeterminada<input type="number" min="1" value={capacidad} onChange={(event) => setCapacidad(event.target.value)} required />{fieldError('capacidad_predeterminada')}</label><label>Ancho<input type="number" min="0" step="0.01" value={ancho} onChange={(event) => setAncho(event.target.value)} /></label><label>Alto<input type="number" min="0" step="0.01" value={alto} onChange={(event) => setAlto(event.target.value)} /></label></>}
          {categoria === 'estados' && <><label className="checkline"><input type="checkbox" checked={operativo} onChange={(event) => setOperativo(event.target.checked)} />Operativo</label><label className="checkline"><input type="checkbox" checked={esBaja} onChange={(event) => setEsBaja(event.target.checked)} />Es baja</label></>}
        </div>
        {error && <p role="alert" className="error">{error}</p>}
        <button type="submit" className="button-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
      </form>}
      {error && editing === null && <p role="alert" className="error">{error}</p>}
      <div className="card table-wrap"><table><thead><tr><th>Nombre</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td className="primary-cell">{row.nombre}</td><td>{row.activo ? 'Activo' : 'Inactivo'}</td><td className="row-actions"><button className="button-ghost" onClick={() => openForm(row)}>Editar</button>{row.activo && <button className="button-ghost" onClick={() => void inactivate(row)}>Inactivar</button>}</td></tr>)}</tbody></table>{rows.length === 0 && <p className="empty">Todavía no hay registros.</p>}</div>
    </section>
  )
}
