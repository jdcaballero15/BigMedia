# Unidad: Ajuste de entornos — producción paga en Render y base de staging en Neon

- **Estado:** en curso · **Épica:** — (unidad técnica) · **App dueña:** `infra`
- **Origen:** decisión de Juan Diego del 21/10/2026 ([ADR-0005](../../adr/0005-base-de-staging-en-neon.md)),
  ajusta la unidad [entornos](entornos.md) ya mergeada · **Rama:** `chore/infra-entornos-neon`

## Objetivo

Dejar en el repo los dos entornos como se decidieron: **producción** en Render con web y PostgreSQL
pagos (con copias de seguridad) y **staging** con la web gratis en Render y la base en **Neon gratis**,
que no vence a los 30 días como la base gratis de Render.

## Cambios

- `render.yaml`:
  - Producción: `bigmedia-web` pasa a `plan: starter` y `bigmedia-db` a `plan: basic-256mb`. Así el
    archivo coincide con lo contratado y una sincronización del Blueprint no intenta volverlos a gratis.
  - Staging: se quita `bigmedia-db-staging`. En `bigmedia-web-staging`, `DATABASE_URL` pasa de
    `fromDatabase` a `sync: false` (secreto que Juan carga en el panel de Render, copiado de Neon).
  - Se actualiza el comentario de cabecera.
- `docs/operacion/despliegue-render.md`: entornos (producción en Render, base de staging en Neon), cómo
  crear el proyecto en Neon (región AWS us-east-1, Virginia, la misma que Render; usar la URL
  **directa**, sin `-pooler`, con `sslmode=require`), los pasos de Juan en orden y cómo ver tablas y
  esquema (Neon: editor SQL del panel; producción: admin de Django o cliente SQL con usuario de solo
  lectura e IP habilitada temporalmente).
- `docs/adr/0005-base-de-staging-en-neon.md` (Propuesto) y su fila en `docs/adr/README.md`.
- `docs/aidlc/roadmap.md`: la próxima unidad de entornos menciona Neon para staging.
- `backend/tests/test_render_blueprint.py` (agregado el 21/10/2026 con aprobación de Juan Diego, al
  fallar en el Gate 2): el test del plan gratis pasa a exigir los planes pagos de producción, y uno
  nuevo controla que staging lea la URL de Neon como secreto y que quede una sola base en el archivo.
- Sin cambios de código de aplicación: `settings.py` ya lee `DATABASE_URL` con `dj-database-url`, que
  acepta la URL de Neon con sus parámetros SSL.

## Migraciones

Ninguna nueva. La base de staging en Neon arranca vacía: `arrancar.sh` corre `migrate` y
`cargar_datos_ejemplo` al iniciar, igual que con la base de Render.

## Reglas provisorias que se usan

Ninguna. Regla 2 y 3 de `CLAUDE.md`: la URL de Neon (con contraseña) nunca va a Git; solo al panel
de Render.

## Pasos de Juan (fuera del repo, en orden)

1. **Render, producción:** pasar `bigmedia-db` a Basic-256mb y `bigmedia-web` a Starter (antes del
   17/11/2026). Confirmar precio en el panel.
2. **Neon:** crear cuenta y proyecto `bigmedia-staging` (Postgres 17, AWS us-east-1); copiar la
   connection string directa.
3. Mergear este PR y el release `develop` → `main`.
4. **Render, Blueprint:** sincronizar. Crea `bigmedia-web-staging` y pide `DATABASE_URL` (la de Neon) y
   `DJANGO_SUPERUSER_*` de staging.
5. Verificar staging: `/api/health/` responde `{"status":"ok"}` y aparecen los datos de ejemplo.

## Cómo se prueba

- `render.yaml` válido: se parsea como YAML y tiene tres recursos (dos web y una base), con producción
  en planes pagos y staging sin `fromDatabase`.
- Verificación completa (DoD): `ruff`, `mypy`, `makemigrations --check`, `pytest --cov`, frontend y
  pre-commit (incluye gitleaks) en verde, aunque no cambie código.
- Manual, después del release: staging levanta contra Neon con datos de ejemplo; producción sigue
  respondiendo en plan pago.

## Registro de gates

- Gate 1 (plan): 2026-10-21 — aprobado por Juan Diego (producción en Render pago, base de staging en
  Neon gratis).
- Gate 2 (verificación): 2026-10-21 — `render.yaml` se parsea con una base (`bigmedia-db`,
  basic-256mb), producción `starter` con `fromDatabase` y staging `free` en `develop` con
  `DATABASE_URL` `sync: false`. `ruff format --check`, `ruff check`, `mypy backend` (89 archivos) y
  `makemigrations --check` sin cambios; `pytest --cov` 264 pasan, cobertura 94,58 % (umbral 80 %).
  Primera corrida: 1 falla en `test_render_blueprint.py` (exigía plan gratis), corregido con
  aprobación. Frontend: `format:check`, `lint`, `typecheck`, `build` OK; `test:coverage` 96 tests,
  líneas 89,34 %, sentencias 86,13 %. `pre-commit run --all-files` (incluye gitleaks) en verde.
- Gate 3 (PR): pendiente
