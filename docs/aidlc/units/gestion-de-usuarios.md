# Unidad: Gestión de usuarios

- **Estado:** en curso · **Épica:** E1 Seguridad y acceso · **App dueña:** `usuarios` (+ `config`, `frontend`)
- **Origen:** HU-005 (RN-021) · **Rama:** `feature/usuarios-gestion-de-usuarios`

## Objetivo

Que el administrador cree, edite e inactive usuarios y les restablezca la contraseña desde la
aplicación, sin pasar por el admin de Django. El servidor garantiza que siempre quede al menos un
administrador activo (HU-005, criterios 1 a 3).

## Punto de partida

- El rol se deriva y no se guarda: Administrador es el superusuario, Operativo es el grupo
  `Operativo` y Lectura es cualquier otro usuario. Gerencia es un grupo aparte que se suma
  (`roles-y-permisos`). `SoloAdministrador` ya existe en `config/permisos.py`, pero ningún endpoint
  la usa.
- **Usuario inactivo:** el `ModelBackend` de Django ya rechaza `is_active=False`, tanto en el login
  como en una sesión abierta (desde la próxima petición). Falta probarlo con un test.
- **Conservación de los registros pasados:** `RegistroAuditoria.usuario` es `on_delete=PROTECT`, así
  que la base no deja borrar a un usuario con actividad.
- No hay mail configurado. El SPA se sirve solo en `/` y no tiene router.

## Decisiones (respondidas por Gonza el 23/10/2026)

1. **Contraseña por link de un solo uso.** El admin genera el link y lo copia para mandarlo a mano
   (WhatsApp o mail). Se usa el `default_token_generator` de Django: el token se invalida cuando
   cambia la contraseña o el último ingreso, y vence a los `PASSWORD_RESET_TIMEOUT` segundos (lo
   configura `DJANGO_LINK_CLAVE_HORAS`, 72 h por defecto). El mismo mecanismo sirve para restablecer:
   generar un link nuevo deja inutilizable la contraseña anterior (`set_unusable_password`). El usuario
   nuevo se crea sin contraseña usable. Sin variables de mail.
2. **Se ingresa con nombre de usuario,** como hoy. El correo, el nombre y el apellido son datos del
   usuario. El login y el bloqueo por intentos no cambian.
3. **Se auditan los cambios** de rol, Gerencia, activo, correo, nombre y apellido, con
   `registrar_cambios` y entidad `usuario`. El alta queda registrada como cambio desde vacío. La
   contraseña y el token no se auditan.

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

4. **No hay borrado desde la API** (HU-006 y la regla de baja lógica): se inactiva. Si hace falta
   corregir una carga errónea, se borra desde el admin de Django, y el `PROTECT` frena el borrado si
   el usuario tiene actividad.
5. **Último administrador activo.** `services.py` bloquea con `select_for_update` a los
   superusuarios activos antes de inactivar a uno o de bajarle el rol, y rechaza la operación si no
   queda otro. Así dos admins que se inactivan a la vez no dejan el sistema sin administrador. Un
   admin sí puede editar sus propios datos.
6. **Asignar el rol** desde la pantalla equivale a lo que hoy se hace en el admin de Django:
   Administrador marca `is_superuser` e `is_staff`; Operativo agrega el grupo `Operativo`; Lectura
   saca las dos cosas. Gerencia es una casilla aparte.
7. **Pantalla para definir la contraseña:** el link es `/?definir-clave=<uid>&token=<token>`. `App.tsx`
   lo detecta antes de pedir la sesión y muestra un formulario de contraseña y su repetición, validado
   con `AUTH_PASSWORD_VALIDATORS`. Si sale bien, lleva al login.
8. **Límite conocido:** el admin de Django no pasa por el servicio, así que un superusuario podría
   inactivar al último administrador desde ahí. Se acepta porque es el mismo superusuario y además
   existe `asegurar_admin`. No se agrega ninguna protección en el admin.

## Cambios

- `backend/apps/usuarios/services.py`: `crear_usuario`, `actualizar_usuario` (datos, rol, Gerencia y
  activo), `generar_link_clave` y `definir_clave`, con el invariante del último admin y la auditoría.
  Lanza `ValidationError` con mensajes en español.
- `backend/apps/usuarios/serializers.py`, `views.py` y `urls.py` (nuevos):
  - `GET/POST /api/usuarios/usuarios/` y `GET/PATCH /api/usuarios/usuarios/<id>/` (la ruta sigue
    la convención `/api/<app>/<recurso>/`), con `SoloAdministrador` y sin `DELETE`.
  - `POST /api/usuarios/usuarios/<id>/link-clave/`, que devuelve la URL.
  - `POST /api/usuarios/definir-clave/`, público, con uid, token y contraseña.
- `backend/config/urls.py`: `api/usuarios/`.
- `backend/config/settings.py` y `backend/.env.example`: `PASSWORD_RESET_TIMEOUT` desde
  `DJANGO_LINK_CLAVE_HORAS`.
- `frontend/src/features/usuarios/` (nuevo):
  - `UsuariosPage`: lista con rol, Gerencia y estado.
  - `UsuarioForm`: alta y edición.
  - Botón "Generar link de contraseña" que muestra el link y ofrece copiarlo.
  - `DefinirClave`: la pantalla pública del link.
- `frontend/src/App.tsx`: ítem "Usuarios" en la navegación, visible solo para el rol Administrador,
  y la ruta del link `definir-clave`.
- `frontend/src/features/auditoria/Auditoria.tsx`: la entidad `usuario` en el filtro y en las etiquetas.

## Migraciones

Ninguna: se usan `User`, `Group` y los grupos que ya existen.

## Reglas provisorias que se usan

RN-021 (quién más usa el sistema) sigue `pendiente`. No bloquea esta unidad: la pantalla sirve para
cualquier cantidad de usuarios, y cuando Seba responda se cargan desde ahí.

## Cómo se prueba

Backend, contra PostgreSQL:

- `test_crear_usuario_sin_clave_usable_y_rol_asignado` (criterio 1)
- `test_link_clave_valido_define_clave_y_queda_usado` y `test_link_clave_vencido_o_reusado_rechaza`
- `test_restablecer_clave_invalida_la_anterior`
- `test_usuario_inactivo_login_rechazado_y_auditoria_conservada` (criterio 2)
- `test_usuario_inactivado_sesion_abierta_pierde_acceso`
- `test_unico_admin_inactivar_o_cambiar_rol_rechaza` (criterio 3)
- `test_dos_admins_inactivacion_concurrente_deja_uno_activo`, con hilos y `transaction=True`
- `test_no_admin_endpoints_usuarios_responde_403` (Operativo, Lectura y Gerencia) y
  `test_api_usuarios_no_permite_delete`
- `test_cambio_de_rol_queda_auditado_sin_clave`

Frontend, con Vitest:

- La lista, el alta y la edición.
- El ítem de navegación oculto para quien no es administrador.
- El link generado se muestra.
- `DefinirClave` muestra los errores del servidor y, si sale bien, lleva al login.

## Registro de gates

- Gate 1 (plan): 2026-10-23 — aprobado por Gonza
- Gate 2 (verificación): 2026-10-23 — `ruff format --check` (108 archivos formateados) y
  `ruff check` sin errores; `mypy backend` sin errores en 108 archivos; `makemigrations --check`
  sin cambios; `pytest --cov` con 388 tests aprobados, ninguno salteado y 95,53 % de coverage.
  Frontend: `format:check`, `lint` y `typecheck` en verde; `test:coverage` con 159 tests en 28
  archivos (87,23 % de sentencias y 90,38 % de líneas); `build` OK, con el aviso de tamaño de
  chunk que ya existía. `pre-commit run --all-files` en verde, gitleaks incluido. Pendiente de
  revisión por Gonza o Juan Diego.
- Gate 3 (PR): pendiente
