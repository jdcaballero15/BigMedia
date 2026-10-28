import { useState } from 'react'
import OcupacionHoy from './OcupacionHoy'
import CalendarioDisponibilidad from './CalendarioDisponibilidad'

type Vista = 'hoy' | 'calendario'

const VISTAS: { id: Vista; label: string }[] = [
  { id: 'hoy', label: 'Hoy' },
  { id: 'calendario', label: 'Calendario' },
]

export default function DisponibilidadPage() {
  const [vista, setVista] = useState<Vista>('hoy')

  const pestanias = (
    <div className="pildoras" role="group" aria-label="Vistas de disponibilidad">
      {VISTAS.map((item) => (
        <button
          key={item.id}
          className={vista === item.id ? 'active' : ''}
          aria-pressed={vista === item.id}
          onClick={() => setVista(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  )

  return (
    <section>
      {vista === 'hoy' ? (
        <OcupacionHoy pestanias={pestanias} />
      ) : (
        <CalendarioDisponibilidad pestanias={pestanias} />
      )}
    </section>
  )
}
