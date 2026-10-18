# Gestión de configuración

Ramas, commits, entornos, credenciales y CI. Es la versión larga de las secciones 4 y 6 de [`CLAUDE.md`](../CLAUDE.md). La decisión de fondo está en [ADR-0002](adr/0002-gitflow-con-develop.md).

## 1. Ramas (GitFlow)

**Todos los cambios se integran mediante Pull Request.** No se hacen commits ni pushes directos a `main` ni a `develop`, ni siquiera para documentación o correcciones pequeñas.

| Tipo | Patrón | Destino |
| --- | --- | --- |
| Funcionalidad | `feature/<modulo>-<descripcion>` | `develop` |
| Corrección | `fix/<modulo>-<descripcion>` | `develop` |
| Documentación | `docs/<descripcion>` | `develop` |
| Mantenimiento | `chore/<descripcion>` | `develop` |
| Emergencia | `hotfix/<descripcion>` | `main`, y después merge a `develop` |
| Release | `develop` | `main` |

- `<descripcion>` va en kebab-case.
- Módulos válidos: `usuarios`, `inventario`, `clientes`, `campanias`, `reservas`, `costos`, `facturacion`, `auditoria`, `frontend`, `infra` y `docs`.
- `main` es producción y despliega en Render; `develop` integra y solo corre CI.
- Los PRs de release (`develop` → `main`) y de sincronización (`chore/infra-sincronizar-main-…` → `develop`) se integran con merge commit, nunca con squash, para que las ramas no diverjan.

### Ciclo

1. Actualizá `develop` y creá tu rama desde ahí: `git switch develop && git pull && git switch -c feature/inventario-capacidad-por-cartel`.
2. Hacé commits acotados a la tarea.
3. Corré las comprobaciones del cambio (ver [Definition of Done](../CLAUDE.md)) y abrí un PR hacia `develop`.
4. Con el CI en verde y el PR revisado, se integra a `develop`.
5. Cuando `develop` está listo para producción, se abre el PR de release `develop` → `main`. Al integrarlo, Render despliega solo si el CI pasó.

### Hotfix

Para una emergencia en producción: rama `hotfix/<descripcion>` desde `main`, PR hacia `main` y, una vez integrado, creá `chore/infra-sincronizar-main-<AAAAMMDD>` desde `main` y abrí un PR hacia `develop` para que no se pierda el arreglo. (El job `convenciones` rechaza PRs de `main` o de `hotfix/*` hacia `develop`, por eso la sincronización va en una rama `chore/`.) Un hotfix también lleva su test que reproduce el error.

### Trabajo en paralelo y push rechazado

- Si otra persona trabaja en paralelo, conservá sus archivos y commits fuera de tu rama; no los incluyas en tus commits.
- **No uses `--force`** para resolver un rechazo de push, y nunca sobre `main` ni `develop`. Tampoco `--no-verify`.
- Si el push se rechaza porque la rama remota avanzó, actualizá tu rama (`git pull --rebase origin <tu-rama>`), resolvé los conflictos, volvé a correr las comprobaciones y reintentá. Si no entendés el rechazo, coordinalo con el equipo antes de tocar nada más.

## 2. Commits

```text
<tipo>(<modulo>): <qué hace el commit>
```

- Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`.
- El módulo es opcional y, si está, es uno de los válidos (lista en la sección 1).
- El asunto va en inglés, con al menos 10 caracteres de descripción. Ejemplo: `feat(inventario): add poster capacity override`.
- El job `convenciones` del CI rechaza los mensajes que no cumplen el formato, salvo los commits de merge de GitHub. Solo mira el asunto: los trailers como `Co-Authored-By` no se validan.

## 3. Entornos

| Entorno | Cómo se configura | Cuándo corre |
| --- | --- | --- |
| Local | PostgreSQL con Docker Compose (`docker compose up -d --wait db`) y variables en `backend/.env` | Desarrollo. Pasos en [desarrollo local](operacion/desarrollo-local.md). |
| CI | PostgreSQL 17 como service container de GitHub Actions | PRs y pushes a `develop` y `main` |
| Producción | Render, desde `main`, con `render.yaml`. Pasos en [despliegue en Render](operacion/despliegue-render.md) | Cada integración a `main` con CI en verde (`autoDeployTrigger: checksPass`) |

**Staging no existe.** Queda documentado en ADR-0002 como el siguiente paso, sin implementar: [ADR-0002](adr/0002-gitflow-con-develop.md).

## 4. Credenciales

- **`.env` nunca se commitea**, ni `*.pem`, `*.key`, `*.p12` ni `*.crt`.
- `backend/.env.example` se versiona con valores vacíos o de ejemplo. Si agregás una variable, actualizá ese archivo en el mismo PR.
- Los secretos de producción (`DJANGO_SECRET_KEY`, `DATABASE_URL`) viven en Render; nunca en Git ni en mensajes.
- Verifican gitleaks (job `secretos` y pre-commit), `detect-private-key` y la revisión del PR.

## 5. CI

`.github/workflows/ci.yml` corre en pull requests y pushes a `develop` y `main`. Los mensajes de error están en español.

| Job | Nombre en GitHub | Qué hace | Falla cuando |
| --- | --- | --- | --- |
| `convenciones` (solo PR) | Convenciones (rama y commits) | Prueba el validador y valida rama contra destino según la tabla de ramas y el formato de cada commit | Validador roto; rama mal nombrada o con destino incorrecto; commit fuera de formato |
| `lint-python` | Lint Python (ruff) | `ruff format --check` y `ruff check` | Formato o reglas de ruff |
| `tipos` | Tipos (mypy --strict) | `mypy --strict` con `django-stubs` y `djangorestframework-stubs` | Código sin tipar o tipos inconsistentes |
| `check-deploy` | Configuración de producción (check --deploy) | `manage.py check --deploy --fail-level WARNING` con settings de producción | Configuración insegura |
| `tests-backend` | Tests backend (PostgreSQL) | `manage.py makemigrations --check --dry-run` y pytest contra PostgreSQL 17 en un service container, coverage mínimo de 80 % | Modelo cambiado sin migración, test fallido, coverage bajo el umbral, o algún test salteado por falta de base |
| `frontend` | Frontend | `npm run format:check` (Prettier), `lint` (oxlint), `typecheck` (`tsc -b`), `test:coverage` (vitest, mínimo de 80 % en líneas y sentencias) y `build` | Cualquiera de esos pasos |
| `secretos` | Credenciales (gitleaks) | gitleaks sobre el árbol de trabajo | Credencial detectada |
| `imagen` | Imagen de producción | `docker build` del Dockerfile de producción | La imagen no compila |

Las versiones fijas de las herramientas están en `requirements-dev.txt`; actualizarlas es un cambio deliberado, en su propio PR.

## 6. Configuración manual en GitHub

La hace Juan Diego desde la configuración del repositorio; no se puede hacer desde un PR. Hacela cuando el CI nuevo ya haya corrido al menos una vez, para que GitHub ofrezca los jobs como checks requeridos.

### Proteger `main` y `develop`

Repetí estos pasos para cada rama:

1. Abrí el repositorio en GitHub → **Settings** → **Branches** → **Add rule** (o **Add branch ruleset**).
2. En *Branch name pattern* escribí `main` (y después repetí con `develop`).
3. Activá **Require a pull request before merging**.
4. Activá **Require status checks to pass before merging** y agregá los ocho checks del CI con el nombre que muestra GitHub: **Convenciones (rama y commits)**, **Lint Python (ruff)**, **Tipos (mypy --strict)**, **Configuración de producción (check --deploy)**, **Tests backend (PostgreSQL)**, **Frontend**, **Credenciales (gitleaks)** e **Imagen de producción**.
5. Activá **Do not allow bypassing the above settings**.
6. Guardá con **Create**.

`main` además solo debería recibir PRs desde `develop` o `hotfix/*`; el job `convenciones` lo verifica en cada PR.

### `develop` como rama por defecto

Para que los PRs nuevos apunten a `develop` sin tener que cambiar el destino a mano: **Settings** → **General** → **Default branch** → ícono de cambio → elegí `develop` → **Update**.

### Etiquetas de los pedidos

Con la CLI de GitHub (`gh`) ya autenticada, desde la raíz del repositorio:

```bash
gh label create pedido --color 0E8A16 --description "Pedido de Seba o Ale por WhatsApp o llamada"
gh label create bug --color D73A4A --description "Algo no anda como debería"
gh label create regla --color 1D76DB --description "Cambia o confirma una regla de negocio"
gh label create descartado --color CCCCCC --description "Se decidió no hacerlo (con motivo en el issue)"
```

Los colores y textos son sugeridos; si una etiqueta ya existe, `gh` lo avisa y no la pisa. El flujo de los pedidos está en [`AIDLC.md`](../.claude/aidlc/AIDLC.md) y en [ADR-0003](adr/0003-requisitos-evolutivos.md).
