# Unidad: Expiración de sesión por inactividad

- **Estado:** mergeada · **Épica:** E1 Seguridad y acceso · **App dueña:** `usuarios`/`config` (+ `frontend`)
- **Origen:** HU-003 criterio 4 · **Rama:** `feature/usuarios-sesion-inactividad`

## Objetivo

Que una **sesión abandonada en una compu compartida se cierre sola** tras un rato de inactividad, y que
la próxima acción **mande a ingresar de nuevo** (HU-003, criterio 4). Es la preocupación principal del
equipo. El bloqueo por intentos fallidos (criterio 3) queda para una unidad siguiente.

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **Expiración por inactividad con lo nativo de Django:** `SESSION_SAVE_EVERY_REQUEST = True` (cada
   request renueva el vencimiento → es un timeout *deslizante* por inactividad) + `SESSION_COOKIE_AGE`
   configurable por variable de entorno, **por defecto 30 minutos**. Tras ese tiempo sin actividad, la
   sesión del servidor vence y el usuario queda deslogueado.
2. **Inactividad, no cierre de navegador:** no se usa `SESSION_EXPIRE_AT_BROWSER_CLOSE` (desloguearía
   al cerrar cada pestaña, molesto). El caso "la dejaron abierta y se fueron" lo cubre el timeout por
   inactividad.
3. **El frontend reacciona al 401:** cuando cualquier llamada a la API devuelve 401 (sesión vencida),
   la app vuelve a la pantalla de **ingreso** con el mensaje *"Tu sesión expiró por inactividad.
   Ingresá de nuevo."*. Hoy solo el chequeo inicial de `/me/` detecta el 401; con esto, una sesión
   vencida rebota a login en la **próxima acción**, no deja errores sueltos por pantalla.
4. **Configurable:** la duración vive en `SESSION_COOKIE_AGE` (env `DJANGO_SESSION_IDLE_MINUTES` →
   segundos), como los otros parámetros provisorios.

## Cambios

- `backend/config/settings.py`: `SESSION_SAVE_EVERY_REQUEST = True` y
  `SESSION_COOKIE_AGE = int(os.environ.get("DJANGO_SESSION_IDLE_MINUTES", "30")) * 60`.
- `backend/.env.example`: documentar `DJANGO_SESSION_IDLE_MINUTES`.
- `frontend/src/shared/api.ts`: al recibir 401, avisar (p. ej. `window.dispatchEvent` de un evento
  `sesion-expirada`) además de lanzar el `ApiError` como ahora.
- `frontend/src/App.tsx`: escuchar ese evento y pasar la sesión a `anonymous` con un flag de
  "expiró"; `Login` muestra el mensaje cuando el flag está.
- `frontend/src/app/Login.tsx`: aceptar y mostrar el mensaje de sesión expirada.

## Reglas

Ninguna del catálogo. Implementa el criterio 4 de HU-003. El criterio 2 (mensaje genérico que no
revela si el usuario existe) ya está. El criterio 3 (bloqueo por intentos) es una unidad aparte.

## Migraciones

Ninguna.

## Cómo se prueba

- Backend (`backend/tests/test_settings.py` o `test_auth.py`): `SESSION_SAVE_EVERY_REQUEST` es `True` y
  `SESSION_COOKIE_AGE` es 1800 por defecto (y respeta `DJANGO_SESSION_IDLE_MINUTES` si se setea).
- Frontend:
  - cuando una llamada a la API devuelve 401 estando la app abierta, se vuelve a la pantalla de ingreso
    con el mensaje de sesión expirada;
  - `Login` muestra el mensaje de expiración cuando corresponde.
- Verificación completa de backend y frontend (DoD).

## Registro de gates

- Gate 1 (plan): 2026-10-22 — aprobado (inactividad 30 min configurable; cualquier 401 no-auth vuelve a
  login). Implementación por subagente en Sonnet; revisión en Opus.
- Gate 2 (verificación): 2026-10-22 — Backend: `ruff`, `mypy` (98), `makemigrations --check`, gitleaks
  y `pytest --cov` 305 pasan (94.90 %). Frontend: `format:check`, `lint`, `typecheck`, `test:coverage`
  119 pasan y `build` OK. Revisión: el 401 se excluye para `/api/auth/*`, así que un login con
  contraseña incorrecta no dispara el mensaje de sesión expirada; sin ajustes.
- Gate 3 (PR): 2026-10-22 — PR #55 mergeado a `develop` (rama `feature/usuarios-sesion-inactividad`).
