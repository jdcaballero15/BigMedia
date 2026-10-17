# Unidad: Despliegue en Render

- **Estado:** mergeada · **Épica:** E0 Plataforma base
- **Rama:** `chore/render-deploy` · **Fecha:** 2026-10-17
- **Origen:** migrado desde `docs/superpowers/` el 2026-10-16. El contenido no se modificó, salvo el nivel de los encabezados y los enlaces que dejaron de resolver.

## Diseño

### Objetivo

Publicar el sistema para que Seba y Ale lo usen con datos reales de Big Media, desde una URL HTTPS, con una base PostgreSQL persistente y un proceso de despliegue que respete los Pull Requests. Esta entrega prepara la infraestructura y el procedimiento de puesta en marcha. El módulo de inventario se habilita cuando su PR se integre; campañas y reservas siguen fuera del alcance funcional actual.

### Decisión

Usar un servicio web pago y una base PostgreSQL paga de Render, en la misma región. El servicio web ejecutará Django y servirá la aplicación React compilada desde el mismo origen. Render desplegará la rama `main` después de cada integración aprobada por PR. La primera URL será la asignada por Render; un dominio propio puede añadirse más adelante.

Se eligió esta opción por su operación en un solo proveedor, conexión privada entre la aplicación y la base, TLS administrado y recuperación a un punto anterior de PostgreSQL. La alternativa Render + Neon requiere dos cuentas y una conexión a la base por Internet; puede evaluarse si cambian los requisitos de recuperación o costos. Los planes gratuitos no se usarán para datos reales.

### Arquitectura y flujo

1. El navegador solicita la URL HTTPS de Render. Django devuelve la página React compilada y sus archivos estáticos.
2. React llama a `/api/` en el mismo origen. Django mantiene las sesiones y la protección CSRF existentes; `/admin/` queda disponible sólo para usuarios administrativos.
3. Django accede a PostgreSQL mediante la cadena de conexión privada que entrega Render. La base no se expone públicamente.
4. `/api/health/` comprueba la conexión a la base y permite a Render detectar una instancia que no puede atender solicitudes.
5. El build produce una imagen reproducible con Node para compilar React y Python para ejecutar Django con un servidor WSGI de producción. Los archivos estáticos se reúnen durante el build.

No se crean datos de ejemplo en producción. La carga real comienza después de verificar el despliegue y las cuentas de usuario.

### Configuración y seguridad

- El repositorio contendrá la definición de Render y el código de despliegue, nunca claves, contraseñas ni datos reales.
- `DJANGO_SECRET_KEY` se generará como secreto del servicio. `DATABASE_URL` vendrá de la base administrada. `DJANGO_DEBUG` será falso.
- Django aceptará el host asignado por Render, confiará en el encabezado HTTPS del proxy de Render y usará cookies de sesión y CSRF seguras. La configuración local seguirá funcionando con `.env` y Docker Compose.
- Sólo los usuarios creados por un administrador podrán iniciar sesión. Se crearán cuentas individuales para Seba y Ale y se asignarán sus permisos de inventario. No habrá registro público.
- Se ejecutará `manage.py check --deploy` antes de la puesta en marcha. Se comprobará que las rutas de API y administración sigan protegidas.

### Publicación y migraciones

El PR incorporará la configuración de Render, el empaquetado de React y Django, las variables de entorno necesarias y una guía operativa. El build y las pruebas se ejecutarán antes de integrar el PR. Render construirá la imagen desde `main` y ejecutará las migraciones de Django como paso previo a activar la nueva versión. Si el build o la migración fallan, la nueva versión no se publicará; el error deberá quedar visible en los logs de Render. Los cambios de esquema futuros deberán conservar compatibilidad con la versión anterior durante el cambio de instancia.

La creación del servicio y de la base paga, la conexión de GitHub con Render y la carga de datos reales requieren un paso operativo posterior con acceso a la cuenta de Big Media y autorización del gasto. Ninguna integración del PR creará recursos pagos por sí sola.

### Recuperación y operación

La base PostgreSQL paga de Render ofrece recuperación a un punto anterior. En el plan Hobby, la ventana documentada es de tres días. Antes de cargar datos reales, se confirmará en el panel que la recuperación esté activa y se hará una restauración de prueba en una base separada. La guía operativa incluirá cómo verificar salud, revisar logs, crear usuarios, restaurar y exportar datos antes de una migración de riesgo. Si Big Media necesita una retención mayor a tres días, se definirá almacenamiento adicional de copias antes de usar el sistema como fuente única de datos.

### Verificación y criterios de aceptación

- La imagen se construye desde cero y el frontend compilado carga en la ruta raíz.
- Las pruebas existentes de frontend y backend pasan, incluida la integración con PostgreSQL donde esté disponible.
- `check --deploy` no reporta problemas pendientes de seguridad relevantes para esta configuración.
- En una instalación de prueba, HTTPS responde, `/api/health/` informa conexión a la base, el inicio y cierre de sesión funcionan y una persona sin permiso no puede modificar inventario.
- Las migraciones se ejecutan sin cargar datos ficticios y los datos persisten después de un nuevo despliegue.
- Se verifica una recuperación de PostgreSQL antes de introducir datos reales.

### Fuera de alcance

Esta entrega no implementa reservas, campañas, disponibilidad, reportes, carga masiva de inventario, dominio propio ni correos transaccionales. Tampoco importa datos reales automáticamente.

## Plan ejecutado

## Render Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preparar el monorepo para publicar React, Django y PostgreSQL pago en Render desde `main`, sin crear aún recursos pagos ni cargar datos reales.

**Architecture:** Un único servicio web Docker compila React con Node y ejecuta Django con Gunicorn. Django sirve `/` y archivos estáticos con WhiteNoise, mantiene `/api/` y `/admin/`, y se conecta por la URL interna de una base PostgreSQL administrada por Render. `render.yaml` declara ambos recursos, el chequeo de salud y las migraciones previas al despliegue.

**Tech Stack:** React 19, TypeScript 6, Vite 8, Django 5.2, Django REST Framework, Python 3.12, PostgreSQL 17, Docker, Render.

**Spec:** `docs/superpowers/specs/2026-10-15-render-deploy-design.md`

### Global Constraints

- Todos los cambios entran a `main` mediante Pull Request; no hacer push directo a `main`.
- La producción usa planes pagos para el servicio web y PostgreSQL; la creación de recursos requiere autorización de gasto aparte.
- Nunca incluir secretos, contraseñas, datos reales ni archivos `.env` en Git.
- La configuración local mediante `.env`, Vite y Docker Compose debe seguir funcionando.
- Las cuentas de Seba y Ale se crean por un administrador; no se agrega registro público.
- El PR de inventario debe integrarse antes de verificar sus pantallas en producción.

### File Map

- `backend/config/settings.py`: selección de entorno, conexión a PostgreSQL, proxy HTTPS, cookies y archivos estáticos.
- `backend/config/urls.py`: ruta raíz para el HTML de React; mantiene API y administración.
- `frontend/vite.config.ts`: prefijo `/static/` para recursos compilados; proxy de desarrollo intacto.
- `backend/pyproject.toml`: dependencias de base URL, Gunicorn, WhiteNoise y parser YAML sólo para pruebas.
- `backend/tests/test_production_settings.py`: controles de host, secretos, TLS y conexión de producción.
- `backend/tests/test_spa.py`: respuesta de la ruta raíz y precedencia de API/administración.
- `backend/tests/test_render_blueprint.py`: invariantes de servicio pago, base privada y migraciones.
- `Dockerfile` y `.dockerignore`: construcción de frontend y runtime Python sin archivos locales ni secretos.
- `render.yaml`: definición declarativa de servicio, PostgreSQL, variables y despliegue.
- `docs/operacion/despliegue-render.md`: alta de recursos, usuarios, verificación, recuperación y exportación.
- `README.md`: enlace al procedimiento y estado real del despliegue.

### Review Focus

1. Un host desconocido debe recibir `400`, incluso si envía `X-Forwarded-Proto: https` — prueba en Task 1.
2. Una petición HTTP por el proxy debe redirigirse a HTTPS sin bucle — prueba en Task 1.
3. La app debe rechazar el arranque de producción si falta `DATABASE_URL` — prueba en Task 1.
4. `/api/health/` y `/admin/` no deben quedar ocultos por la ruta de React — prueba en Task 2.
5. El Blueprint no debe aprovisionar planes gratuitos ni exponer PostgreSQL públicamente — prueba en Task 3.

---

#### Task 1: Configuración Django de producción

**Files:**
- Modify: `backend/config/settings.py`
- Modify: `backend/pyproject.toml`
- Create: `backend/tests/test_production_settings.py`

**Interfaces:**
- Consumes: `DJANGO_ENV=production`, `DJANGO_SECRET_KEY`, `DATABASE_URL`, `RENDER_EXTERNAL_HOSTNAME`, y variables locales existentes.
- Produces: `settings.DATABASES`, `ALLOWED_HOSTS`, `SECURE_PROXY_SSL_HEADER`, cookies seguras y configuración de WhiteNoise para Task 2.

- [ ] **Step 1: Escribir pruebas fallidas en `test_production_settings.py`.** Ejecutar un subproceso con el entorno de producción para no contaminar los otros tests. Casos mínimos:

  ```python
  env = {**os.environ, "DJANGO_ENV": "production", "DJANGO_SECRET_KEY": "test-only", "RENDER_EXTERNAL_HOSTNAME": "bigmedia.onrender.com", "DATABASE_URL": "postgresql://u:p@db.internal:5432/bigmedia"}
  result = subprocess.run([sys.executable, "-c", script], cwd=BACKEND_DIR, env=env, capture_output=True, text=True)
  assert result.returncode == 0, result.stderr
  assert json.loads(result.stdout)["db_host"] == "db.internal"
  assert json.loads(result.stdout)["allowed_hosts"] == ["bigmedia.onrender.com"]
  assert json.loads(result.stdout)["secure_cookies"] is True
  ```

  En `script`, serializar `settings.DATABASES["default"]["HOST"]`, `settings.ALLOWED_HOSTS`, ambas cookies, `SECURE_SSL_REDIRECT` y `SECURE_PROXY_SSL_HEADER`. Repetir sin `DATABASE_URL` y exigir salida distinta de cero. En otro subproceso, usar `Client(HTTP_HOST="otro.example")` y exigir 400; con host válido y `HTTP_X_FORWARDED_PROTO="http"`, exigir redirección HTTPS.
- [ ] **Step 2: Ejecutar** `python -m pytest backend/tests/test_production_settings.py -q` **y constatar el fallo por configuración faltante.**
- [ ] **Step 3: Añadir `dj-database-url>=2,<4`, `gunicorn>=23,<25` y `whitenoise>=6,<8` a dependencias.** En `settings.py`, aplicar exactamente estas ramas y conservar la DB local existente:

  ```python
  PRODUCTION = os.environ.get("DJANGO_ENV") == "production"
  STATIC_URL = "/static/"
  STATIC_ROOT = BASE_DIR / "staticfiles"
  if PRODUCTION:
      DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"])}
      ALLOWED_HOSTS = [os.environ["RENDER_EXTERNAL_HOSTNAME"]]
      SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
      SECURE_SSL_REDIRECT = True
      SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
      SECURE_HSTS_SECONDS = 3600
      STORAGES = {"staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
  ```

  Insertar `"whitenoise.middleware.WhiteNoiseMiddleware"` después de `SecurityMiddleware`; si se configura `STORAGES`, incluir también el backend `default` para no romper futuros archivos.
- [ ] **Step 4: Ejecutar** `python -m pytest backend/tests/test_production_settings.py backend/tests/test_health.py -q` **y** `python backend/manage.py check`; **corregir sólo fallos atribuibles al cambio.**
- [ ] **Step 5: Commit:** `git add backend/config/settings.py backend/pyproject.toml backend/tests/test_production_settings.py && git commit -m "feat: configure Django for Render production"`.

#### Task 2: Un único origen para React y Django

**Files:**
- Modify: `frontend/vite.config.ts`
- Modify: `backend/config/settings.py`
- Modify: `backend/config/urls.py`
- Create: `backend/tests/test_spa.py`
- Create: `Dockerfile`
- Create: `.dockerignore`

**Interfaces:**
- Consumes: frontend compilado en `backend/frontend_dist/` dentro de la imagen; configuración estática de Task 1.
- Produces: `GET /` devuelve `frontend_dist/index.html`, `/static/*` sirve recursos compilados y las rutas Django conservan precedencia.

- [ ] **Step 1: Escribir `test_spa.py` con `override_settings(TEMPLATES=...)` y un directorio temporal que contenga `index.html` con texto `BIGMEDIA_SPA`.** Cubrir las rutas:

  ```python
  with override_settings(TEMPLATES=[{**settings.TEMPLATES[0], "DIRS": [temp_dir]}]):
      assert b"BIGMEDIA_SPA" in Client().get("/").content
  with patch("config.health.connection.ensure_connection"):
      assert Client().get("/api/health/").json() == {"status": "ok"}
  assert Client().get("/admin/").status_code == 302
  ```

  Comprobar por separado, tras `npm run build`, que `frontend/dist/index.html` referencia `/static/assets/`.
- [ ] **Step 2: Ejecutar** `python -m pytest backend/tests/test_spa.py -q` **y constatar el 404 en `/`.**
- [ ] **Step 3: En Vite, fijar `base: '/static/'` sólo para el build (`command === 'build'`), manteniendo el proxy local.** En Django, agregar el directorio compilado y la ruta raíz:

  ```typescript
  export default defineConfig(({ command }) => ({
    base: command === 'build' ? '/static/' : '/',
    plugins: [react()],
    server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
    test: { environment: 'jsdom' },
  }))
  ```

  ```python
  FRONTEND_DIST = BASE_DIR / "frontend_dist"
  TEMPLATES[0]["DIRS"] = [FRONTEND_DIST] if FRONTEND_DIST.exists() else []
  STATICFILES_DIRS = [FRONTEND_DIST] if FRONTEND_DIST.exists() else []
  # Al final de urlpatterns: path("", TemplateView.as_view(template_name="index.html"))
  ```
- [ ] **Step 4: Crear Docker multi-stage.** La imagen debe seguir esta estructura; no copiar `.env` ni dar una clave real durante el build:

  ```dockerfile
  FROM node:24-alpine AS frontend
  WORKDIR /app/frontend
  COPY frontend/package*.json ./
  RUN npm ci
  COPY frontend/ ./
  RUN npm run build
  FROM python:3.12-slim
  WORKDIR /app/backend
  COPY backend/ ./
  RUN pip install --no-cache-dir .
  COPY --from=frontend /app/frontend/dist/ ./frontend_dist/
  RUN DJANGO_ENV=production DJANGO_SECRET_KEY=build-only DATABASE_URL=postgresql://build:build@localhost:5432/build RENDER_EXTERNAL_HOSTNAME=build.invalid python manage.py collectstatic --noinput
  EXPOSE 10000
  CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000}"]
  ```

  `.dockerignore` excluye `.git`, `.env*`, `node_modules`, `.venv`, `dist`, `staticfiles`, documentación privada y archivos temporales. Los valores `build-only` y `build.invalid` no son credenciales operativas; sólo permiten generar el manifiesto estático durante el build sin conectar a PostgreSQL.
- [ ] **Step 5: Ejecutar** `npm test`, `npm run lint`, `npm run build` desde `frontend/`; luego `python -m pytest backend/tests/test_spa.py -q` y `docker build -t bigmedia-render .` desde la raíz. Inspeccionar que la imagen no contenga `.env` ni contraseñas y que `collectstatic` haya producido recursos.
- [ ] **Step 6: Commit:** `git add Dockerfile .dockerignore frontend/vite.config.ts backend/config/settings.py backend/config/urls.py backend/tests/test_spa.py && git commit -m "feat: serve React and Django from one production image"`.

#### Task 3: Blueprint de Render y controles de despliegue

**Files:**
- Create: `render.yaml`
- Modify: `backend/pyproject.toml`
- Create: `backend/tests/test_render_blueprint.py`

**Interfaces:**
- Consumes: Dockerfile y variables definidas en Tasks 1–2.
- Produces: servicio `bigmedia-web` y base `bigmedia-db` en la misma región, conectados por `DATABASE_URL` interna.

- [ ] **Step 1: Añadir `PyYAML>=6,<7` sólo a dependencias de desarrollo y escribir la prueba del Blueprint.** Leer `render.yaml` con `yaml.safe_load`. Afirmar los recursos pagos y la migración desde `/app/backend`:

  ```python
  manifest = yaml.safe_load(Path("render.yaml").read_text(encoding="utf-8"))
  web, db = manifest["services"][0], manifest["databases"][0]
  assert (web["runtime"], web["plan"], web["branch"]) == ("docker", "0.5c-512mb", "main")
  assert web["healthCheckPath"] == "/api/health/"
  assert web["preDeployCommand"] == "python manage.py migrate --noinput"
  assert db["plan"] == "0.1c-256mb" and db["ipAllowList"] == []
  assert web["region"] == db["region"] == "virginia"
  ```

  Inspeccionar `envVars` y afirmar `DATABASE_URL.fromDatabase.property == "connectionString"`, `DJANGO_ENV.value == "production"` y `DJANGO_SECRET_KEY.generateValue is True`.
- [ ] **Step 2: Ejecutar** `python -m pytest backend/tests/test_render_blueprint.py -q` **y constatar que falta `render.yaml`.**
- [ ] **Step 3: Crear `render.yaml` con los valores de la prueba.** Sin credenciales, siguiendo esta estructura:

  ```yaml
  databases:
    - name: bigmedia-db
      plan: 0.1c-256mb
      region: virginia
      postgresMajorVersion: '17'
      ipAllowList: []
  services:
    - type: web
      name: bigmedia-web
      runtime: docker
      plan: 0.5c-512mb
      region: virginia
      branch: main
      autoDeployTrigger: commit
      healthCheckPath: /api/health/
      preDeployCommand: python manage.py migrate --noinput
      envVars:
        - key: DATABASE_URL
          fromDatabase: {name: bigmedia-db, property: connectionString}
        - key: DJANGO_SECRET_KEY
          generateValue: true
        - key: DJANGO_ENV
          value: production
        - key: DJANGO_DEBUG
          value: 'false'
  ```

  Comprobar en la documentación de Render que `preDeployCommand` se ejecuta desde la imagen Docker y que el trabajo tiene acceso a la base antes de crear recursos.
- [ ] **Step 4: Ejecutar** `python -m pytest backend/tests/test_render_blueprint.py -q` **y** `git diff --check`. Validar el YAML con el validador de Render si hay acceso; de lo contrario, registrar que la validación de proveedor queda para la instalación.
- [ ] **Step 5: Commit:** `git add render.yaml backend/pyproject.toml backend/tests/test_render_blueprint.py && git commit -m "chore: declare paid Render web and Postgres services"`.

#### Task 4: Guía operativa y verificación final

**Files:**
- Create: `docs/operacion/despliegue-render.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: `render.yaml` y la imagen de Tasks 2–3.
- Produces: procedimiento que el dueño de la cuenta puede ejecutar y verificar antes de ingresar datos reales.

- [ ] **Step 1: Documentar alta de Blueprint desde `main`, revisión de los cargos antes de aplicar, URL asignada, variables generadas, `check --deploy`, creación de superusuario desde Render Shell y cuentas individuales de Seba/Ale.** Registrar que PR #1 debe estar integrado antes de verificar inventario. Incluir comprobación HTTPS, salud, login, permisos, persistencia tras nuevo despliegue, logs y error de migración.
- [ ] **Step 2: Documentar recuperación:** confirmar PITR activo, crear instancia restaurada separada, comprobar un registro, volver a la instancia primaria; exportar un `pg_dump` antes de migraciones de riesgo. Explicar la ventana Hobby de 3 días y que una retención mayor requiere copias externas o plan superior.
- [ ] **Step 3: Enlazar la guía desde `README.md` sin declarar que el sistema ya está online.**
- [ ] **Step 4: Verificación final:** `python -m pytest backend/tests -q`, `python backend/manage.py check`, `npm test`, `npm run lint`, `npm run build`, `docker build -t bigmedia-render .`, `git diff --check`. Si PostgreSQL local está disponible, activar la prueba de integración existente. Revisar el diff y no cargar datos reales.
- [ ] **Step 5: Commit:** `git add docs/operacion/despliegue-render.md README.md && git commit -m "docs: add Render launch and recovery runbook"`.
- [ ] **Step 6: Abrir PR contra `main` con resultados de pruebas, costo esperado y pasos pendientes en la cuenta de Render.** No integrar ni crear recursos pagos automáticamente.

### Handoff

El PR #1 de inventario está separado. Si se integra durante este trabajo, actualizar la rama antes de la verificación final y repetir las pruebas pertinentes. La puesta en marcha real en Render sucede después de aprobar el gasto y conectar la cuenta de GitHub; este plan entrega código y una guía listos para revisar.
