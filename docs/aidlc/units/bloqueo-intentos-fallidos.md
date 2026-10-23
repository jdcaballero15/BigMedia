# Unidad: Bloqueo temporal por intentos fallidos

- **Estado:** mergeada · **Épica:** E1 Seguridad y acceso · **App dueña:** `usuarios` (+ `config`, `frontend`)
- **Origen:** HU-003 criterio 3 · **Rama:** `feature/usuarios-bloqueo-intentos-fallidos`

## Objetivo

Que **adivinar una contraseña probando muchas** no sirva: tras varios intentos fallidos seguidos, la
cuenta queda **bloqueada un rato** y ni siquiera la contraseña correcta entra hasta que vence
(HU-003, criterio 3). El mensaje sigue sin revelar si el usuario existe (criterio 2).

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **Código propio en `usuarios`, sin `django-axes`.** Lo que se necesita es chico (contar, bloquear,
   reiniciar) y `axes` suma una dependencia con middleware, varias tablas y su propia configuración,
   que es más superficie que la regla. Si más adelante se pide bloqueo por IP o un panel de bloqueos,
   se revisa.
2. **Se guarda en PostgreSQL, no en la caché.** No hay caché compartida configurada (la de Django por
   defecto vive en la memoria de cada proceso), así que con más de un worker de gunicorn o un reinicio
   el contador se perdería o se repartiría. Un modelo `IntentoIngreso` en `usuarios`:
   `username` (normalizado a minúsculas, único), `fallidos_seguidos`, `bloqueado_hasta` (con zona).
3. **Se cuenta por nombre de usuario, exista o no.** Un nombre inexistente también se bloquea, así
   que el bloqueo no sirve para averiguar qué cuentas existen. No se guarda la IP: no hace falta para
   el criterio y evita guardar datos personales.
4. **Valores:** **5 intentos fallidos seguidos → 15 minutos de bloqueo**. Configurables por entorno
   (`DJANGO_LOGIN_MAX_INTENTOS`, `DJANGO_LOGIN_BLOQUEO_MINUTOS`) como la inactividad de sesión, hasta
   que exista HU-001. Un ingreso correcto reinicia el contador; al vencer el bloqueo se arranca de cero.
5. **Cubre la API y el admin de Django.** Se implementa como un *backend* de autenticación
   (`apps/usuarios/backends.py`, subclase de `ModelBackend`) que reemplaza al de Django en
   `AUTHENTICATION_BACKENDS`. Si la cuenta está bloqueada, rechaza sin mirar la contraseña; si falla,
   suma; si entra, reinicia. Así `/admin/` no queda como puerta trasera.
6. **Respuesta del login bloqueado:** `429` con *"Demasiados intentos fallidos. Probá de nuevo en unos
   minutos."*. Se da igual para usuarios existentes e inexistentes, así que no revela nada. El
   frontend ya muestra el `detail` que manda el servidor; solo se verifica con un test.
7. **Sin auditoría del bloqueo en esta unidad:** `auditoria` registra cambios de campos de entidades
   de negocio, y un intento de ingreso no lo es. Se registra con `logging` (nivel `WARNING`, solo el
   id de `IntentoIngreso`, no el nombre de usuario, por la regla 6) para poder diagnosticar.
8. **Sin desbloqueo manual desde una pantalla:** el administrador puede borrar o editar la fila desde
   el admin de Django (se registra `IntentoIngreso` en el admin, solo para eso).

## Cambios

- `backend/apps/usuarios/models.py` (nuevo): modelo `IntentoIngreso`.
- `backend/apps/usuarios/services.py` (nuevo): `esta_bloqueado(username)`, `registrar_fallo(username)`
  y `registrar_exito(username)`, con `select_for_update()` dentro de `transaction.atomic()` para que
  dos intentos simultáneos no pierdan un fallo.
- `backend/apps/usuarios/backends.py` (nuevo): `BackendConBloqueo(ModelBackend)`. También
  `aauthenticate`, que en `ModelBackend` tiene su propia versión async y salteaba el bloqueo: se
  delega en la sync (agregado en la implementación).
- `backend/apps/usuarios/admin.py` (nuevo): registro de `IntentoIngreso` en el admin.
- `backend/config/settings.py`: `AUTHENTICATION_BACKENDS`, `LOGIN_MAX_INTENTOS` y
  `LOGIN_BLOQUEO_MINUTOS` leídos del entorno.
- `backend/config/auth_views.py`: si el usuario está bloqueado, responde `429` con el mensaje genérico.
- `backend/.env.example`: documentar las dos variables nuevas.
- `frontend/src/app/Login.test.tsx`: test de que se muestra el mensaje del `429`. Si `Login.tsx` no
  muestra el `detail` de un `429`, ajuste mínimo ahí.

## Migraciones

Una: `usuarios/0001_intentoingreso` (tabla nueva, no mueve datos). Revisada a mano: solo crea
`IntentoIngreso` con `username` único.

## Reglas provisorias que se usan

Ninguna del catálogo. Los valores 5 intentos / 15 minutos son decisión de esta unidad y quedan
configurables por entorno.

## Cómo se prueba

En `backend/tests/test_auth.py` (y `test_settings.py` para los valores por defecto), siempre contra
PostgreSQL:

- `test_login_quinto_fallo_seguido_bloquea_la_cuenta`
- `test_login_bloqueado_rechaza_la_contrasenia_correcta_con_429`
- `test_login_bloqueado_usuario_inexistente_responde_igual_que_existente`
- `test_login_correcto_reinicia_el_contador_de_fallos`
- `test_login_bloqueo_vencido_permite_ingresar` (fecha manipulada, sin `sleep`)
- `test_admin_login_respeta_el_bloqueo`
- `test_login_usuario_se_normaliza_sin_distinguir_mayusculas`
- `test_settings_bloqueo_por_defecto_cinco_intentos_quince_minutos` (solo los valores por defecto,
  como el test de la inactividad de sesión; que se respeten las variables no se prueba)
- `test_aauthenticate_respeta_el_bloqueo`
- Frontend: `Login` muestra el mensaje del servidor ante un `429`.
- Verificación completa de backend y frontend (Definition of Done).

## Registro de gates

- Gate 1 (plan): 2026-10-23 — aprobado por Gonza tal cual (código propio, PostgreSQL, por nombre de
  usuario, 5 intentos / 15 minutos configurables, cubre el admin, `429` genérico, sin auditoría).
- Gate 2 (verificación): 2026-10-23 — Backend: `ruff format --check` (102 archivos), `ruff check`,
  `mypy` (102, sin errores), `makemigrations --check` sin cambios y `pytest --cov` 315 pasan
  (94.87 %). Frontend: `format:check`, `lint`, `typecheck`, `test:coverage` 120 pasan (líneas 89.45 %,
  sentencias 86.08 %) y `build` OK. `pre-commit run --all-files` con gitleaks pasa. Aprobado por Gonza el mismo día.
- Gate 3 (PR): 2026-10-23 — PR #59 mergeado a `develop` (rama
  `feature/usuarios-bloqueo-intentos-fallidos`).
