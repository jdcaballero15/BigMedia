# Unidad: Permiso de ingresos (grupo Gerencia)

- **Estado:** mergeada · **Épica:** E1 Seguridad y acceso · **App dueña:** `usuarios` (+ `facturacion`, `frontend`)
- **Origen:** HU-052 criterio 2 (destraba el gate de facturación) · **Rama:** `feature/usuarios-permiso-ingresos`

## Objetivo

Que los **números de facturación/ingresos** los vean solo quienes tienen que verlos. Seba y Ale son
**gerentes**; el tercer trabajador es operativo y **no** ve ingresos. Se introduce el grupo **Gerencia**
y se cierra el reporte de ingresos (HU-049) a ese grupo, lo que cumple el criterio 2 de HU-052 (un
usuario sin permiso no puede ver —ni exportar— los ingresos).

## Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **Grupo `Gerencia`**, aditivo al `Operativo` que ya existe (un gerente puede estar en los dos). Se
   crea vacío por migración; **las personas se asignan desde el admin** (como el Operativo), así no hay
   datos reales en el código.
2. **Qué se cierra:** solo el endpoint de **ingresos** (`GET /api/facturacion/ingresos/`), que es dato
   de facturación. La **ocupación no es facturación** y queda abierta como está. La exportación CSV es
   cliente-side sobre esos datos: al cerrar el endpoint, un usuario sin permiso no puede exportarlos
   (criterio 2 de HU-052, sin tocar el front de export).
3. **Permiso por pertenencia al grupo** (como el Operativo, por nombre): nueva clase
   `LecturaSoloGerencia` (lectura solo para Gerencia o superusuario).
4. **`/api/auth/me/` y el login** exponen `es_gerencia`, para que el frontend **oculte la pantalla de
   Ingresos** a quien no es Gerencia (si igual llegara al endpoint, da 403).
5. **Migración del grupo en `facturacion`:** la app no tiene modelos, pero sí puede tener una migración
   de datos (`0001_grupo_gerencia`) que crea el grupo; es la app dueña del dato de ingresos.

## Cambios

- `backend/apps/facturacion/migrations/0001_grupo_gerencia.py` (+ `__init__.py`): crea el grupo
  `Gerencia` (idempotente).
- `backend/config/permisos.py`: `GRUPO_GERENCIA = "Gerencia"` y clase `LecturaSoloGerencia`.
- `backend/apps/facturacion/views.py`: `IngresosView` pasa a exigir `LecturaSoloGerencia`.
- `backend/config/auth_views.py`: `me` y `login_view` devuelven `es_gerencia`.
- `frontend/src/app/Login.tsx` y `frontend/src/App.tsx`: se pasa `es_gerencia` y se **oculta el ítem
  "Ingresos"** de la barra cuando el usuario no es Gerencia.
- Tests: fixture `gerencia_client` en `conftest.py`; se actualizan los tests de ingresos para usarlo y
  se agrega que un usuario sin Gerencia recibe 403; `/me/` devuelve `es_gerencia`.

## Reglas

Ninguna del catálogo RN. Es seguridad de acceso (E1) que satisface el criterio 2 de HU-052.

## Migraciones

- `facturacion/0001_grupo_gerencia` (datos): crea el grupo `Gerencia`. `makemigrations --check` debe
  quedar limpio.

## Cómo se prueba

- Backend (`backend/tests/`, PostgreSQL real):
  - un usuario Gerencia (y un superusuario) **puede** leer `/api/facturacion/ingresos/` (200).
  - un usuario Operativo o sin grupos **no puede** (403); anónimo 401/403 (criterio 2 de HU-052).
  - `/api/auth/me/` devuelve `es_gerencia` verdadero para Gerencia y falso para el resto.
  - la migración crea el grupo `Gerencia`.
- Frontend: el ítem "Ingresos" **no aparece** en la barra para un usuario que no es Gerencia y **sí**
  para uno que lo es.
- Verificación completa de backend y frontend (DoD).

## Registro de gates

- Gate 1 (plan): 2026-10-21 — aprobado (Gerencia = Seba y Ale; solo ingresos se cierra; aditivo a
  Operativo).
- Gate 2 (verificación): 2026-10-21 — Backend: `ruff`, `mypy` (89 archivos), `makemigrations --check`,
  gitleaks y `pytest --cov` 263 pasan (cobertura 94.58 %). Frontend: `format:check`, `lint`,
  `typecheck`, `test:coverage` 96 pasan (líneas 89 %, sentencias 86 %) y `build` en verde.
- Gate 3 (PR): 2026-10-21 — PR #40 mergeado a `develop` (rama `feature/usuarios-permiso-ingresos`).
  Juan asigna a Seba y Ale al grupo Gerencia desde el admin.
