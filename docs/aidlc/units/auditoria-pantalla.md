# Unidad: Pantalla de auditoría

- **Estado:** en curso · **Épica:** E1 Seguridad y acceso · **App dueña:** `frontend` (+ `auditoria`)
- **Origen:** HU-007 (pantalla) · **Rama:** `feature/frontend-auditoria`

## Objetivo

Darle a gerencia la pantalla del **registro general de auditoría, filtrable**, para investigar "quién
cambió qué y cuándo" (HU-007, criterio 1). Consume el endpoint ya mergeado
`GET /api/auditoria/registros/`. Como gerencia **arranca sabiendo a quién sospecha**, el filtro por
**usuario** va primero.

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **Filtro por persona primero:** un desplegable de **Usuario**. Como no existe un endpoint de
   usuarios (HU-005 no está hecho), se agrega uno chico en `auditoria` que devuelve **los usuarios que
   aparecen en la auditoría** (`GET /api/auditoria/usuarios/` → `[{id, nombre}]`, solo Gerencia). Así
   el desplegable muestra solo a quienes efectivamente hicieron cambios.
2. **Filtros:** Usuario (desplegable), rango **Desde/Hasta** (`input type="date"`, por defecto los
   últimos 30 días) y **Entidad** (desplegable; hoy solo "Reserva", queda abierto para cuando se
   auditen campaña/tarifa/config). Al cambiar cualquiera, se vuelve a pedir.
3. **Tabla** (solo lectura): `Momento` (fecha y hora local), `Usuario`, `Entidad` ("Reserva #5"),
   `Campo`, `Valor anterior`, `Valor nuevo`. Del más nuevo al más viejo (ya lo ordena el backend).
   Estados de carga/vacío/error.
4. **Navegación:** una sección nueva **"Administración"** en la barra con el ítem **"Auditoría"**,
   `soloGerencia: true` (se oculta a quien no es Gerencia), igual que el reporte de Ingresos.
5. **Sin exportación** en esta pantalla (no lo pide HU-007; el foco es investigar en pantalla).
6. **Sin paginación** (no hay paginación global en el proyecto); los filtros acotan el volumen. Si más
   adelante el registro crece mucho, se agrega paginación en una unidad aparte.

## Cambios

- **Backend** (`backend/apps/auditoria/`): endpoint `GET /api/auditoria/usuarios/` (solo Gerencia) que
  devuelve los usuarios distintos presentes en `RegistroAuditoria` (`[{id, nombre}]`, ordenados por
  nombre). Se puede implementar como una acción del viewset o una vista aparte.
- **Frontend** (`frontend/src/features/auditoria/`):
  - `Auditoria.tsx`: la pantalla (filtros + tabla).
  - `types.ts`: tipos `RegistroAuditoria`, `UsuarioAuditoria`.
  - `Auditoria.test.tsx`: tests con `fetch` mockeado.
  - `App.tsx`: sección "Administración" con el ítem "Auditoría" (`soloGerencia`).

## Reglas

Ninguna nueva. Es la cara visible de HU-007; el backend ya garantiza la inmutabilidad y el permiso.

## Migraciones

Ninguna.

## Cómo se prueba

- Backend (`backend/tests/test_auditoria.py`, se agregan casos): `GET /api/auditoria/usuarios/`
  devuelve los usuarios que hicieron cambios (sin duplicados); Gerencia 200, Operativo 403, anónimo
  401/403.
- Frontend (`Auditoria.test.tsx`, Vitest, `fetch` mockeado para `/auditoria/registros/` y
  `/auditoria/usuarios/`):
  - muestra las filas con momento, usuario, entidad, campo y valores;
  - elegir un usuario vuelve a pedir el registro con `usuario=<id>`;
  - cambiar el rango de fechas vuelve a pedir con `desde`/`hasta`;
  - estado vacío cuando no hay registros; el ítem "Auditoría" aparece solo para Gerencia.
- Verificación completa de backend y frontend (DoD).

## Registro de gates

- Gate 1 (plan): 2026-10-22 — aprobado (filtro por usuario primero; sección "Administración"; default
  últimos 30 días). Implementación por subagente en Sonnet; revisión en Opus.
- Gate 2 (verificación): 2026-10-22 — Backend: `ruff`, `mypy` (98), `makemigrations --check`, gitleaks
  y `pytest --cov` 299 pasan. Frontend: `format:check`, `lint`, `typecheck`, `test:coverage` 113 pasan
  (líneas 89.47 %) y `build` OK. En revisión se corrigió el default de fechas para usar hora local
  (es-AR, UTC-3) en vez de UTC.
- Gate 3 (PR): —
