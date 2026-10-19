# Unidad: Disponibilidad — calendario a futuro

- **Estado:** mergeada · **Épica:** E6 Vista de disponibilidad · **App dueña:** `reservas`
- **Origen:** HU-042 (usa RN-001, RN-003, RN-013) · **Rama:** `feature/reservas-calendario-disponibilidad`

## Objetivo

Responder "¿está libre en octubre?" sin abrir registros: una grilla de carteles (filas) × períodos
(columnas) con la ocupación de cada celda, para un rango y una zona elegidos. Completa E6 (HU-042).

## Granularidad resuelta — meses (Juan Diego, 2026-10-19)

Columnas por **mes** (3 a 12). Cada celda muestra la **ocupación pico** del mes (máximo de cupos
usados en algún día del mes). Responde directo "¿libre en octubre?"; liviano y rápido.

## Cambios

- `reservas/services.py`: `calendario_disponibilidad(desde, hasta, filtros)` → por cartel (no de baja),
  la ocupación pico por período (pico diario de RN-003 acotado a cada período; día de borde RN-001).
- `reservas/views.py` + `urls.py`: `GET /api/reservas/calendario/` con `desde`, `hasta`, `zona`,
  `formato`, `modalidad`. Rango por defecto 3 meses desde hoy; máximo 12 meses (se valida).
- Frontend `frontend/src/features/disponibilidad/`: `CalendarioDisponibilidad` (grilla con celdas
  coloreadas por ocupación; click en una celda ocupada muestra campaña y reserva que la ocupan). Se
  suma como segunda vista dentro de la pestaña Disponibilidad (junto a "Ocupación de hoy").
- El detalle de celda (criterio 3) reusa `GET /api/reservas/reservas/?cartel=…` filtrando por el período.

### Reglas y comportamiento

- Celda = ocupación pico del período / capacidad (multi-marca: "12/20"); color por nivel de ocupación.
- Carteles de baja: excluidos por defecto; señalados si se piden (HU-042 criterio 4).
- Performance: una sola consulta de reservas del rango + carteles; el pico se calcula en memoria.
  Objetivo < 3 s con 12 meses sobre el inventario real (HU-042 criterio 1).

## Migraciones

Ninguna.

## Reglas provisorias que se usan

- **RN-003 (pico diario)** acotado a cada período · **RN-001 (día de borde)** para el solapamiento ·
  **RN-013**: se construye como Should (su respuesta sigue pendiente; no bloquea).

## Cómo se prueba

- Backend (`backend/tests/test_calendario.py`, PostgreSQL real):
  - devuelve una columna por período del rango; rango por defecto 3 meses; > 12 meses se rechaza.
  - la celda refleja la ocupación pico del período (una reserva que cubre parte del mes lo marca
    ocupado; cancelada no cuenta); multi-marca muestra ocupados/capacidad.
  - filtros `zona`/`formato`/`modalidad` y exclusión de bajas.
  - anónimo sin sesión → 401/403.
- Frontend (Vitest): la grilla muestra carteles × períodos con su ocupación; el click en una celda
  ocupada dispara la consulta de las reservas de ese cartel/período.

## Decisiones

- **Hacer HU-042 (Juan Diego, 2026-10-19):** se construye el calendario (RN-013 default). Granularidad
  a resolver en este Gate 1 (ver arriba).

## Registro de gates

- Gate 1 (plan): 2026-10-19 — aprobado por Juan Diego (granularidad = meses).
- Gate 2 (verificación): 2026-10-19 — `ruff format --check`/`ruff check` sin errores; `mypy backend`
  sin problemas (69 archivos); `makemigrations --check` sin cambios; `pytest --cov` 209 pasan, total
  94.3 %; frontend `format:check`/`lint`/`typecheck` OK, `test:coverage` 70 pasan (líneas 88.7 %),
  `build` OK; `pre-commit run --all-files` todo en verde. Aprobado por Juan Diego.
- Gate 3 (PR): #20 (mergeado a develop el 2026-10-19).
