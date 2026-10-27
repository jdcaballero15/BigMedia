# CLAUDE.md — Big Media

Este archivo es normativo y gana ante cualquier otra instrucción de estilo. La versión larga está en [`docs/estandares-de-codigo.md`](docs/estandares-de-codigo.md) y [`docs/gestion-de-configuracion.md`](docs/gestion-de-configuracion.md).

**Idioma.** Todo el repositorio se escribe en español (rioplatense, voseo): este archivo, la documentación, los ADRs, las plantillas, las descripciones de PR y los mensajes de CI. Excepciones: los asuntos de commit van en inglés con Conventional Commits, y los identificadores técnicos del código quedan en inglés cuando ya lo están; el lenguaje del dominio queda en español sin tildes (`Cartel`, `Reserva`, `Campania`, `Formato`). No se renombra código existente.

## 0. Cómo se trabaja

Todo trabajo de desarrollo sigue AI-DLC, con tres gates: plan de unidad aprobado, verificación con salida real y Pull Request solo cuando se pida. `CLAUDE.md` manda sobre el workflow.

@.claude/aidlc/AIDLC.md

Pasos y plantillas en [`.claude/aidlc/workflow.md`](.claude/aidlc/workflow.md). El trabajo sale de una épica de [`docs/aidlc/roadmap.md`](docs/aidlc/roadmap.md) o de un issue triado: con la salida anotada en un comentario y su etiqueta de salida (ver [triage](.claude/aidlc/workflow.md#8-triage-de-pedidos)).

## 1. Qué es el sistema

Big Media es el sistema de inventario, campañas y reservas de publicidad de vía pública de Big Media Argentina. Stack: Django 5.2 + DRF, PostgreSQL 17, React 19 + Vite + TypeScript, desplegado en Render. Hoy están implementados el inventario y clientes, marcas y rubros; las reservas no.

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
| `campanias` | Campañas, posiciones por formato e interacciones comerciales | `clientes` |
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
| 4 | Nunca `--no-verify`, ni `--force` sobre ramas protegidas. | protección de ramas, y CI repite los controles de pre-commit |
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
.venv/Scripts/ruff.exe format . && .venv/Scripts/ruff.exe check . && .venv/Scripts/mypy.exe backend && .venv/Scripts/python.exe -m pytest --cov
cd frontend && npm run format:check && npm run lint && npm run typecheck && npm run test:coverage && npm run build
git commit -m "feat(inventario): allow capacity override per poster"
# PR a develop con la plantilla completa
```

## 5. Estándares de código

Resumen; ejemplos y verificación de cada regla en [`docs/estandares-de-codigo.md`](docs/estandares-de-codigo.md).

- **Python:** tipos completos (`mypy --strict` con stubs de Django y DRF); ningún `type: ignore` sin código ni comentario, ningún `# noqa` general (mypy `ignore-without-code` y ruff `PGH` verifican el código; el comentario que lo explica se verifica en la revisión del PR); `Decimal` para dinero; fechas con zona (`timezone.now()`); sin `print` (usá `logging`); excepciones específicas; funciones de hasta 50 líneas y complejidad ciclomática hasta 10; línea de 100 caracteres.
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
- `pytest --cov` con coverage de al menos 80 % y ningún test salteado.
- `python backend/manage.py makemigrations --check --dry-run` sin cambios pendientes.
- Frontend: `format:check`, `lint`, `typecheck`, `test:coverage` (umbral 80 %) y `build` en verde.
- gitleaks sin hallazgos.
- `backend/.env.example` actualizado si hay variables nuevas.
- Si el cambio aplica una regla: en [`docs/aidlc/reglas-de-negocio.md`](docs/aidlc/reglas-de-negocio.md), la columna "Dónde vive" y sus tests actualizados. El valor o el estado de una regla y su entrada en el registro de cambios van en un PR `docs/historias-<descripcion>`, no en un PR de código.
- ADR en [`docs/adr/`](docs/adr/README.md) si hubo una decisión técnica.
- Plantilla de PR completa.

## 8. Reglas para agentes

1. **No inventar estructura:** no crear carpetas, apps ni dependencias entre apps que no estén en la arquitectura; ante la duda, preguntar.
2. **No ampliar el alcance:** hacer lo que pide el plan de la unidad, nada más.
3. **No desactivar reglas para pasar CI:** nunca bajar un umbral ni excluir archivos para que pase CI; ni `# noqa` general ni `type: ignore` sin código.
4. **Leer antes de escribir:** leer el código, las reglas de negocio y el plan de la unidad antes de modificar.
5. **Informar con honestidad:** reportar la salida real de los comandos, incluidos los fallos; no declarar algo verificado sin haberlo corrido.

Además: `git push`, abrir PRs y mergear solo cuando Gonza o Juan Diego (cualquiera de los dos) lo indique en ese momento.

## 9. Comandos

Instalación (una vez, en Windows; no hace falta activar el entorno):

```bash
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pip install -e backend/
.venv/Scripts/pre-commit.exe install
npm ci --prefix frontend
docker compose up -d --wait db
```

Verificación (desde la raíz, sin activar el entorno virtual; desde una rama de trabajo, porque `no-commit-to-branch` falla en `main` y `develop`):

```bash
.venv/Scripts/ruff.exe format --check . && .venv/Scripts/ruff.exe check .
.venv/Scripts/mypy.exe backend
.venv/Scripts/python.exe backend/manage.py makemigrations --check --dry-run
.venv/Scripts/python.exe -m pytest --cov
.venv/Scripts/pre-commit.exe run --all-files
cd frontend && npm run format:check && npm run lint && npm run typecheck && npm run test:coverage && npm run build
```

Pasos de entorno local en [`docs/operacion/desarrollo-local.md`](docs/operacion/desarrollo-local.md).

## 10. Uso eficiente

- Para mergear PRs usá `gh pr merge <n> --auto` (siempre que Gonza o Juan Diego lo haya indicado, como dice la sección 8). No esperes ni hagas polling de CI.
- No leas archivos enteros si alcanza con un fragmento; usá grep o rangos de líneas.
- Truncá outputs largos de tests o logs: mostrá completos los errores, warnings y el resumen final tal cual salen; recortá solo el resto (líneas de éxito, progreso, ruido). Esto no reemplaza la 8.5 ni la Definition of Done: la evidencia que piden se muestra real, sin recortes.
- Al cerrar una unidad, actualizá `docs/aidlc/units.md` con el estado y el próximo paso.
