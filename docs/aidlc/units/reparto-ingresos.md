# Unidad: Reparto de ingresos por día

- **Estado:** en curso · **Épica:** E8 Reportes y paneles · **App dueña:** `reservas`
- **Origen:** HU-051 · **Rama:** `feature/reservas-reparto-ingresos`

## Objetivo

Repartir el ingreso de una reserva entre los meses que corre, en proporción a los días de cada mes,
para que los reportes mensuales no queden distorsionados (HU-051). Es cálculo puro, base de HU-049.

## Cambios

- `reservas/services.py`: `reparto_por_mes(reserva)` → el `reserva.total` dividido por mes según los
  días (inclusive inicio y fin). La suma de los meses es exactamente el total; el último mes absorbe el
  redondeo. Devuelve una lista ordenada `[{ mes: 'YYYY-MM', etiqueta: 'Nov 2026', monto }]`.
- `reservas/views.py` + `urls.py`: endpoint de solo lectura `GET /api/reservas/reparto/?reserva=<id>`
  que expone el reparto.
- Sin frontend: HU-051 es cálculo del sistema; lo consumen los reportes (HU-049), no una pantalla.

### Reglas (HU-051)

- Días por mes = días del rango `[fecha_inicio, fecha_fin]` que caen en ese mes (inclusive ambos
  extremos). `monto_mes = round(total * dias_mes / dias_totales, 2)`; el último mes = `total - suma de
  los anteriores`, para que la suma coincida al centavo.
- Sirve igual para alquileres mensuales y de 15 días (se reparte por días reales).

## Migraciones

Ninguna.

## Reglas que se usan

Ninguna del catálogo RN-xxx; implementa directamente HU-051.

## Cómo se prueba

- Backend (`backend/tests/test_reparto.py`, PostgreSQL real):
  - una reserva de sep a nov reparte el total en 3 meses proporcional a los días; la suma == total al
    centavo (HU-051 criterios 1 y 3).
  - una reserva de 15 días asigna por los días reales dentro del mes (criterio 2).
  - una reserva dentro de un solo mes asigna todo a ese mes; endpoint con reserva inexistente → 400;
    anónimo → 401/403.

## Registro de gates

- Gate 1 (plan): 2026-10-20 — aprobado (campo a repartir confirmado: `reserva.total`).
- Gate 2 (verificación): 2026-10-20 — `ruff format --check`, `ruff check`, `mypy backend`,
  `makemigrations --check` y gitleaks en verde; `pytest --cov` 239 pasan, cobertura total 94.64 %
  (umbral 80 %). Frontend no aplica (unidad sin frontend). Pendiente de Juan Diego.
- Gate 3 (PR): —
