import { useEffect, useState } from 'react'
import { ApiError, apiGet, apiUpload } from '../../shared/api'
import Cifras from '../../shared/Cifras'
import { descargarCsv } from '../../shared/csv'
import { FieldErrors } from '../../shared/FieldErrors'
import type { Formato, Importacion, ResultadoFila } from './types'

const URL = '/api/inventario/importaciones/'

const RESULTADOS: Record<ResultadoFila, string> = {
  creada: 'Creada',
  omitida: 'Omitida',
  rechazada: 'Rechazada',
  en_revision: 'En revisión',
}

// Mismas columnas que la plantilla del reporte (docs/aidlc/inputs/importacion).
const COLUMNAS_REPORTE = [
  'fila',
  'ref_origen',
  'resultado',
  'campo',
  'motivo',
  'cartel_coincidente',
]

function descargarReporte(importacion: Importacion) {
  descargarCsv(
    importacion.simulado ? 'simulacion-importacion.csv' : 'reporte-importacion.csv',
    COLUMNAS_REPORTE,
    importacion.filas.map((fila) => [
      fila.fila,
      fila.ref_origen,
      fila.resultado,
      fila.campo,
      fila.motivo,
      fila.cartel_coincidente,
    ]),
  )
}

/** Importar el inventario desde CSV, con simulación previa y reporte por fila (HU-015). */
export default function ImportacionPage() {
  const [formatos, setFormatos] = useState<Formato[]>([])
  const [formato, setFormato] = useState('')
  const [archivo, setArchivo] = useState<File | null>(null)
  const [resultado, setResultado] = useState<Importacion | null>(null)
  const [errores, setErrores] = useState<Record<string, string[]>>({})
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    let active = true
    void apiGet<Formato[]>('/api/inventario/formatos/')
      .then((datos) => {
        if (active) setFormatos(datos.filter((item) => item.modalidad === 'fija'))
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los formatos.')
      })
    return () => {
      active = false
    }
  }, [])

  async function enviar(simular: boolean) {
    if (archivo === null || formato === '') return
    const form = new FormData()
    form.append('archivo', archivo)
    form.append('formato', formato)
    form.append('simular', simular ? '1' : '0')
    setEnviando(true)
    setErrores({})
    setError('')
    try {
      setResultado(await apiUpload<Importacion>(URL, form, 'POST'))
    } catch (cause) {
      setResultado(null)
      if (cause instanceof ApiError && Object.keys(cause.fields).length > 0) {
        setErrores(cause.fields)
      } else {
        setError(cause instanceof Error ? cause.message : 'No se pudo importar el archivo.')
      }
    } finally {
      setEnviando(false)
    }
  }

  const listo = archivo !== null && formato !== '' && !enviando

  return (
    <section>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Inventario</p>
          <h2>Importar carteles</h2>
          <p className="muted">
            Carga carteles desde un CSV con la plantilla del formato. Simulá primero: muestra el
            mismo reporte sin guardar nada.
          </p>
        </div>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <form className="filters card" onSubmit={(event) => event.preventDefault()}>
        <label>
          Formato
          <select
            value={formato}
            onChange={(event) => {
              setFormato(event.target.value)
              setResultado(null)
            }}
          >
            <option value="">Elegí un formato</option>
            {formatos.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nombre}
              </option>
            ))}
          </select>
          <FieldErrors messages={errores.formato} />
        </label>
        <label>
          Archivo CSV
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => {
              setArchivo(event.target.files?.[0] ?? null)
              setResultado(null)
            }}
          />
          <FieldErrors messages={errores.archivo} />
        </label>
        <div className="row-actions">
          <button type="button" disabled={!listo} onClick={() => void enviar(true)}>
            Simular
          </button>
          <button
            type="button"
            className="button-primary"
            disabled={!listo}
            onClick={() => void enviar(false)}
          >
            Importar
          </button>
        </div>
      </form>
      {resultado && <Reporte importacion={resultado} />}
    </section>
  )
}

function Reporte({ importacion }: { importacion: Importacion }) {
  const { resumen } = importacion
  return (
    <>
      <p role="status">
        {importacion.simulado
          ? 'Simulación: no se guardó nada. Así quedaría la importación.'
          : 'Importación terminada.'}
      </p>
      <Cifras
        titulo="Resumen de la importación"
        cifras={[
          { etiqueta: 'Filas leídas', valor: resumen.leidas },
          {
            etiqueta: importacion.simulado ? 'Se crearían' : 'Creadas',
            valor: resumen.creadas,
            detalle: resumen.incompletas > 0 ? `${resumen.incompletas} incompletas` : undefined,
            tono: 'principal',
          },
          { etiqueta: 'Omitidas', valor: resumen.omitidas, detalle: 'ya existían' },
          {
            etiqueta: 'Rechazadas',
            valor: resumen.rechazadas,
            tono: resumen.rechazadas > 0 ? 'alerta' : undefined,
          },
          {
            etiqueta: 'En revisión',
            valor: resumen.en_revision,
            tono: resumen.en_revision > 0 ? 'alerta' : undefined,
          },
        ]}
      />
      <div className="section-heading">
        <h3>Reporte por fila</h3>
        <button
          type="button"
          className="button-ghost"
          onClick={() => descargarReporte(importacion)}
        >
          Descargar reporte
        </button>
      </div>
      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              <th>Fila</th>
              <th>Resultado</th>
              <th>Motivo</th>
              <th className="col-secundaria">Campo</th>
              <th className="col-secundaria">Origen</th>
              <th>Cartel con el que coincide</th>
            </tr>
          </thead>
          <tbody>
            {importacion.filas.map((fila, indice) => (
              <tr key={`${fila.fila}-${fila.campo}-${indice}`}>
                <td className="primary-cell">{fila.fila}</td>
                <td>{RESULTADOS[fila.resultado]}</td>
                <td>{fila.motivo || '—'}</td>
                <td className="col-secundaria">{fila.campo || '—'}</td>
                <td className="col-secundaria">{fila.ref_origen || '—'}</td>
                <td>{fila.cartel_coincidente || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
