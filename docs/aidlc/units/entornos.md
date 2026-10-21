# Unidad: Entornos — producción paga y staging gratis

- **Estado:** mergeada · **Épica:** — (unidad técnica) · **App dueña:** `infra`
- **Origen:** roadmap (decisión de Juan Diego, antes del 17/11/2026) · **Rama:** `feature/infra-entornos`

## Objetivo

Separar **producción** (paga, en `main`, con copias de seguridad) de un **staging gratis** conectado a
`develop` que Seba y Ale usan para probar lo nuevo antes de producción y para demos. El staging arranca
con datos de ejemplo (nunca datos reales). Motivo con fecha: la base gratis actual **vence el
17/11/2026** y, en el plan gratis, además se recrea cada 30 días.

## Qué hace esta unidad (código/config) y qué queda para Juan

Esta unidad entrega **solo lo que vive en el repo** (config, un comando y docs). La provisión real en
Render y el gasto los ejecuta Juan (ver "Pasos de Juan").

### Decisiones de diseño (mi criterio — corregir acá si hace falta)

1. **Dos entornos por `DJANGO_ENV`:** `production` y `staging`. Ambos son entornos desplegados
   (endurecidos: `DEBUG` off, HTTPS, `ALLOWED_HOSTS` por `RENDER_EXTERNAL_HOSTNAME`). Se agrega en
   `settings.py` una bandera `STAGING` y una `DESPLEGADO = PRODUCTION or STAGING`; los bloques de
   seguridad que hoy dependen de `PRODUCTION` pasan a depender de `DESPLEGADO`, para que staging quede
   igual de endurecido que producción.
2. **Datos de ejemplo solo en staging:** un management command `cargar_datos_ejemplo`, idempotente,
   que crea carteles, clientes, marcas, campañas y reservas de muestra (nunca datos reales). Se niega a
   correr si `PRODUCTION` (nunca en producción). Corre en el arranque **solo** cuando
   `DJANGO_ENV=staging` (en `backend/arrancar.sh`).
3. **Dónde vive el comando:** en `apps/usuarios/management/commands/` junto a `asegurar_admin`, tratado
   como **tooling de bootstrap** (como los tests, importa modelos de varias apps). Se deja la nota para
   la revisión del PR, porque ninguna app de negocio podría importar `inventario` + `clientes` +
   `campanias` + `reservas` a la vez; acá es tooling, no lógica de negocio.
4. **`render.yaml`:** se agrega un segundo servicio web y una segunda base para **staging**
   (`plan: free`, `branch: develop`, `DJANGO_ENV=staging`), y se deja **producción** apuntando a un
   plan **pago** (web + PostgreSQL) con un comentario para que Juan confirme el tier. Los backups de la
   base paga de Render son automáticos; se documenta.
5. **Nunca datos personales reales** (regla 6): el comando solo genera datos inventados.

## Cambios

- `backend/config/settings.py`: banderas `STAGING` y `DESPLEGADO`; los gates de seguridad pasan de
  `PRODUCTION` a `DESPLEGADO`.
- `backend/apps/usuarios/management/commands/cargar_datos_ejemplo.py`: comando idempotente con guarda
  anti-producción.
- `backend/arrancar.sh`: tras `migrate` y `asegurar_admin`, si `DJANGO_ENV=staging`, corre
  `cargar_datos_ejemplo`.
- `render.yaml`: servicio + base de staging (free, `develop`); producción a plan pago (comentado para
  que Juan confirme el tier).
- `docs/operacion/despliegue-render.md`: sección de entornos (producción vs staging) y los pasos de
  Juan.

## Pasos de Juan (infra, fuera de lo que puedo ejecutar)

- Pasar la web y la base de **producción** al plan **pago** elegido y activar las **copias de
  seguridad**.
- Crear el **Blueprint de staging** en Render (servicio + base gratis en `develop`) y cargar sus
  **secretos** (`DJANGO_SUPERUSER_*`).
- Recordar que la base gratis de staging **vence a los 30 días**: recrearla y dejar que el arranque
  vuelva a cargar los datos de ejemplo.

## Reglas que se usan

- **Regla 6** (ningún dato personal real): el comando solo genera datos de ejemplo inventados; test que
  lo verifica.
- **Regla 8** (estructura): no se crean carpetas nuevas en la raíz; `render.yaml` y los settings ya
  existen.

## Migraciones

Ninguna.

## Cómo se prueba

- Backend (`backend/tests/`):
  - `cargar_datos_ejemplo` crea datos y, corrido dos veces, no duplica (idempotente).
  - el comando **se niega a correr** cuando el entorno es `production` (guarda anti-producción).
  - en `test_production_settings.py` / `test_settings.py`: con `DJANGO_ENV=staging`, las protecciones
    de seguridad quedan activas (igual que producción) y `DEBUG` es `False`.
- Verificación completa del backend (DoD) y `render.yaml` válido (revisión del PR; Render lo valida al
  sincronizar el Blueprint).

## Registro de gates

- Gate 1 (plan): 2026-10-21 — aprobado (upgrade a pago lo hace Juan a mano; comando como tooling en
  `usuarios`).
- Gate 2 (verificación): 2026-10-21 — `ruff format --check`, `ruff check`, `mypy backend` (89
  archivos), `makemigrations --check` y gitleaks en verde; `pytest --cov` 261 pasan (7 nuevos),
  cobertura total 95 % (umbral 80 %). `render.yaml` válido (dos entornos). Frontend no aplica (sin
  cambios de frontend).
- Gate 3 (PR): 2026-10-21 — PR #38 mergeado a `develop` (rama `feature/infra-entornos`). Los pasos de
  infra de Render quedan para Juan.
