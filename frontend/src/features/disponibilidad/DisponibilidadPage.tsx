import { useState } from 'react'
import OcupacionHoy from './OcupacionHoy'
import CalendarioDisponibilidad from './CalendarioDisponibilidad'

type Vista = 'hoy' | 'calendario'

export default function DisponibilidadPage() {
  const [vista, setVista] = useState<Vista>('hoy')

  return (
    <section className="inventory-page">
      <nav className="topnav" aria-label="Vistas de disponibilidad">
        <button className={vista === 'hoy' ? 'active' : ''} onClick={() => setVista('hoy')}>
          Hoy
        </button>
        <button
          className={vista === 'calendario' ? 'active' : ''}
          onClick={() => setVista('calendario')}
        >
          Calendario
        </button>
      </nav>
      {vista === 'hoy' ? <OcupacionHoy /> : <CalendarioDisponibilidad />}
    </section>
  )
}
