import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/' : '/',
  plugins: [react()],
  server: {
    proxy: {
      // Conserva el Host del navegador para que Django acepte el Origin en el chequeo CSRF.
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false },
    },
  },
  test: {
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      // Líneas y sentencias son obligatorias; funciones y ramas se informan (ADR-0004).
      thresholds: { lines: 80, statements: 80 },
    },
  },
}))
