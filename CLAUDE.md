# CLAUDE.md — Big Media

Este archivo es normativo y gana ante cualquier otra instrucción de estilo. La versión larga está en [`docs/estandares-de-codigo.md`](docs/estandares-de-codigo.md) y [`docs/gestion-de-configuracion.md`](docs/gestion-de-configuracion.md).

**Idioma.** Todo el repositorio se escribe en español (rioplatense, voseo): este archivo, la documentación, los ADRs, las plantillas, las descripciones de PR y los mensajes de CI. Excepciones: los asuntos de commit van en inglés con Conventional Commits, y los identificadores técnicos del código quedan en inglés cuando ya lo están; el lenguaje del dominio queda en español sin tildes (`Cartel`, `Reserva`, `Campania`, `Formato`). No se renombra código existente.

## 0. Cómo se trabaja

Todo trabajo de desarrollo sigue AI-DLC, con tres gates: plan de unidad aprobado, verificación con salida real y Pull Request solo cuando se pida. `CLAUDE.md` manda sobre el workflow.

@.claude/aidlc/AIDLC.md

Pasos y plantillas en [`.claude/aidlc/workflow.md`](.claude/aidlc/workflow.md). El trabajo sale de una épica de [`docs/aidlc/roadmap.md`](docs/aidlc/roadmap.md) o de un issue triado (`pedido`, `bug`, `regla`).

## 1. Qué es el sistema

Big Media es el sistema de inventario, campañas y reservas de publicidad de vía pública de Big Media Argentina. Stack: Django 5.2 + DRF, PostgreSQL 17, React 19 + Vite + TypeScript, desplegado en Render. Hoy está implementado el inventario; las reservas no.

Riesgo dominante de las apps que más importan:

- `reservas`: sobreventa de un cartel.
- `facturacion`: importes y cierre mensual incorrectos.
- `auditoria`: pérdida de inmutabilidad del registro.

Los riesgos de las demás apps están en [`docs/arquitectura.md`](docs/arquitectura.md#3-apps-del-backend).

## 2. Arquitectura y estructura

Monolito modular: una API Django y una base PostgreSQL; cada área de negocio es una app en `backend/apps/<app>/`. El frontend (`frontend/src/features/<app>/`) usa los mismos nombres de app.

| App | Responsabilidad | Puede importar de |
| --- | --- | --- |
| `usuarios` | Cuentas, sesión y permisos | — |
| `inventario` | Formatos, proveedores, zonas, carteles y capacidad | — |
| `clientes` | Clientes, marcas, contactos | — |
| `campanias` | Campañas y posiciones por formato | `clientes` |
| `reservas` | Disponibilidad, confirmación, cancelación | `inventario`, `campanias` |
| `costos` | Costos de reservas e ítems de facturación | `reservas`, `inventario` |
| `facturacion` | Importes, cierre mensual, exportación | `campanias`, `reservas`, `costos`, `clientes` |
| `auditoria` | Registro inmutable de cambios | ninguna (las demás le escriben por su servicio) |

Una app no importa modelos de otra fuera de esta tabla; se revisa en el PR, ninguna herramienta lo verifica. Las reglas de negocio viven en `apps/<app>/services.py` o en el modelo, no en vistas ni serializers.

En la raíz va lo que gobierna ambos lados (`pyproject.toml`, `requirements-dev.txt`, `.pre-commit-config.yaml`, `.gitleaks.toml`, `compose.yaml`, `Dockerfile`, `render.yaml`, `docs/`, `.claude/`, `.github/`); la API en `backend/` y la web en `frontend/`. Detalle en [`docs/arquitectura.md`](docs/arquitectura.md).

## 3. Reglas absolutas

| # | Regla | Quién la hace cumplir |
| --- | --- | --- |
| 1 | Nada se escribe directo en `main` ni en `develop`. | pre-commit `no-commit-to-branch` y protección de ramas |
| 2 | Ninguna credencial en el código; todo por variables de entorno. | gitleaks (CI y pre-commit) y `.gitignore` |
| 3 | Nunca se commitean `.env`, `*.pem`, `*.key`, `*.p12` ni `*.crt`. | gitleaks (CI y pre-commit) y `.gitignore` |
| 4 | Nunca `--no-verify`, ni `--force` sobre ramas protegidas. | protección de ramas |
| 5 | `Decimal` para dinero (tarifas, importes, costos), nunca `float`. | revisión del PR y [estándares](docs/estandares-de-codigo.md#dinero-con-decimal) |
| 6 | Ningún dato personal real en desarrollo, pruebas ni logs. | revisión del PR |
| 7 | La confirmación de reservas ocurre solo en el servidor, dentro de una transacción de PostgreSQL. | revisión del PR y tests de concurrencia cuando exista `reservas` |
| 8 | No se crean carpetas nuevas en la raíz sin un ADR aprobado. | revisión del PR y [ADR](docs/adr/README.md) |

## 4. Workflow de ramas

GitFlow: todo cambio entra por Pull Request.

| Tipo | Patrón | Destino |
| --- | --- | --- |
| Funcionalidad | `feature/<modulo>-<descripcion>` | `develop` |
| Corrección | `fix/<modulo>-<descripcion>` | `develop` |
| Documentación | `docs/<descripcion>` | `develop` |
| Mantenimiento | `chore/<descripcion>` | `develop` |
| Emergencia | `hotfix/<descripcion>` | `main`, y después merge a `develop` |
| Release | `develop` | `main` |

`<descripcion>` va en kebab-case. Módulos válidos: `usuarios`, `inventario`, `clientes`, `campanias`, `reservas`, `costos`, `facturacion`, `auditoria`, `frontend`, `infra` y `docs`. `main` es producción y despliega en Render; `develop` integra y solo corre CI.

Hotfix: `hotfix/<descripcion>` desde `main`, PR a `main`; después `chore/infra-sincronizar-main-<AAAAMMDD>` desde `main`, PR a `develop`. Detalle en [`docs/gestion-de-configuracion.md`](docs/gestion-de-configuracion.md#hotfix).

```bash
git switch develop && git pull
git switch -c feature/inventario-capacidad-por-cartel
# trabajo...
ruff format . && ruff check . && mypy backend && pytest
cd frontend && npm run format:check && npm run lint && npm run typecheck && npm run test:coverage && npm run build
git commit -m "feat(inventario): allow capacity override per poster"
# PR a develop con la plantilla completa
```

## 5. Estándares de código

Resumen; ejemplos y verificación de cada regla en [`docs/estandares-de-codigo.md`](docs/estandares-de-codigo.md).

- **Python:** tipos completos (`mypy --strict` con stubs de Django y DRF); ningún `type: ignore` sin código ni comentario, ningún `# noqa` general (los verifican mypy `ignore-without-code` y ruff `PGH`); `Decimal` para dinero; fechas con zona (`timezone.now()`); sin `print` (usá `logging`); excepciones específicas; funciones de hasta 50 líneas y complejidad ciclomática hasta 10; línea de 100 caracteres.
- **Django:** reglas de negocio en servicios o modelo; confirmaciones con `transaction.atomic()` y `select_for_update()`; baja lógica (nunca `DELETE` desde la API); toda migración revisada a mano y comprobada con `makemigrations --check`.
- **TypeScript:** `strict`, sin `any` explícito ni `@ts-ignore` (esto lo verifica la revisión del PR, no una herramienta); Prettier y oxlint.
- **Tests:** siempre contra PostgreSQL, sin red; nombre `test_<qué>_<condición>_<resultado>`; `@pytest.mark.regla("RN-xxx")` en los que verifican una regla; todo bug empieza con un test que lo reproduce.
- **Coverage mínimo:** backend 80 % (sentencias y ramas); frontend 80 % de líneas y de sentencias. Bajar un umbral requiere un ADR nuevo.
- **Ningún archivo excluido** de las herramientas, salvo migraciones (código generado).

## 6. Commits

```text
<tipo>(<modulo>): <qué hace el commit>
```

Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`. El módulo es opcional y, si está, es uno de los válidos. Asunto en inglés, con al menos 10 caracteres de descripción. CI rechaza los asuntos que no cumplen el formato, salvo los merges de GitHub; los trailers (`Co-Authored-By`) no se validan.

## 7. Definition of Done

Un cambio está terminado cuando se cumple todo esto, con la salida real de los comandos a la vista:

- `ruff format --check` y `ruff check` sin errores.
- `mypy backend` sin errores.
- `pytest` con coverage de al menos 80 % y ningún test salteado.
- `python backend/manage.py makemigrations --check --dry-run` sin cambios pendientes.
- Frontend: `format:check`, `lint`, `typecheck`, `test:coverage` (umbral 80 %) y `build` en verde.
- gitleaks sin hallazgos.
- `backend/.env.example` actualizado si hay variables nuevas.
- [`docs/aidlc/reglas-de-negocio.md`](docs/aidlc/reglas-de-negocio.md) actualizado si cambió una regla.
- ADR en [`docs/adr/`](docs/adr/README.md) si hubo una decisión técnica.
- Plantilla de PR completa.

## 8. Reglas para agentes

1. **No inventar estructura:** no crear carpetas, apps ni dependencias entre apps que no estén en la arquitectura; ante la duda, preguntar.
2. **No ampliar el alcance:** hacer lo que pide el plan de la unidad, nada más.
3. **No desactivar reglas para pasar CI:** nunca bajar un umbral ni excluir archivos para que pase CI; ni `# noqa` general ni `type: ignore` sin código.
4. **Leer antes de escribir:** leer el código, las reglas de negocio y el plan de la unidad antes de modificar.
5. **Informar con honestidad:** reportar la salida real de los comandos, incluidos los fallos; no declarar algo verificado sin haberlo corrido.

Además: `git push`, abrir PRs y mergear solo cuando Juan Diego lo indique en ese momento.

## 9. Comandos

Instalación (una vez):

```bash
py -3.12 -m venv .venv
pip install -r requirements-dev.txt
pip install -e backend/
pre-commit install
npm ci --prefix frontend
docker compose up -d --wait db
```

Verificación (desde la raíz; `requirements-dev.txt`, pre-commit y los scripts de frontend `format:check`, `typecheck` y `test:coverage` llegan con el PR `chore/gates-de-calidad`):

```bash
ruff format --check . && ruff check .
mypy backend
python backend/manage.py makemigrations --check --dry-run
pytest
pre-commit run --all-files
cd frontend && npm run format:check && npm run lint && npm run typecheck && npm run test:coverage && npm run build
```

Pasos de entorno local en [`docs/operacion/desarrollo-local.md`](docs/operacion/desarrollo-local.md).
