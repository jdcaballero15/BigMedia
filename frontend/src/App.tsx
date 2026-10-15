import { useEffect, useState } from 'react'
import './App.css'

type ApiStatus = 'checking' | 'available' | 'unavailable'

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking')

  useEffect(() => {
    const controller = new AbortController()

    async function checkApi() {
      try {
        const response = await fetch('/api/health/', { signal: controller.signal })
        if (!response.ok) {
          setApiStatus('unavailable')
          return
        }

        const data: { status?: string } = await response.json()
        setApiStatus(data.status === 'ok' ? 'available' : 'unavailable')
      } catch {
        if (!controller.signal.aborted) setApiStatus('unavailable')
      }
    }

    void checkApi()
    return () => controller.abort()
  }, [])

  const statusLabel = {
    checking: 'Comprobando API',
    available: 'API disponible',
    unavailable: 'API no disponible',
  }[apiStatus]

  return (
    <main className="page">
      <div className="shell">
        <p className="eyebrow">Sistema de reservas OOH</p>
        <h1>Big Media</h1>
        <p className="intro">
          Base de desarrollo del sistema de inventario, campañas y reservas de
          publicidad de vía pública.
        </p>

        <section className="status-card" aria-label="Estado del entorno">
          <span className={`status-dot status-dot--${apiStatus}`} aria-hidden="true" />
          <div>
            <strong>{statusLabel}</strong>
            <p>La conexión con la API y PostgreSQL se comprueba al abrir esta página.</p>
          </div>
        </section>

        <p className="footnote">El sistema funcional está en preparación.</p>
      </div>
    </main>
  )
}

export default App
