# Unidad: Disponibilidad — ocupación de hoy

- **Estado:** en curso · **Épica:** E6 Vista de disponibilidad · **App dueña:** `reservas`
- **Origen:** HU-041 · **Rama:** `feature/reservas-disponibilidad-hoy`

## Objetivo

Dar una vista de la ocupación **actual** de los carteles: una lista ordenada por estado de ocupación,
con accesos rápidos a Libres y Ocupados y los filtros del inventario, para ver de un vistazo qué hay
disponible hoy (HU-041). No proyecta a futuro: el calendario (HU-042) es una unidad posterior.

## Cambios

- `reservas/views.py` + `services.py`: endpoint de solo lectura `GET /api/reservas/disponibilidad/`
  que devuelve, por cartel no dado de baja, su capacidad, cupos ocupados hoy y si está libre. Reusa la
  lógica de ocupación de HU-040. Sin modelo nuevo, sin migración.
- Frontend `frontend/src/features/disponibilidad/`: `DisponibilidadPage` (tabla + accesos Libres/Ocupados
  + filtros zona/formato/modalidad). Pestaña "Disponibilidad" en `App.tsx`.

### Endpoint `GET /api/reservas/disponibilidad/`

- Devuelve una fila por cartel con `estado.es_baja = False` (se excluyen las bajas, RN de HU-041):
  `{ id, nombre_visible, formato_nombre, zona_nombre, modalidad, capacidad, ocupados, libre }`.
- `ocupados` = reservas del cartel que ocupan cupo hoy (estado ≠ cancelada, con hoy dentro del rango).
  `libre = ocupados < capacidad`. Multi-marca: se muestra `ocupados` sobre `capacidad`.
- Orden por disponibilidad: primero los que tienen más cupos libres (`capacidad - ocupados`).
- Filtros combinables (intersección): `zona`, `formato`, `modalidad`, y acceso rápido
  `ocupacion=libres|ocupados`. Se respetan junto con los del inventario (HU-041 criterio 3).
- Permiso `config.permisos.LecturaConSesionEdicionOperativo` (lectura con sesión iniciada).

## Migraciones

Ninguna.

## Reglas provisorias que se usan

- Reusa la ocupación de HU-040 (RN-004/RN-005: una reserva ocupa un cupo genérico). El día de borde
  (RN-001) ya está en el servicio de disponibilidad; acá la ocupación es puntual (hoy), sin rango.

## Cómo se prueba

- Backend (`backend/tests/test_disponibilidad_hoy.py`, PostgreSQL real):
  - lista excluye carteles de baja (HU-041).
  - `ocupados` cuenta las reservas vigentes hoy (confirmadas/pendientes/finalizadas) y no las canceladas;
    `libre` es correcto contra la capacidad; multi-marca muestra `ocupados`/`capacidad` (HU-040/HU-041).
  - acceso rápido `libres`/`ocupados` filtra bien; filtros `zona`/`formato`/`modalidad` se combinan
    (HU-041 criterios 2 y 3).
  - orden por cupos libres; anónimo sin sesión → 401/403.
- Frontend (Vitest): `DisponibilidadPage` lista los carteles con su ocupación y los accesos
  Libres/Ocupados y filtros cambian la consulta.

## Decisiones

- **Alcance (Juan Diego, 2026-10-19):** solo HU-041 (ocupación de hoy). HU-042 (calendario a futuro,
  pregunta 20 de Seba / RN-013) queda para una unidad siguiente.

## Registro de gates

- Gate 1 (plan): 2026-10-19 — aprobado por Juan Diego.
- Gate 2 (verificación): 2026-10-19 — `ruff format --check`/`ruff check` sin errores; `mypy backend`
  sin problemas (68 archivos); `makemigrations --check` sin cambios; `pytest --cov` 202 pasan, total
  94 %; frontend `format:check`/`lint`/`typecheck` OK, `test:coverage` 66 pasan (líneas 89.1 %),
  `build` OK; `pre-commit run --all-files` todo en verde. Aprobado por Juan Diego.
- Gate 3 (PR): —
