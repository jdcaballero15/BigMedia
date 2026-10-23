# Unidad: Roles y permisos

- **Estado:** en revisión · **Épica:** E1 Seguridad y acceso · **App dueña:** `usuarios` (+ `config`, `frontend`)
- **Origen:** HU-004 · **Rama:** `feature/usuarios-roles-y-permisos`

## Objetivo

Que cada usuario tenga un rol claro (**Operativo**, **Administrador** o **Lectura**) y que el servidor
rechace lo que su rol no permite (HU-004, criterios 1 a 3). La pantalla deja de ofrecer acciones de
edición a quien no puede editar, pero la regla vive en el servidor.

## Punto de partida

- `config/permisos.py` ya tiene `LecturaConSesionEdicionOperativo` en todas las vistas de negocio
  (inventario, clientes, campañas, reservas, costos): lee cualquiera con sesión y edita el grupo
  `Operativo` o un superusuario. Un usuario sin grupos ya es, de hecho, de solo lectura en la API.
- `Gerencia` es un grupo **aditivo** que habilita ingresos y auditoría (decisión de `permiso-ingresos`,
  aprobada el 21/10/2026: Seba y Ale son Gerencia y pueden estar también en Operativo).
- El administrador hoy es el superusuario (`asegurar_admin`); la configuración (HU-001) y la gestión de
  usuarios (HU-005) todavía no tienen API, solo el admin de Django.
- El frontend no oculta ningún botón de edición según el rol.

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **Gerencia sigue siendo aditiva y no es el rol Lectura.** La historia dice «Lectura (Gerencia)»,
   pero eso choca con lo aprobado en `permiso-ingresos`. Se separan: el **rol** dice qué puede
   modificar (Operativo, Administrador, Lectura) y **Gerencia** es un permiso extra para ver ingresos y
   auditoría, que se combina con cualquier rol. Si se confirma, la aclaración de la historia va en un
   PR `docs/historias-roles-y-gerencia` aparte.
2. **El rol se deriva, no se guarda en un campo nuevo.** Administrador = superusuario; Operativo =
   miembro del grupo `Operativo`; Lectura = cualquier otro usuario con sesión. Se crea además el grupo
   `Lectura` vacío por migración solo para que en el admin se vea explícito, sin efecto en los permisos.
   Sin modelo nuevo ni campo en `User`: el criterio 3 (rige desde la próxima petición) se cumple solo,
   porque el rol se lee de la base en cada petición.
3. **Una función única `rol_de(user)`** en `apps/usuarios/services.py` devuelve `"administrador"`,
   `"operativo"` o `"lectura"`. Las clases de `config/permisos.py` la usan, así la regla está en un
   solo lugar.
4. **Nueva clase `SoloAdministrador`** en `config/permisos.py`, para las futuras APIs de configuración
   (HU-001) y usuarios (HU-005). En esta unidad no hay endpoint que la use; se prueba con una vista de
   test. El criterio 1 se cubre hoy con el admin de Django: un Operativo no es `is_staff` y no entra.
5. **`/api/auth/me/` y el login devuelven `rol`** además de `es_gerencia`.
6. **El frontend oculta las acciones de edición para Lectura**: los botones de crear, editar, cancelar
   y confirmar en carteles, catálogos, clientes, marcas, rubros, campañas y reservas. Se hace con un
   contexto de sesión (`puedeEditar`) leído desde `App.tsx`, sin tocar la lógica de cada formulario.
7. **El rol se asigna desde el admin de Django** (grupos y casilla de superusuario), como hoy. La
   pantalla de usuarios es HU-005.

## Cambios

- `backend/apps/usuarios/services.py`: `rol_de(user)` y, para tener la regla en un solo lugar,
  `es_gerencia(user)` y los nombres de grupo (antes en `config/permisos.py` y `auth_views.py`).
- `backend/config/permisos.py`: `LecturaConSesionEdicionOperativo` usa `rol_de`; nueva `SoloAdministrador`.
- `backend/config/auth_views.py`: `rol` en `/me/` y en el login.
- `backend/apps/usuarios/migrations/0002_grupo_lectura.py`: crea el grupo `Lectura` (idempotente).
- `frontend/src/shared/sesion.ts` (nuevo): tipo `Rol`, `PuedeEditarContext` y `usePuedeEditar()`.
- `frontend/src/App.tsx` y `app/Login.tsx`: guardan `rol` en la sesión y lo proveen por contexto.
- `frontend/src/features/…`: `CartelesPage`, `CatalogosPage`, `ClientesPage`, `MarcasPage`,
  `RubrosAdmin`, `CampaniasPage`, `CampaniaDetalle`, `ReservasCampania` y `CostosReserva` ocultan
  crear, editar, inactivar, dar de baja y agregar costo si el rol es Lectura.

## Migraciones

Una de datos: `usuarios/0002_grupo_lectura`, crea el grupo `Lectura` vacío. No mueve datos.

## Reglas provisorias que se usan

RN-021 (quiénes usan el sistema) sigue `pendiente`. No bloquea esta unidad: los roles no dependen de
cuántas personas haya, y la asignación de cada persona se hace desde el admin.

## Cómo se prueba

Backend, contra PostgreSQL:

- `test_rol_superusuario_es_administrador`, `test_rol_grupo_operativo_es_operativo`,
  `test_rol_sin_grupos_es_lectura`, `test_rol_gerencia_sola_es_lectura`.
- `test_lectura_crear_o_editar_por_api_responde_403` (parametrizado sobre carteles, clientes, marcas,
  campañas, reservas y costos; criterio 2).
- `test_operativo_accion_de_administrador_responde_403` (vista de test con `SoloAdministrador`) y
  `test_operativo_no_entra_al_admin_de_django` (criterio 1).
- `test_cambio_de_rol_rige_en_la_proxima_peticion` (misma sesión, se quita el grupo entre dos
  peticiones; criterio 3).
- `test_me_devuelve_rol` y `test_login_devuelve_rol`.
- `test_migracion_crea_grupo_lectura`.

Frontend: un usuario Lectura no ve los botones de crear y editar en cada pantalla; uno Operativo sí.

Verificación completa de backend y frontend (Definition of Done).

## Registro de gates

- Gate 1 (plan): 2026-10-23 — aprobado por Gonza tal cual (Gerencia aditiva y separada del rol
  Lectura, rol derivado sin campo nuevo, grupo `Lectura` vacío, `SoloAdministrador` sin endpoint
  todavía, frontend oculta la edición, RN-021 no bloquea).
- Gate 2 (verificación): 2026-10-23 — Backend: `ruff format --check` (103 archivos), `ruff check`,
  `mypy` (103, sin errores), `makemigrations --check` sin cambios y `pytest --cov` 354 pasan
  (94.84 %). Frontend: `format:check`, `lint`, `typecheck`, `test:coverage` 141 pasan (líneas 89.55 %,
  sentencias 86.2 %) y `build` OK. `pre-commit run --all-files` con gitleaks pasa. Aprobado por
  Gonza el mismo día.
- Gate 3 (PR): _pendiente_
