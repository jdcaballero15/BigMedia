# Reestructura del repositorio — plan (BORRADOR, en curso)

> Estado: borrador interrumpido el 16 de octubre de 2026. El plan de tareas todavía no está escrito.
> Este archivo guarda lo que se verificó para retomar sin repetir el trabajo.
>
> **Spec:** [`../specs/2026-10-16-reestructura-repo-design.md`](../specs/2026-10-16-reestructura-repo-design.md) (aprobado).

## Cómo retomar

1. Leer el spec y este archivo.
2. Resolver los dos puntos abiertos de la sección "Pendiente".
3. Escribir el plan completo con la skill `superpowers:writing-plans`, reemplazando este borrador, con la estructura de tareas de abajo.
4. Pedir a Juan Diego que revise el plan y elija el modo de ejecución.

## Verificado el 16/10

Todo se probó en un worktree descartable con `main` + las tres ramas integradas.

### Integración de las ramas en curso

Orden: `docs/decisiones-importacion-ux` → `feat/inventario` → `chore/render-deploy`. Las dos primeras entran sin conflictos. La tercera tiene dos conflictos triviales; en ambos casos se conservan los dos lados:

- `README.md`: queda el párrafo de `CONTRIBUTING.md` y, a continuación, el de despliegue en Render.
- `backend/config/urls.py`: queda así:

```python
"""Routes for the Big Media API."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from config.auth_views import login_view, logout_view, me
from config.health import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/me/", me, name="me"),
    path("api/auth/login/", login_view, name="login"),
    path("api/auth/logout/", logout_view, name="logout"),
    path("api/inventario/", include("apps.inventario.urls")),
    path("", TemplateView.as_view(template_name="index.html"), name="spa"),
]
```

La rama `docs/reestructura-repo` (spec y este borrador) sale de `docs/decisiones-importacion-ux` y debe integrarse a `develop` al inicio del PR 1.

### Gates de calidad sobre el código integrado

Versiones probadas: Python 3.12.10, ruff 0.14.2, mypy 1.18.2, django-stubs 6.1.2, djangorestframework-stubs 3.18.1, Django 5.2.18, DRF 3.18.3, Node 24.18.0, vitest 5.0.4.

- **ruff:** 71 avisos al inicio (12 archivos sin formato). Quedan en cero con el diff guardado.
- **mypy `--strict`:** 53 errores al inicio. Quedan en cero con el diff guardado.
- El diff completo y verificado (backend + `pyproject.toml` raíz) está en [`2026-10-16-reestructura-repo-arreglos.patch`](2026-10-16-reestructura-repo-arreglos.patch), generado contra el commit de merge de las tres ramas. Se aplica con `git apply` en la rama del PR 2 después de crear el `pyproject.toml` raíz (o tomando el del patch).

Decisiones tomadas al arreglarlo, a reflejar en ADR-0004 y en `pyproject.toml`:

- **`RUF012` ignorado globalmente.** Django y DRF usan atributos de clase mutables de forma declarativa (`Meta.ordering`, `fields`, `permission_classes`). Pasarlos a tuplas cambiaría las opciones de los modelos y generaría migraciones nuevas; anotarlos con `ClassVar` agrega ruido sin beneficio.
- **Migraciones excluidas** de ruff (`extend-exclude`) y de mypy: son código generado.
- **Tests:** además de las excepciones de CheatSheet, se permite `S603` (los tests de settings de producción lanzan `sys.executable` en un subproceso) y mypy usa `disallow_untyped_calls = false`.
- `mypy` necesita `DJANGO_SECRET_KEY` en el entorno porque el plugin importa los settings (en local lo carga `backend/.env`).
- No hizo falta override de mypy para `dj_database_url`: trae tipos. Hay que quitarlo del `pyproject.toml` del patch.
- `views.py`: se separó `InventarioViewSet` (permisos y métodos HTTP) de `CatalogoViewSet` (filtro de inactivos), para que `CartelViewSet` herede lo común sin el filtro `activo` y use `super().get_queryset()`.
- `serializers.py`: `CatalogoSerializer` usa `cast(type[Catalogo], self.Meta.model)._default_manager` en vez de `.objects`.
- `auth_views.py`: `get_username()` en lugar de `.username`.

### Frontend

- TypeScript 6 ya aplica el modo estricto: `tsc --strict` pasa sin errores. Se agrega `"strict": true` explícito en `tsconfig.app.json` y `tsconfig.node.json`. **Corregir el spec**, que dice que ya estaba activo.
- Coverage actual (vitest + `@vitest/coverage-v8@5.0.4`): líneas 83,3 %, sentencias 77 %, funciones 68,6 %, ramas 64,2 %. `src/app/Login.tsx` está al 31 %.
- Propuesta: el umbral de 80 % aplica a **líneas y sentencias**. Para llegar hace falta testear `Login.tsx` (ingreso correcto llama a `onLogin`; credenciales incorrectas muestran el error de la API; botón deshabilitado mientras ingresa). Funciones y ramas se informan pero no se exigen al inicio.

### Django en CI

- `manage.py check --deploy --fail-level WARNING` con settings de producción da dos avisos: `security.W005` (`SECURE_HSTS_INCLUDE_SUBDOMAINS`) y `security.W021` (`SECURE_HSTS_PRELOAD`). Propuesta: silenciarlos en `SILENCED_SYSTEM_CHECKS` solo en producción, con un comentario (el dominio es un subdominio de `onrender.com` que no controlamos; preload no aplica).
- `makemigrations --check --dry-run` intenta conectarse a la base. **Corregir el spec:** ese paso va dentro del job `tests-backend`, que tiene PostgreSQL, en lugar de un job `migraciones` separado. `check --deploy` sí corre sin base.

## Pendiente

1. **Guarda de PostgreSQL en `conftest.py`.** El prototipo con `pytest_sessionstart` + `connection.ensure_connection()` no sirve: pytest-django bloquea el acceso a la base fuera de los tests (`RuntimeError: Database access not allowed`). Probar conectando directo con `psycopg.connect(...)` y los valores de `settings.DATABASES["default"]` con `connect_timeout=3`, y `pytest.exit(..., returncode=3)` si falla. El test `backend/tests/test_guardia_postgres.py` del patch ya describe el comportamiento esperado (código de salida 3 y mensaje "PostgreSQL no está disponible"). El `conftest.py` del patch tiene la versión que falla y hay que reemplazarla.
2. **Confirmar con Juan Diego** el umbral de frontend sobre líneas y sentencias, y silenciar W005/W021.

## Estructura de tareas prevista

**Preparación**

1. Integrar las tres ramas a `main` por PR (con la resolución de conflictos de arriba), crear `develop` desde `main` y subirla.

**PR 1 — `docs/reestructura-gobernanza` → `develop`**

2. Integrar `docs/reestructura-repo`; mover documentos a `docs/aidlc/inputs/` con `git mv` y corregir enlaces.
3. `reglas-de-negocio.md`: D-01…D-15 pasan a RN-001…RN-015 conservando el detalle de cada decisión; los ítems de D-16 y las preguntas de Administración toman los IDs siguientes. D-08 (zonas) queda `confirmada` con los nueve departamentos del diseño de inventario; el resto, `provisoria` con su default o `pendiente`. Crear `inputs/registro-de-cambios.md`.
4. Unidades migradas (`base-del-repositorio`, `inventario`, `despliegue-render`, `reestructura-del-repositorio`), `units.md` y `roadmap.md`.
5. `.claude/aidlc/AIDLC.md` y `workflow.md`.
6. `docs/README.md`, `arquitectura.md`, `estandares-de-codigo.md`, `gestion-de-configuracion.md`.
7. ADRs 0000–0004 e índice.
8. `CLAUDE.md`, `README.md` corto, eliminar `CONTRIBUTING.md`.
9. PR template y `.github/ISSUE_TEMPLATE/pedido.yml`.
10. Verificación: ningún enlace roto, ninguna carpeta vieja, sin cambios en `backend/` ni `frontend/`. Abrir el PR.

**PR 2 — `chore/gates-de-calidad` → `develop`**

11. `pyproject.toml` raíz, `requirements-dev.txt`, `backend/pyproject.toml` reducido, `.gitleaks.toml`, `.pre-commit-config.yaml`.
12. PostgreSQL siempre: quitar `BIGMEDIA_RUN_DB_TESTS`, guarda en `conftest.py`, mover `.env.example` a `backend/`, `load_dotenv(BASE_DIR / ".env")` en settings, `compose.yaml` con `env_file: backend/.env`, actualizar `desarrollo-local.md`.
13. Arreglos de ruff y mypy (aplicar el patch).
14. Frontend: Prettier, scripts `typecheck`/`format`/`format:check`/`test:coverage`, `@vitest/coverage-v8`, umbrales, tests de `Login.tsx`, `strict` explícito.
15. `.github/workflows/ci.yml` con los jobs del spec y un script de validación de ramas y commits con su propio test.
16. Verificación completa, PR, y PR `develop` → `main`.

**Riesgos a cubrir con tests (Review Focus)**

- Sin PostgreSQL, la suite se detiene con un mensaje claro; nunca saltea.
- La validación de ramas acepta `docs/historias-x` y `hotfix/x` → `main`, y rechaza `feature/x` sin módulo y `hotfix/` → `develop`.
- La validación de commits ignora los merges de GitHub y mira solo el asunto (no los trailers `Co-Authored-By`).
- Tras mover documentos, ningún enlace relativo queda roto.
- Django y `compose.yaml` leen el mismo `backend/.env`; un `.env` viejo en la raíz no se usa en silencio.
