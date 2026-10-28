import { useEffect, useState } from 'react'
import { apiGet } from '../../shared/api'
import type { Marca } from './types'

type Props = {
  /** La marca de la ficha: se excluye de la lista. */
  marca: Marca
  grupo: number
}

type Carga = { estado: 'cargando' | 'error' | 'listo'; filas: Marca[] }

/** Las otras marcas del grupo económico de una marca (HU-022 criterio 2, RN-016). */
export default function MarcasDelGrupo({ marca, grupo }: Props) {
  const [carga, setCarga] = useState<Carga>({ estado: 'cargando', filas: [] })
  const titulo = `Otras marcas del grupo ${marca.grupo_nombre ?? ''}`.trim()

  useEffect(() => {
    let active = true
    void apiGet<Marca[]>(`/api/clientes/marcas/?grupo=${grupo}&incluir_inactivos=1`)
      .then((filas) => {
        if (active) setCarga({ estado: 'listo', filas: filas.filter((m) => m.id !== marca.id) })
      })
      .catch(() => {
        if (active) setCarga({ estado: 'error', filas: [] })
      })
    return () => {
      active = false
    }
  }, [grupo, marca.id])

  return (
    <section className="card table-wrap section-gap" aria-label={titulo}>
      <h3>{titulo}</h3>
      {carga.estado === 'cargando' ? (
        <p className="empty">Cargando marcas…</p>
      ) : carga.estado === 'error' ? (
        <p className="error" role="alert">
          No se pudieron cargar las marcas del grupo.
        </p>
      ) : carga.filas.length === 0 ? (
        <p className="empty">No hay otras marcas en el grupo.</p>
      ) : (
        <table aria-label="Marcas del grupo">
          <thead>
            <tr>
              <th>Marca</th>
              <th>Cliente</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {carga.filas.map((fila) => (
              <tr key={fila.id}>
                <td className="primary-cell">{fila.nombre}</td>
                <td>{fila.cliente_nombre}</td>
                <td>{fila.activo ? 'Activa' : 'Inactiva'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
