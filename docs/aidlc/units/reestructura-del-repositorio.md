# Unidad: Reestructura del repositorio

- **Estado:** en curso · **Épica:** — (unidad técnica)
- **Rama:** `docs/reestructura-gobernanza` + `chore/gates-de-calidad` · **Fecha:** 2026-10-16
- **Origen:** migrado desde `docs/superpowers/` el 2026-10-16. El contenido no se modificó, salvo el nivel de los encabezados y los enlaces que dejaron de resolver.

**Avance:** Tareas 1–9 hechas; Tarea 10 en curso (falta definir «Próximas» del roadmap y los gates 2 y 3). Sigue la Tarea 11 en `chore/gates-de-calidad`.

## Diseño

Estado: para revisión de Juan Diego, 16 de octubre de 2026.

### Propósito

Adoptar la organización del repositorio de referencia [CheatSheet](https://github.com/cheatsheet12/CheatSheet): gobernanza escrita, ADRs, CI con gates estrictos y un workflow de desarrollo con puntos de aprobación. La lógica de negocio de CheatSheet no aplica a Big Media; solo se toma su estructura, sus convenciones y su configuración.

Hay una diferencia de contexto que condiciona todo el diseño: CheatSheet parte de requisitos cerrados y trata las historias de usuario como insumo de solo lectura. En Big Media el relevamiento es incompleto y no hay tiempo para mejorarlo antes de construir. Las reglas de negocio, las historias y el alcance van a cambiar a medida que Seba use el sistema. Por eso se conserva lo que ayuda cuando todo cambia (CI estricto, tests, unidades chicas, ADRs técnicos) y se aligera lo que estorba (roadmap completo por adelantado, planes largos, historias inmutables).

### Alcance

**Se adopta**

- Gobernanza y documentación: `CLAUDE.md` normativo, documentos de arquitectura, estándares y gestión de configuración, ADRs, PR template y plantilla de issues.
- CI y calidad estrictos: ruff, mypy `--strict` con stubs de Django, coverage mínimo de 80 % en backend y frontend, gitleaks, pre-commit.
- Workflow AI-DLC adaptado a requisitos evolutivos.
- GitFlow con `develop`.

**No se adopta**

- Hooks de Claude Code (`.claude/hooks/`). El cumplimiento de reglas queda en CI, pre-commit y la protección de ramas de GitHub.
- Arquitectura hexagonal por bounded context. El backend sigue organizado como apps de Django.
- Entorno de staging. Queda documentado en ADR-0002 como el siguiente paso, sin implementar.

### Precondiciones

Antes de empezar, se integran a `main` las ramas en curso, en este orden y sin modificarlas:

1. `docs/decisiones-importacion-ux` (decisiones pendientes, plantillas de importación, recorrido de UX).
2. `feat/inventario` (app `inventario`, autenticación, PR template y `CONTRIBUTING.md`).
3. `chore/render-deploy` (Dockerfile, `render.yaml`, CI inicial, settings de producción).

Después se crea `develop` desde ese `main`. La reestructura parte de `develop` y absorbe lo que esas ramas agregaron: el CI, el PR template y `CONTRIBUTING.md` se reescriben; `docs/arquitectura/estructura-repo.md` se integra en `docs/arquitectura.md`.

### Entrega en dos PRs

1. **`docs/reestructura-gobernanza`** — gobernanza, ADRs, workflow AI-DLC, migración de documentos y plantillas de GitHub. Solo documentación y plantillas; no cambia código.
2. **`chore/gates-de-calidad`** — configuración de herramientas, CI nuevo y los arreglos de código necesarios para que el código existente pase los gates estrictos.

Ambos apuntan a `develop`. Al terminar, se abre el PR `develop` → `main`.

### Estructura resultante

```text
bigMedia/
├── CLAUDE.md                       # constitución normativa
├── README.md                       # qué es, cómo arrancar, enlaces a docs/
├── pyproject.toml                  # ruff, mypy, pytest y coverage para todo el Python
├── requirements-dev.txt            # herramientas con versión fija
├── .pre-commit-config.yaml
├── .gitleaks.toml
├── compose.yaml                    # Postgres local; lee backend/.env
├── Dockerfile, .dockerignore, render.yaml   # sin cambios de forma
├── .github/
│   ├── workflows/ci.yml
│   ├── pull_request_template.md
│   └── ISSUE_TEMPLATE/pedido.yml
├── .claude/
│   └── aidlc/
│       ├── AIDLC.md
│       └── workflow.md
├── backend/
│   ├── pyproject.toml              # solo empaquetado y dependencias de la aplicación
│   ├── .env.example                # movido desde la raíz
│   ├── manage.py
│   ├── config/
│   ├── apps/<app>/
│   └── tests/
│       └── README.md
├── frontend/
│   ├── .prettierrc.json
│   ├── .oxlintrc.json
│   ├── package.json                # scripts typecheck, format:check, test:coverage
│   └── src/{app,features/<app>,shared}/
└── docs/
    ├── README.md
    ├── arquitectura.md
    ├── estandares-de-codigo.md
    ├── gestion-de-configuracion.md
    ├── adr/
    │   ├── README.md
    │   ├── 0000-plantilla.md
    │   ├── 0001-estructura-del-repositorio.md
    │   ├── 0002-gitflow-con-develop.md
    │   ├── 0003-requisitos-evolutivos.md
    │   └── 0004-gates-de-calidad-estrictos.md
    ├── operacion/
    │   ├── desarrollo-local.md
    │   └── despliegue-render.md
    └── aidlc/
        ├── inputs/
        │   ├── historias-de-usuario.md
        │   ├── registro-de-cambios.md
        │   ├── importacion/        # plantillas CSV y su README
        │   └── ux/
        ├── reglas-de-negocio.md
        ├── roadmap.md
        ├── units.md
        └── units/<unidad>.md
```

`analytics/` no se crea hasta que tenga contenido. No se crean carpetas vacías.

#### Movimientos de documentos

| Origen | Destino |
|---|---|
| `docs/requisitos/historias-de-usuario.md` | `docs/aidlc/inputs/historias-de-usuario.md` |
| `docs/importacion/` | `docs/aidlc/inputs/importacion/` |
| `docs/ux/` | `docs/aidlc/inputs/ux/` |
| `docs/decisiones/2026-10-15-pendientes-seba-ale.md` | filas de `docs/aidlc/reglas-de-negocio.md`; el archivo se elimina |
| `docs/superpowers/specs/*` y `plans/*` | `docs/aidlc/units/<unidad>.md`, un archivo por tema con spec y plan fusionados |
| `docs/arquitectura/estructura-repo.md` | integrado en `docs/arquitectura.md` |
| `CONTRIBUTING.md` | integrado en `docs/gestion-de-configuracion.md` y `CLAUDE.md`; se elimina |
| `.env.example` (raíz) | `backend/.env.example` |

Las unidades migradas son `base-del-repositorio`, `inventario`, `despliegue-render` y `reestructura-del-repositorio` (este documento), todas registradas en `units.md`. Los enlaces internos de cada documento movido se actualizan. Al terminar, `docs/superpowers/`, `docs/requisitos/`, `docs/importacion/`, `docs/ux/`, `docs/decisiones/` y `docs/arquitectura/` dejan de existir.

### Política de idioma

Todo el repositorio se escribe en español: `CLAUDE.md`, documentación, ADRs, PR template, plantillas de issues, descripciones de PR y mensajes de CI. Excepciones:

- **Commits:** Conventional Commits en inglés, como hasta ahora (`feat(inventario): add poster capacity override`). El tipo y el módulo son vocabulario fijo; mantener el resto en inglés conserva la coherencia con el historial.
- **Código:** identificadores técnicos en inglés cuando ya lo están; el lenguaje del dominio queda en español sin tildes (`Cartel`, `Reserva`, `Campania`, `Formato`), como ya hace la app `inventario`. No se renombra código existente.

### Gobernanza

#### `CLAUDE.md`

Normativo, en español, con la misma estructura que el de CheatSheet:

0. Cómo se trabaja: AI-DLC, con `@.claude/aidlc/AIDLC.md` importado. Tres gates.
1. Qué es el sistema y el riesgo dominante de cada app (`reservas`: sobreventa de un cartel; `facturacion`: importes y cierre mensual; `auditoria`: inmutabilidad del registro).
2. Arquitectura y estructura: monolito modular Django, tabla de apps con responsabilidades y dependencias permitidas, qué va en la raíz y qué dentro de cada paquete.
3. Reglas absolutas, cada una con quién la hace cumplir (CI, pre-commit o revisión del PR):
   1. Nada se escribe directo en `main` ni en `develop`.
   2. Ninguna credencial en el código; todo por variables de entorno.
   3. Nunca se commitean `.env`, `*.pem`, `*.key`, `*.p12` ni `*.crt`.
   4. Nunca `--no-verify`, ni `--force` sobre ramas protegidas.
   5. `Decimal` para dinero (tarifas, importes, costos), nunca `float`.
   6. Ningún dato personal real en desarrollo, pruebas ni logs.
   7. La confirmación de reservas ocurre solo en el servidor, dentro de una transacción de PostgreSQL.
   8. No se crean carpetas nuevas en la raíz sin un ADR aprobado.
4. Workflow de ramas.
5. Resumen de estándares de código.
6. Commits.
7. Definition of Done.
8. Reglas para agentes: no inventar estructura, no ampliar el alcance, no desactivar reglas para pasar CI, leer antes de escribir, informar con honestidad.
9. Comandos.

La versión larga de las reglas, con ejemplos correctos e incorrectos y cómo se verifica cada una, va en `docs/estandares-de-codigo.md`.

#### Apps y dependencias

Las apps de Django cumplen el rol de los bounded contexts de CheatSheet: `usuarios`, `inventario`, `clientes`, `campanias`, `reservas`, `costos`, `facturacion` y `auditoria`. `docs/arquitectura.md` declara qué app puede depender de cuál (por ejemplo, `reservas → inventario`, `reservas → campanias`). Una app no importa modelos de otra fuera de esas dependencias. Esto se revisa en el PR; ninguna herramienta lo verifica.

#### Ramas (GitFlow)

| Tipo | Patrón | Destino |
|---|---|---|
| Funcionalidad | `feature/<modulo>-<descripcion>` | `develop` |
| Corrección | `fix/<modulo>-<descripcion>` | `develop` |
| Documentación | `docs/<descripcion>` | `develop` |
| Mantenimiento | `chore/<descripcion>` | `develop` |
| Emergencia | `hotfix/<descripcion>` | `main`, y después merge a `develop` |
| Release | `develop` | `main` |

`<descripcion>` va en kebab-case. Módulos válidos: los ocho nombres de app, más `frontend`, `infra` y `docs`. `main` es producción y despliega en Render; `develop` integra y solo corre CI.

#### Commits

```
<tipo>(<modulo>): <qué hace el commit>
```

Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`. El módulo es opcional y, si está, es uno de los válidos. Mínimo 10 caracteres de descripción. CI rechaza los mensajes que no cumplen el formato, salvo los commits de merge de GitHub.

#### PR template

En español, con estas secciones: descripción; issue que cierra (`Closes #N`); módulos afectados; tipo de cambio; reglas de negocio tocadas (RN-xxx) y si se actualizó `reglas-de-negocio.md`; Definition of Done (ruff, mypy, pytest con coverage, frontend, gitleaks, migraciones); seguridad (sin credenciales ni datos reales, `.env.example` actualizado si hay variables nuevas); calidad y decisiones (tests nuevos, test que reproduce el bug si es un fix, ADR si hubo decisión técnica, ninguna regla desactivada).

#### Plantilla de issues

`.github/ISSUE_TEMPLATE/pedido.yml`, formulario "Pedido de Seba" pensado para cargarse desde el celular después de una llamada o un WhatsApp: fecha, canal, qué pidió con sus palabras, pantalla o proceso afectado, urgencia y adjuntos. Etiquetas: `pedido`, `bug`, `regla`, `descartado`. `docs/gestion-de-configuracion.md` documenta cómo crear las etiquetas.

#### ADRs

`docs/adr/` copia el modelo de CheatSheet, traducido: plantilla con contexto, decisión, alternativas consideradas, consecuencias e impacto en reglas del repositorio; índice en el README; un ADR aceptado no se edita, se reemplaza por otro que lo referencia. Hace falta un ADR cuando una decisión afecta a más de una app o es costosa de revertir. Los cambios de reglas de negocio no requieren ADR, salvo que obliguen a cambiar la arquitectura o una regla de `CLAUDE.md`.

ADRs iniciales:

- **0001 — Estructura del repositorio.** Monolito modular Django con apps como módulos; frontend por `features/<app>`; qué va en la raíz y qué dentro de cada paquete; alternativas descartadas (arquitectura hexagonal de CheatSheet, separar en servicios).
- **0002 — GitFlow con `develop`.** Modelo de ramas y por qué. Staging como siguiente paso: un servicio web y una base en Render conectados a `develop`, y un job `deploy-staging` en CI con `needs:` sobre todos los gates. Se recomienda activarlo cuando Seba empiece a probar cambios antes de que lleguen a producción.
- **0003 — Requisitos evolutivos.** Catálogo de reglas de negocio, historias vivas con IDs estables, issues para los pedidos y unidades de ajuste. Explica en qué se aparta del AI-DLC de CheatSheet y por qué.
- **0004 — Gates de calidad estrictos.** mypy `--strict` con stubs de Django, coverage mínimo de 80 %, tests siempre contra PostgreSQL. Bajar un umbral requiere un ADR nuevo.

Las decisiones ya tomadas sobre Render e inventario no se convierten en ADRs retroactivos; quedan registradas en sus planes de unidad migrados.

### Requisitos evolutivos

#### Catálogo de reglas de negocio

`docs/aidlc/reglas-de-negocio.md` es una tabla viva:

| Columna | Contenido |
|---|---|
| ID | `RN-001`, `RN-002`, … Nunca se reutiliza. |
| Regla | Enunciado breve. |
| Estado | `pendiente` · `provisoria` · `confirmada` · `reemplazada por RN-xxx` |
| Valor actual | Lo que el sistema hace hoy. |
| Origen | Documento de historias, Seba, Ale o issue `#N`, con fecha. |
| HUs | Historias que la usan. |
| Dónde vive | Parámetro configurable o código; tests que la cubren. |

- `provisoria` significa que se usa un valor razonable para no frenar el desarrollo hasta que Big Media confirme.
- Lo que está en `provisoria` se implementa, en lo posible, como parámetro configurable (HU-001), para cambiarlo sin desplegar código.
- Los tests que verifican una regla llevan `@pytest.mark.regla("RN-xxx")`; el marcador se declara en `pyproject.toml`. `pytest -m regla` y una búsqueda por ID encuentran todo lo afectado por un cambio.
- La carga inicial sale de `docs/decisiones/2026-10-15-pendientes-seba-ale.md` y de las decisiones abiertas al final del documento de historias.

#### Historias vivas

- `docs/aidlc/inputs/historias-de-usuario.md` es la fuente de verdad. El archivo original fuera del repositorio queda como histórico.
- Las historias se cambian en un PR `docs/historias-<descripcion>`, nunca mezclado con código.
- Los IDs no se reutilizan ni se renumeran. Una historia eliminada se marca `(retirada AAAA-MM-DD: motivo)`; una fusionada, `(fusionada en HU-xxx)`. Las nuevas toman el siguiente número libre.
- Cada cambio agrega una entrada a `docs/aidlc/inputs/registro-de-cambios.md`: fecha, quién lo pidió, issue, HUs afectadas, qué cambió y por qué, y qué regla abre o cierra.
- El mismo PR actualiza `roadmap.md` y `units.md` si el cambio mueve historias entre épicas o afecta unidades.
- Cuando se toca una historia, sus reglas pasan a referenciarse por ID en lugar de repetirse. No se reescribe el documento completo por adelantado.

#### Pedidos de Seba

Los pedidos llegan por WhatsApp y llamadas. Se cargan como issues con la plantilla "Pedido de Seba". El triage clasifica cada issue en una de cuatro salidas: cambia una regla, es una historia nueva o ajustada, es un bug, o se descarta (con motivo). El PR que lo resuelve lo cierra con `Closes #N`, y queda la traza pedido → PR → regla o test. El repositorio guarda solo lo decidido.

### Workflow AI-DLC adaptado

#### Archivos

- `.claude/aidlc/AIDLC.md`: se carga siempre desde `CLAUDE.md`. Contiene los tres gates, las reglas no negociables y cómo retomar trabajo.
- `.claude/aidlc/workflow.md`: los pasos y las plantillas de `roadmap.md`, `units.md` y el plan de unidad. Se carga al empezar trabajo de desarrollo.

#### Documentos de trabajo

- `roadmap.md`: corto y reordenable. Épica actual, las dos o tres siguientes y una lista "más adelante". Se reordena cuando cambian las prioridades de Big Media; no reparte todo el catálogo de una vez.
- `units.md`: una tabla para todo el proyecto con épica, unidad, app dueña, HUs/RN/issue, dependencias, responsable, rama y estado (`pendiente`, `en curso`, `en revisión`, `mergeada`). El estado de una épica se deriva de sus unidades.
- `units/<unidad>.md`: plan de una página y registro de sus gates.

#### Ciclo de una unidad

0. **Origen.** Una épica del roadmap o un issue triado.
1. **Encuadre** (sin gate). Leer historias y reglas involucradas y revisar el registro de cambios por si se movieron desde que se mapeó la unidad. Decir en tres líneas qué app es dueña, qué capas toca y si implica migraciones o reglas nuevas. Si no está claro, preguntar en español con opciones concretas.
2. **Gate 1 — Plan de unidad.** Objetivo; HUs, RN e issue; cambios por app; migraciones; cómo se prueba; reglas en `provisoria` que se usan. No se toca `backend/` ni `frontend/` hasta que se apruebe.
3. **Implementación.** TDD; tests con marcador de regla; lo provisorio como parámetro cuando sea posible.
4. **Gate 2 — Verificación.** Correr los mismos comandos que CI y reportar la salida real.
5. **Gate 3 — Pull Request.** Push y PR solo cuando se pidan. El PR cierra su issue y actualiza `units.md` y, si corresponde, `reglas-de-negocio.md`.

#### Diferencias con CheatSheet

- Historias y reglas son insumos vivos: cambian por PR `docs/` con registro, sin ADR.
- El roadmap es corto y se reordena; no es un catálogo completo repartido al inicio.
- Una unidad mergeada es histórico inmutable. Un cambio posterior se hace en una unidad nueva `ajuste-<tema>` que referencia el cambio.
- Un cambio trivial (typo, versión) se declara en una línea y se implementa directo, siempre en rama y por PR.

#### Roadmap inicial

E0 (base) y E2 (inventario, sin la importación de HU-015) figuran como hechas; las unidades mergeadas se registran en `units.md`. La épica siguiente se elige con Juan Diego al escribir el roadmap, según lo que Seba necesite usar primero.

### CI y calidad

#### Workflow

`.github/workflows/ci.yml` corre en pull requests y pushes a `develop` y `main`. Jobs:

| Job | Qué hace | Falla cuando |
|---|---|---|
| `convenciones` (solo PR) | Valida rama contra destino según la tabla de ramas y el formato de cada commit | Rama mal nombrada o con destino incorrecto; commit fuera de formato |
| `lint-python` | `ruff format --check` y `ruff check` | Formato o reglas de ruff |
| `tipos` | `mypy --strict` con `django-stubs` y `djangorestframework-stubs` | Código sin tipar o tipos inconsistentes |
| `check-deploy` | `manage.py check --deploy --fail-level WARNING` con settings de producción | Configuración insegura |
| `tests-backend` | `manage.py makemigrations --check --dry-run` y pytest contra PostgreSQL 17 en un service container, coverage mínimo de 80 % | Modelo cambiado sin migración, test fallido, coverage bajo el umbral, o algún test salteado por falta de base |
| `frontend` | Prettier, oxlint, `tsc --noEmit`, vitest con coverage mínimo de 80 %, `vite build` | Cualquiera de esos pasos |
| `secretos` | gitleaks sobre el árbol de trabajo | Credencial detectada |
| `imagen` | `docker build` del Dockerfile de producción | La imagen no compila |

Render sigue desplegando `main` con `autoDeployTrigger: checksPass`, de modo que producción solo recibe commits con CI verde. Los mensajes de error de CI se escriben en español.

#### Configuración

- **`pyproject.toml` (raíz):** ruff con Python 3.12, línea 100 y las reglas de CheatSheet (`E`, `W`, `F`, `I`, `UP`, `B`, `S`, `ANN`, `PT`, `C90`, `SIM`, `RET`, `ARG`, `PTH`, `DTZ`, `T20`, `BLE`, `RUF`), con excepciones por archivo para tests y migraciones; mypy `strict` con el plugin de django-stubs; pytest con `DJANGO_SETTINGS_MODULE`, `--strict-markers`, `--strict-config` y el marcador `regla`; coverage con `branch = true` y `fail_under = 80`, sin contar migraciones.
- **`backend/pyproject.toml`:** solo empaquetado y dependencias de la aplicación. Pierde `[tool.pytest.ini_options]` y el extra `dev`, que pasan a la raíz y a `requirements-dev.txt`.
- **`requirements-dev.txt`:** versiones fijas de ruff, mypy, django-stubs, djangorestframework-stubs, pytest, pytest-django, pytest-cov y pre-commit. Actualizarlas es un cambio deliberado, en su propio PR.
- **`.pre-commit-config.yaml`:** trailing whitespace, fin de archivo, YAML/TOML/JSON válidos, conflictos de merge, archivos grandes, `detect-private-key`, `no-commit-to-branch` para `main` y `develop`, ruff y gitleaks. mypy queda solo en CI porque con stubs de Django es lento.
- **`.gitleaks.toml`:** reglas por defecto, con allowlist para `.env.example` y archivos Markdown.
- **Frontend:** Prettier con su configuración e ignore; scripts `typecheck`, `format`, `format:check` y `test:coverage`; umbral de coverage en `vite.config.ts` sobre **líneas y sentencias** (80 %); funciones y ramas se informan sin umbral.
- **`check --deploy`:** `security.W005` y `security.W021` se silencian solo en producción, con un comentario: el dominio es un subdominio de `onrender.com` que no controlamos y el preload de HSTS es difícil de revertir. TypeScript 6 ya aplica el modo estricto por defecto; se declara `"strict": true` explícito en `tsconfig.app.json` y `tsconfig.node.json`.

#### Tests siempre contra PostgreSQL

Se elimina `BIGMEDIA_RUN_DB_TESTS`. La suite completa corre siempre contra PostgreSQL: local con `docker compose up db`, en CI con el service container. El job `tests-backend` falla si algún test queda salteado. Así una regla de disponibilidad no puede pasar en un modo de ejecución y fallar en otro. `docs/operacion/desarrollo-local.md` y `backend/tests/README.md` se actualizan.

#### Arreglos de código

El PR 2 ajusta el código existente (configuración, salud, autenticación, app `inventario` y sus tests, frontend) para que pase ruff, mypy `--strict` y el coverage de 80 %. Si algo no se puede tipar sin pelearse con Django, se usa `# type: ignore[codigo]` con un comentario que explique por qué. No se usan ignores generales, no se excluyen archivos del linter y no se baja ningún umbral. Si el coverage del código existente queda por debajo de 80 %, se agregan los tests que falten en este mismo PR.

#### Protección de ramas

`docs/gestion-de-configuracion.md` documenta la configuración manual en GitHub: `main` y `develop` requieren PR y todos los jobs de CI en verde antes de mergear; `main` además solo recibe PRs desde `develop` o `hotfix/*`. Activarla lo hace Juan Diego desde la configuración del repositorio.

### Criterios de aceptación

**PR 1 — gobernanza**

- Existen `CLAUDE.md`, `docs/README.md`, `docs/arquitectura.md`, `docs/estandares-de-codigo.md`, `docs/gestion-de-configuracion.md`, los cuatro ADRs con plantilla e índice, `.claude/aidlc/`, el PR template y la plantilla de issues, todo en español.
- Todos los documentos están migrados según la tabla de movimientos; ninguna carpeta vieja queda en `docs/`; ningún enlace interno queda roto.
- `reglas-de-negocio.md` contiene todas las decisiones pendientes con estado e ID; `roadmap.md` y `units.md` reflejan lo hecho.
- `README.md` es breve y enlaza a `docs/`.
- No cambia código de backend ni de frontend.

**PR 2 — gates de calidad**

- Todos los jobs de CI pasan sobre `develop`.
- `pre-commit run --all-files` pasa en una máquina limpia siguiendo `docs/operacion/desarrollo-local.md`.
- La suite de backend corre contra PostgreSQL sin flags y ningún test queda salteado.
- Coverage de backend y frontend igual o mayor a 80 %.
- No hay ignores generales ni archivos excluidos de las herramientas.
- `.env.example` vive en `backend/` y `compose.yaml` funciona con `backend/.env`.

### Riesgos

- **Rebase de trabajo en paralelo.** Si se empieza otra rama antes de que el PR 2 llegue a `develop`, va a fallar los gates nuevos. Mitigación: mergear el PR 2 enseguida después del PR 1 y no abrir ramas de funcionalidad en el medio.
- **mypy strict con Django.** Los stubs no cubren todo; puede haber `type: ignore` justificados en serializers y querysets. Se aceptan con su comentario.
- **Ceremonia contra velocidad.** Si el workflow resulta pesado en la práctica, se aligera con un ADR que reemplace a ADR-0003; no se saltean pasos en silencio.

## Plan ejecutado

## Reestructura del repositorio — plan de implementación

> **Para agentes:** SUB-SKILL REQUERIDA: usar superpowers:subagent-driven-development (recomendado) o superpowers:executing-plans para implementar este plan tarea por tarea. Los pasos usan casillas (`- [ ]`) para el seguimiento.

**Objetivo:** adoptar la gobernanza, el CI estricto y el workflow AI-DLC del repositorio CheatSheet, adaptados a un proyecto Django con requisitos que cambian con el uso.

**Arquitectura:** dos PRs contra una rama `develop` nueva. El PR 1 (`docs/reestructura-gobernanza`) solo mueve y escribe documentación y plantillas. El PR 2 (`chore/gates-de-calidad`) agrega la configuración de herramientas, reescribe el CI y aplica los arreglos de código ya verificados para que el código existente pase los gates.

**Stack:** Django 5.2 + DRF 3.18, PostgreSQL 17, React 19 + Vite 8 + Vitest 5, TypeScript 6, GitHub Actions, Render.

**Spec:** [`../specs/2026-10-16-reestructura-repo-design.md`](#diseño)

### Restricciones globales

- Todo texto nuevo del repositorio va en español: documentos, ADRs, plantillas, mensajes de CI y de scripts. Excepción: asuntos de commit en inglés con Conventional Commits.
- El lenguaje del dominio queda en español sin tildes en identificadores (`Cartel`, `Campania`). No se renombra código existente.
- Python 3.12. Node 24.
- Versiones fijas de herramientas: ruff 0.14.2, mypy 1.18.2, django-stubs 6.1.2, django-stubs-ext 6.1.2, djangorestframework-stubs 3.18.1, types-PyYAML 6.0.12.20260906, pytest 9.1.1, pytest-django 4.14.0, pytest-cov 7.1.0, PyYAML 6.0.3, pre-commit 4.7.0, gitleaks 8.21.2, prettier 3.9.10, @vitest/coverage-v8 5.0.4.
- Coverage mínimo: backend 80 % (sentencias + ramas, `fail_under = 80`); frontend 80 % de líneas y 80 % de sentencias. Funciones y ramas del frontend se informan sin umbral.
- Ningún `# noqa` general, ningún `type: ignore` sin código ni comentario, ningún archivo excluido de las herramientas salvo migraciones (código generado).
- Los tests de backend corren siempre contra PostgreSQL. Desaparece `BIGMEDIA_RUN_DB_TESTS`.
- Módulos válidos para ramas y commits: `usuarios`, `inventario`, `clientes`, `campanias`, `reservas`, `costos`, `facturacion`, `auditoria`, `frontend`, `infra`, `docs`.
- `git push`, abrir PRs y mergear son acciones externas: el ejecutor las hace solo cuando Juan Diego lo indica en ese momento.
- Nunca `--no-verify` ni `--force` sobre `main` o `develop`.

### Foco de revisión

1. **PostgreSQL apagado.** Quien corre `pytest` sin la base levantada debe ver un único mensaje claro y código de salida 3, no 37 errores ni tests salteados. Lo cubre `test_guardia_postgres.py` (Tarea 13).
2. **Nombres de rama de la vida real.** `docs/historias-cancelacion` y `hotfix/x` → `main` se aceptan; `feature/capacidad` (sin módulo), `feat/inventario` (prefijo viejo) y `hotfix/x` → `develop` se rechazan. Lo cubre `test_validar_convenciones.sh` (Tarea 15).
3. **Commits con trailers y merges.** El job mira solo el asunto: los merges de GitHub pasan y la línea `Co-Authored-By` no se valida. Lo cubre el mismo test y el uso de `git log --format=%s` (Tarea 15).
4. **Enlaces rotos tras mover documentos.** Ningún enlace relativo en Markdown puede quedar apuntando a una ruta vieja. Lo cubre el verificador de enlaces (Tarea 10).
5. **`.env` viejo en la raíz.** Django y Compose leen `backend/.env`; un `.env` que quedó en la raíz no debe usarse en silencio. Lo cubre `test_settings_lee_backend_env` (Tarea 12) y la nota de migración en `desarrollo-local.md`.

---

### Preparación

#### Tarea 1: Integrar las ramas en curso y crear `develop`

**Archivos:**
- Modificar (resolución de conflictos): `README.md`, `backend/config/urls.py`

**Interfaces:**
- Produce: `main` con las tres ramas integradas; rama remota `develop` creada desde ese `main`.

> `chore/render-deploy` está abierta en otro worktree (`C:/Users/Juan Diego/Documents/Codex/2026-10-14/mej/work/bigmedia-inventario`). No se puede hacer checkout de ella en el worktree principal: la resolución de conflictos se hace en ese worktree o en uno temporal.

- [x] **Paso 1: Confirmar con Juan Diego** que se pueden abrir y mergear los tres PRs ahora, en este orden: `docs/decisiones-importacion-ux`, `feat/inventario`, `chore/render-deploy`.

- [x] **Paso 2: Abrir y mergear los dos primeros PRs** (entran sin conflictos):

```bash
git fetch origin
gh pr create --base main --head docs/decisiones-importacion-ux --title "docs: add pending decisions, inventory import and booking UX" --body "Decisiones pendientes con Seba y Ale, plantillas de importación y recorrido de UX."
gh pr merge docs/decisiones-importacion-ux --merge
gh pr create --base main --head feat/inventario --title "feat(inventario): add inventory module" --body "Módulo de inventario: catálogos, carteles, autenticación por sesión y pantallas."
gh pr merge feat/inventario --merge
```

Si `feat/inventario` ya tiene un PR abierto, usar ese en lugar de crear otro (`gh pr list --head feat/inventario`).

- [x] **Paso 3: Actualizar `chore/render-deploy` con `main` y resolver los dos conflictos**

```bash
git worktree add ../bm-render chore/render-deploy   # o trabajar en el worktree de Codex
cd ../bm-render
git pull --ff-only
git merge origin/main
```

Resolver `backend/config/urls.py` dejando exactamente:

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

Resolver `README.md` conservando ambos párrafos, primero el de `CONTRIBUTING.md` y luego el de Render, separados por una línea en blanco.

- [x] **Paso 4: Verificar la integración**

Con PostgreSQL levantado (`docker compose up -d --wait db`):

```bash
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
cd frontend && npm test && npm run lint && npm run build
```

Esperado: todo en verde (los tests de base de datos pueden aparecer como salteados; eso se corrige en la Tarea 12).

- [x] **Paso 5: Commit, push y PR** (con autorización de Juan Diego)

```bash
git add README.md backend/config/urls.py
git commit -m "chore: merge main into render deploy branch"
git push
gh pr create --base main --head chore/render-deploy --title "feat(infra): deploy to Render" --body "Imagen única Django + React, Blueprint de Render y CI inicial."
gh pr merge chore/render-deploy --merge
```

- [x] **Paso 6: Crear `develop`**

```bash
git fetch origin
git switch -c develop origin/main
git push -u origin develop
git worktree remove ../bm-render   # si se creó en el paso 3
```

---

### PR 1 — `docs/reestructura-gobernanza` → `develop`

#### Tarea 2: Mover documentos a `docs/aidlc/inputs/` y corregir enlaces

**Archivos:**
- Mover: `docs/requisitos/historias-de-usuario.md` → `docs/aidlc/inputs/historias-de-usuario.md`
- Mover: `docs/importacion/*` → `docs/aidlc/inputs/importacion/`
- Mover: `docs/ux/recorrido-disponibilidad-y-reservas.md` → `docs/aidlc/inputs/ux/recorrido-disponibilidad-y-reservas.md`
- Crear: `docs/aidlc/inputs/registro-de-cambios.md`
- Modificar: todo `.md` que enlace a las rutas viejas

**Interfaces:**
- Produce: las rutas nuevas de `docs/aidlc/inputs/`, que usan las Tareas 3, 4, 6 y 8.

- [x] **Paso 1: Crear la rama e integrar el spec**

```bash
git switch develop && git pull
git switch -c docs/reestructura-gobernanza
git merge --no-edit docs/reestructura-repo
```

- [x] **Paso 2: Mover con historia**

```bash
mkdir -p docs/aidlc/inputs/importacion docs/aidlc/inputs/ux
git mv docs/requisitos/historias-de-usuario.md docs/aidlc/inputs/historias-de-usuario.md
git mv docs/importacion/README.md docs/importacion/plantilla-gran-formato.csv docs/importacion/plantilla-sextuples.csv docs/importacion/plantilla-reporte-importacion.csv docs/aidlc/inputs/importacion/
git mv docs/ux/recorrido-disponibilidad-y-reservas.md docs/aidlc/inputs/ux/
```

- [x] **Paso 3: Crear `docs/aidlc/inputs/registro-de-cambios.md`**

```markdown
# Registro de cambios de las historias de usuario

Cada cambio a [`historias-de-usuario.md`](historias-de-usuario.md) agrega una fila, en el mismo PR
que lo hace. Los IDs de historia nunca se reutilizan ni se renumeran: una historia eliminada se
marca `(retirada AAAA-MM-DD: motivo)` y una fusionada `(fusionada en HU-xxx)`.

| Fecha | Pedido por | Issue | HUs | Qué cambió y por qué | Reglas |
| --- | --- | --- | --- | --- | --- |
| 2026-10-16 | Equipo | — | todas | Las historias pasan a esta carpeta y este documento se vuelve la fuente de verdad. El contenido no cambia. | — |
```

- [x] **Paso 4: Corregir los enlaces relativos dentro de los archivos movidos y de los que apuntan a ellos**

Buscar referencias viejas:

```bash
grep -rnE "requisitos/|importacion/|\(\.\./ux/|docs/ux/" --include=*.md . | grep -v node_modules
```

Reemplazos esperados (ajustar la profundidad relativa según el archivo que enlaza):
- `../requisitos/historias-de-usuario.md` → `../aidlc/inputs/historias-de-usuario.md` (desde `docs/<carpeta>/`)
- `../importacion/README.md` → `importacion/README.md` (desde `docs/aidlc/inputs/`) o `inputs/importacion/README.md` (desde `docs/aidlc/`)
- `../ux/recorrido-disponibilidad-y-reservas.md` → `ux/recorrido-disponibilidad-y-reservas.md` (desde `docs/aidlc/inputs/`)

Los archivos de `docs/decisiones/` y `docs/superpowers/` se reescriben en las Tareas 3 y 4; no hace falta corregirlos acá.

- [x] **Paso 5: Commit**

```bash
git add -A docs
git commit -m "docs: move requirements and inputs to aidlc folder"
```

#### Tarea 3: Catálogo de reglas de negocio

**Archivos:**
- Crear: `docs/aidlc/reglas-de-negocio.md`
- Eliminar: `docs/decisiones/2026-10-15-pendientes-seba-ale.md`

**Interfaces:**
- Consume: `docs/decisiones/2026-10-15-pendientes-seba-ale.md` (D-01…D-16 y el bloque de Administración).
- Produce: IDs `RN-001`…`RN-026` que usan las Tareas 4, 7, 9 y 13.

- [x] **Paso 1: Mover el archivo para conservar la historia y reescribirlo**

```bash
git mv docs/decisiones/2026-10-15-pendientes-seba-ale.md docs/aidlc/reglas-de-negocio.md
```

- [x] **Paso 2: Escribir la cabecera y la tabla resumen**

Reemplazar el título y la introducción por:

```markdown
# Reglas de negocio

Catálogo vivo de las reglas que el sistema aplica, con su estado. Cuando una regla cambia, se
actualiza acá, en la historia afectada y en el registro de cambios
([`inputs/registro-de-cambios.md`](inputs/registro-de-cambios.md)), en el mismo PR.

- **Estados:** `pendiente` (sin respuesta ni valor usable) · `provisoria` (se usa un valor razonable
  hasta que Big Media confirme) · `confirmada` · `reemplazada por RN-xxx`.
- **IDs:** nunca se reutilizan. Las reglas que vienen de las decisiones del 15/10 conservan su
  número viejo entre paréntesis (D-xx).
- **Tests:** los que verifican una regla llevan `@pytest.mark.regla("RN-xxx")`.
  `pytest -m regla` los lista todos.
- Lo que está en `provisoria` se implementa, en lo posible, como parámetro configurable (HU-001).
```

Después, la tabla resumen con columnas `ID | Regla | Estado | Valor actual | Origen | HUs | Dónde vive`, una fila por regla, con este mapeo:

| ID | Viene de | Estado | Dónde vive |
| --- | --- | --- | --- |
| RN-001…RN-007 | D-01…D-07 | `provisoria` (valor actual = el default de la decisión) | RN-004 y RN-005: `Formato.capacidad_predeterminada`, `Cartel.capacidad`, `backend/tests/test_carteles.py`. El resto: "Sin implementar". |
| RN-008 | D-08 | `confirmada`: los nueve departamentos (Ciudad, Godoy Cruz, Maipú, Luján de Cuyo, Guaymallén, Las Heras, San Martín, Rivadavia, San Carlos). Origen: Juan Diego, 15/10/2026, diseño de inventario. | Migración `inventario/0002_catalogos_iniciales`, catálogo editable |
| RN-009 | D-09 | `pendiente` | Sin implementar |
| RN-010 | D-10 | `provisoria` | Modelo `EstadoCartel`, migración `0002_catalogos_iniciales` (los cinco estados) |
| RN-011…RN-015 | D-11…D-15 | `provisoria` | Sin implementar |
| RN-016…RN-021 | Los seis ítems de D-16, en orden: grupo económico, cambio de razón social, interacciones previas, dimensiones por formato, formatos sin relevamiento, usuarios | `pendiente` | Sin implementar |
| RN-022…RN-026 | Las cinco filas de "Para Administración", en orden | `provisoria` las cuatro con default; `pendiente` la de corrección de ítems facturados | Sin implementar |

Origen por defecto: "Documento de historias (decisión D-xx del 15/10/2026)".

- [x] **Paso 3: Conservar el detalle**

Debajo de la tabla, una sección por regla (`### RN-001 Día límite entre reservas (D-01)`, …) con el contenido de la decisión original **sin cambios**: pregunta, preguntas de apoyo, opciones, default, qué bloquea y la línea de respuesta. Conservar también las secciones "Cómo se priorizó" (P1/P2/P3, como columna o nota) y adaptar "Cómo registrar una respuesta":

```markdown
## Cómo registrar una respuesta

1. Cargar o actualizar el issue del pedido (plantilla "Pedido de Seba").
2. En un PR `docs/historias-<descripcion>`: cambiar el estado y el valor de la regla, completar
   **Respuesta**, **Fecha** y **Quién respondió**, actualizar las historias afectadas y agregar
   una fila al registro de cambios.
3. Si la regla es un parámetro configurable (RN-001, RN-002), anotar el valor inicial para producción.
4. Si ya hay código que aplica la regla, el cambio de código va en una unidad aparte
   (`ajuste-<tema>`) que cierra el issue.
```

Corregir los enlaces internos: `../requisitos/historias-de-usuario.md` → `inputs/historias-de-usuario.md`; `../importacion/README.md` → `inputs/importacion/README.md`; `../ux/...` → `inputs/ux/...`.

- [x] **Paso 4: Verificar que no se perdió ninguna decisión**

```bash
for d in $(seq -w 1 15); do grep -q "(D-$d)" docs/aidlc/reglas-de-negocio.md || echo "Falta D-$d"; done
grep -c "^### RN-" docs/aidlc/reglas-de-negocio.md
```

Esperado: ninguna línea "Falta" y `26`.

- [x] **Paso 5: Commit**

```bash
git add -A docs
git commit -m "docs: turn pending decisions into business rules catalog"
```

#### Tarea 4: Unidades migradas, mapa de unidades y roadmap

**Archivos:**
- Crear: `docs/aidlc/units/base-del-repositorio.md`, `docs/aidlc/units/inventario.md`, `docs/aidlc/units/despliegue-render.md`, `docs/aidlc/units/reestructura-del-repositorio.md`
- Crear: `docs/aidlc/units.md`, `docs/aidlc/roadmap.md`
- Eliminar: `docs/superpowers/` completo (salvo lo que se mueve)

**Interfaces:**
- Consume: specs y planes de `docs/superpowers/`.
- Produce: los nombres de unidad usados en `units.md`.

- [x] **Paso 1: Fusionar cada spec con su plan**

Correspondencia:

| Unidad | Spec | Plan |
| --- | --- | --- |
| `base-del-repositorio` | `specs/2026-10-14-bigmedia-repo-design.md` | `plans/2026-10-15-bigmedia-base.md` |
| `inventario` | `specs/2026-10-15-bigmedia-inventario-design.md` | `plans/2026-10-15-bigmedia-inventario.md` |
| `despliegue-render` | `specs/2026-10-15-render-deploy-design.md` | `plans/2026-10-15-render-deploy.md` |
| `reestructura-del-repositorio` | `specs/2026-10-16-reestructura-repo-design.md` | `plans/2026-10-16-reestructura-repo.md` (este archivo) |

Para cada fila:

```bash
git mv docs/superpowers/specs/<spec>.md docs/aidlc/units/<unidad>.md
```

Editar `docs/aidlc/units/<unidad>.md`: anteponer esta cabecera, convertir el título original en `## Diseño` (bajando un nivel los encabezados del spec) y pegar debajo el plan completo bajo `## Plan ejecutado` (bajando un nivel sus encabezados). Después `git rm` del plan.

```markdown
# Unidad: <nombre legible>

- **Estado:** mergeada · **Épica:** <E0 Plataforma base | E2 Inventario de soportes | Infraestructura>
- **Rama:** `<rama>` · **Fecha:** <AAAA-MM-DD del merge>
- **Origen:** migrado desde `docs/superpowers/` el 2026-10-16. El contenido no se modificó.
```

Para `reestructura-del-repositorio`, el estado es `en curso` y la rama `docs/reestructura-gobernanza` + `chore/gates-de-calidad`.

`plans/2026-10-16-reestructura-repo-arreglos.patch` **no** se mueve ni se borra en este paso: se borra al final de la Tarea 13 (la Tarea 13 lo lee desde la rama `docs/reestructura-repo`).

- [x] **Paso 2: Escribir `docs/aidlc/units.md`**

```markdown
# Mapa de unidades

Una fila por unidad de trabajo. La columna `Épica` coincide con el nombre en
[`roadmap.md`](roadmap.md). El estado de una épica se deriva de sus unidades.

Estados: `pendiente` · `en curso` · `en revisión` (PR abierto) · `mergeada`.

| Épica | Unidad | App dueña | HUs / RN / issue | Depende de | Responsable | Rama | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E0 Plataforma base | [base-del-repositorio](units/base-del-repositorio.md) | infra | HU-002 | — | Juan Diego | main (inicial) | mergeada |
| E2 Inventario de soportes | [inventario](units/inventario.md) | inventario | HU-008…HU-014, RN-004, RN-005, RN-008, RN-010 | base-del-repositorio | Juan Diego | feat/inventario | mergeada |
| Infraestructura | [despliegue-render](units/despliegue-render.md) | infra | HU-002 | base-del-repositorio | Juan Diego | chore/render-deploy | mergeada |
| Infraestructura | [reestructura-del-repositorio](units/reestructura-del-repositorio.md) | docs, infra | — | despliegue-render | Juan Diego | docs/reestructura-gobernanza, chore/gates-de-calidad | en curso |

## Notas

- HU-015 (importación de inventario) queda fuera de la unidad `inventario` hasta tener los relevamientos (RN-009).
```

- [x] **Paso 3: Escribir `docs/aidlc/roadmap.md`**

```markdown
# Roadmap

Corto y reordenable: la épica en curso, las próximas y lo que queda para más adelante. Se reordena
cuando cambian las prioridades de Big Media; cada cambio de orden se anota abajo con fecha y motivo.
Las épicas vienen del mapa de [`inputs/historias-de-usuario.md`](inputs/historias-de-usuario.md).

## Hecho

- **E0 Plataforma base** — base del repositorio y despliegue en Render. HU-001 (parámetros) sigue pendiente.
- **E2 Inventario de soportes** — HU-008 a HU-014. HU-015 espera los relevamientos (RN-009).

## En curso

- Reestructura del repositorio (unidad técnica, sin épica).

## Próximas

1. A definir con Juan Diego según lo que Seba necesite usar primero.

## Más adelante

E1 Seguridad y acceso · E3 Clientes, marcas y CRM · E4 Campañas · E5 Reservas y motor de
disponibilidad · E6 Vista de disponibilidad · E7 Costos y rentabilidad · E8 Reportes y paneles ·
E9 Entrega y traspaso · E10 Armado de campañas y reserva masiva · E11 Facturación mensual.

E5 es el núcleo: si hay que recortar alcance, se recorta alrededor de ella y nunca adentro.

## Cambios de orden

| Fecha | Cambio | Motivo |
| --- | --- | --- |
```

> La sección "Próximas" la completa Juan Diego antes de mergear el PR 1. El ejecutor le pregunta qué épica sigue y la escribe; no la elige por su cuenta.

- [x] **Paso 4: Verificar que `docs/superpowers/` solo conserva el patch**

```bash
git ls-files docs/superpowers
```

Esperado: solo `docs/superpowers/plans/2026-10-16-reestructura-repo-arreglos.patch`.

- [x] **Paso 5: Commit**

```bash
git add -A docs
git commit -m "docs: migrate specs and plans to aidlc units"
```

#### Tarea 5: Workflow AI-DLC en `.claude/aidlc/`

**Archivos:**
- Crear: `.claude/aidlc/AIDLC.md`, `.claude/aidlc/workflow.md`

**Interfaces:**
- Consume: rutas de `docs/aidlc/` de las Tareas 2–4.
- Produce: `@.claude/aidlc/AIDLC.md`, importado por `CLAUDE.md` en la Tarea 8.

- [x] **Paso 1: Escribir `.claude/aidlc/AIDLC.md`** (en español, máximo ~80 líneas), con estas secciones y contenido:

1. **Qué es:** el workflow de desarrollo del repositorio; se aplica a toda funcionalidad, corrección, refactor o migración sin que haga falta pedirlo. Al recibir trabajo de desarrollo, decir en una línea qué unidad es y cargar `.claude/aidlc/workflow.md`.
2. **Los tres gates:** Gate 1 plan de unidad (nada se escribe en `backend/` ni `frontend/` sin aprobación); Gate 2 verificación (correr los comandos de CI y reportar la salida real; esperar a Juan Diego); Gate 3 PR (push y PR solo cuando se pidan). Entre gates no se inventan aprobaciones extra.
3. **No negociables:** `CLAUDE.md` manda sobre el workflow; un gate es una parada real (el silencio no es aprobación); nunca se esquiva una regla de CI o de pre-commit; los documentos de trabajo viven en `docs/aidlc/`; las preguntas se hacen en español, con opciones concretas, y la respuesta se anota en el plan de unidad.
4. **Requisitos vivos:** historias y reglas pueden cambiar. Antes de planificar, revisar `docs/aidlc/inputs/registro-de-cambios.md` y `docs/aidlc/reglas-de-negocio.md`. Un cambio de historia o regla va en un PR `docs/historias-<descripcion>`; una unidad mergeada no se reescribe: el ajuste es una unidad nueva `ajuste-<tema>`.
5. **De dónde sale el trabajo:** una épica de `roadmap.md` o un issue triado (`pedido`, `bug`, `regla`).
6. **Retomar:** si `docs/aidlc/units.md` tiene una unidad `en curso`, leer su plan y retomarla sin volver a preguntar lo que el plan ya registra.
7. **Trabajo trivial:** conversación sin cambios no lleva gates; un cambio más chico que su plan (typo, versión) se declara en una línea y se hace directo, siempre en rama y por PR.

- [x] **Paso 2: Escribir `.claude/aidlc/workflow.md`** (en español), con:

1. **Insumos y su estado:** tabla con `docs/arquitectura.md` y `docs/adr/` (decididos; cambian por ADR), `CLAUDE.md` y `docs/estandares-de-codigo.md` (decididos), `docs/gestion-de-configuracion.md` (decidido), `docs/aidlc/inputs/historias-de-usuario.md` y `docs/aidlc/reglas-de-negocio.md` (**vivos**; cambian por PR `docs/` con registro).
2. **Documentos de trabajo:** árbol de `docs/aidlc/` y para qué sirve cada uno (roadmap corto, `units.md` como mapa y estado, `units/<unidad>.md` como plan y registro de gates).
3. **Paso 0 — Origen** y **Paso 1 — Encuadre** (sin gate): leer historias, reglas y registro de cambios; decir en tres líneas app dueña, capas que toca, migraciones o reglas nuevas; preguntar si la app dueña no está clara.
4. **Paso 2 — Gate 1, plan de unidad:** agregar la fila a `units.md` si no existe, y esta plantilla:

```markdown
# Unidad: <nombre>

- **Estado:** en curso · **Épica:** <épica> · **App dueña:** <app>
- **Origen:** <HU-xxx / RN-xxx / issue #N> · **Rama:** `<tipo>/<modulo>-<descripcion>`

## Objetivo
<Una o dos oraciones.>

## Cambios
- <app>: <qué cambia>

## Migraciones
<Ninguna / cuáles y si mueven datos.>

## Reglas provisorias que se usan
<RN-xxx con su valor actual, o "ninguna".>

## Cómo se prueba
- <tests nuevos, con su marcador de regla si aplica>

## Registro de gates
- Gate 1 (plan): <fecha> — <aprobado por>
- Gate 2 (verificación): <fecha> — <salida resumida de los comandos>
- Gate 3 (PR): <número de PR>
```

5. **Paso 3 — Implementación:** TDD; tests con `@pytest.mark.regla("RN-xxx")` cuando verifican una regla; lo provisorio como parámetro cuando sea posible; commits en Conventional Commits.
6. **Paso 4 — Gate 2, verificación:** los mismos comandos de la Definition of Done de `CLAUDE.md` §7; pegar la salida real en el plan.
7. **Paso 5 — Gate 3, PR:** completar la plantilla de PR, `Closes #N` si hay issue, actualizar `units.md` (`en revisión`, después `mergeada`) y `reglas-de-negocio.md` si cambió una regla.
8. **Triage de pedidos:** cada issue `pedido` termina en una de cuatro salidas (cambia una regla, historia nueva o ajustada, bug, descartado con motivo); el issue se etiqueta y, si se acepta, se convierte en una unidad.
9. **Diferencias con el AI-DLC original de CheatSheet:** insumos vivos, roadmap corto, unidades de ajuste, plan de una página.

- [x] **Paso 3: Commit**

```bash
git add .claude/aidlc
git commit -m "docs: add evolutive AI-DLC workflow"
```

#### Tarea 6: Documentos de arquitectura, estándares y configuración

**Archivos:**
- Crear: `docs/README.md`, `docs/arquitectura.md`, `docs/estandares-de-codigo.md`, `docs/gestion-de-configuracion.md`
- Eliminar: `docs/arquitectura/estructura-repo.md` (su contenido se integra en `docs/arquitectura.md`)

**Interfaces:**
- Consume: spec, secciones "Gobernanza", "CI y calidad" y "Requisitos evolutivos".
- Produce: los enlaces que usan `CLAUDE.md` (Tarea 8), los ADRs (Tarea 7) y el PR template (Tarea 9).

- [x] **Paso 1: `docs/arquitectura.md`**, con:
  1. Estilo: monolito modular Django + DRF; una API, una base PostgreSQL; frontend React servido por la misma imagen en producción (resumen de `despliegue-render`). Integrar acá lo que tenga `docs/arquitectura/estructura-repo.md` y luego `git rm` ese archivo.
  2. Árbol del repositorio (el de la sección "Estructura resultante" del spec).
  3. Tabla de apps: nombre, responsabilidad (copiar de "Límites entre módulos" de la unidad `base-del-repositorio`), riesgo dominante, estado (`inventario` implementada; el resto, planificada).
  4. Dependencias permitidas entre apps, como tabla "app → puede importar de": `inventario` → —; `clientes` → —; `campanias` → `clientes`; `reservas` → `inventario`, `campanias`; `costos` → `reservas`, `inventario`; `facturacion` → `campanias`, `reservas`, `costos`, `clientes`; `auditoria` → ninguna (las demás le escriben a través de su servicio); `usuarios` → —. Cualquier app puede importar de `django.contrib.auth`. Se revisa en el PR.
  5. Regla crítica de disponibilidad (copiar de la unidad `base-del-repositorio`) y referencia a RN-001…RN-003.
  6. Frontend: `src/app/` (arranque, sesión), `src/features/<app>/` con los mismos nombres de app, `src/shared/` (cliente HTTP, UI común). El frontend no decide reglas de negocio.

- [x] **Paso 2: `docs/estandares-de-codigo.md`**: versión larga de `CLAUDE.md` §3 y §5. Para cada regla: enunciado, ejemplo correcto, ejemplo incorrecto y **cómo se verifica** (ruff + regla, mypy, CI, pre-commit o revisión). Incluir obligatoriamente:
  - Python: tipado completo (`mypy --strict`); `Decimal` para dinero con `quantize(Decimal("0.01"), ROUND_HALF_UP)`; fechas con zona (`DTZ`); sin `print` (`T20`); sin `except Exception` (`BLE`); excepciones específicas; funciones ≤ 50 líneas y complejidad ≤ 10 (`C90`).
  - Django: reglas de negocio en servicios o en el modelo, no en vistas; confirmaciones que dependen de disponibilidad dentro de `transaction.atomic()` con bloqueo de fila; baja lógica, nunca `DELETE` desde la API; toda migración revisada y comprobada en CI.
  - `type: ignore` solo con código y comentario; las decisiones de configuración de ADR-0004 (RUF012 ignorado, migraciones excluidas, excepciones en tests).
  - TypeScript: `strict`, sin `any` ni `@ts-ignore`, Prettier y oxlint.
  - Tests: siempre contra PostgreSQL; sin red; nombre `test_<qué>_<condición>_<resultado>` en código nuevo; marcador `regla`; todo bug empieza con un test que lo reproduce; coverage mínimo.
  - Datos: nunca datos personales reales; nunca credenciales en código.

- [x] **Paso 3: `docs/gestion-de-configuracion.md`**, con:
  1. Ramas (tabla del spec) y ciclo `feature` → `develop` → `main`; hotfix.
  2. Commits (formato, tipos, módulos).
  3. Entornos: local (Compose + `backend/.env`), CI (service container), producción (Render desde `main`). Staging: no existe; ver ADR-0002.
  4. Credenciales: `.env` nunca se commitea; `backend/.env.example` con valores vacíos o de ejemplo; secretos de producción en Render.
  5. CI: tabla de jobs del spec.
  6. **Configuración manual en GitHub**, paso a paso: proteger `main` y `develop` (Settings → Branches → Add rule: *Require a pull request before merging*, *Require status checks to pass* con todos los jobs del CI, *Do not allow bypassing*); poner `develop` como rama por defecto para que los PRs apunten ahí; crear las etiquetas `pedido`, `bug`, `regla`, `descartado` con `gh label create <nombre> --color <hex> --description "<texto>"`.
  7. Incorporar el contenido útil de `CONTRIBUTING.md` (trabajo en paralelo, no usar `--force`, qué hacer si falla el push) y luego `git rm CONTRIBUTING.md`.

- [x] **Paso 4: `docs/README.md`**: tabla con cada documento de `docs/` y para qué sirve (como el `docs/README.md` de CheatSheet), más `operacion/` y `aidlc/`. Aclarar que historias y reglas son insumos vivos.

- [x] **Paso 5: Commit**

```bash
git add -A docs CONTRIBUTING.md
git commit -m "docs: add architecture, standards and configuration guides"
```

#### Tarea 7: ADRs

**Archivos:**
- Crear: `docs/adr/README.md`, `docs/adr/0000-plantilla.md`, `docs/adr/0001-estructura-del-repositorio.md`, `docs/adr/0002-gitflow-con-develop.md`, `docs/adr/0003-requisitos-evolutivos.md`, `docs/adr/0004-gates-de-calidad-estrictos.md`

**Interfaces:**
- Consume: spec, sección "ADRs"; borrador de decisiones de la sección "Decisiones de configuración" de abajo.

- [x] **Paso 1: `docs/adr/0000-plantilla.md`**

```markdown
# ADR-NNNN — <Título en una línea, en imperativo>

- **Estado:** Propuesto | Aceptado | Rechazado | Reemplazado por [ADR-NNNN](NNNN-....md)
- **Fecha:** AAAA-MM-DD
- **Decidido por:** <persona o rol>
- **Módulos afectados:** <usuarios | inventario | clientes | campanias | reservas | costos | facturacion | auditoria | frontend | infra | docs>

---

## Contexto

Qué problema hay que resolver y por qué ahora. Incluir las restricciones reales: plazos, costo,
conocimiento del equipo, reglas de negocio que todavía pueden cambiar. Sin mencionar la solución.

## Decisión

Qué se decidió, en una o dos oraciones en presente:

> Vamos a usar X para Y.

Después, el detalle necesario para implementarlo sin volver a preguntar.

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| A | | |
| B | | |

Si esta tabla está vacía, el ADR no está listo.

## Consecuencias

**Positivas**
-

**Negativas / costo que aceptamos**
-

**Qué se vuelve más difícil**
-

## Impacto en las reglas del repositorio

Marcar lo que hay que actualizar y hacerlo en el mismo PR.

- [ ] `CLAUDE.md`
- [ ] `docs/estandares-de-codigo.md`
- [ ] `pyproject.toml`, `requirements-dev.txt` o la configuración del frontend
- [ ] `.github/workflows/ci.yml`
- [ ] `backend/.env.example`
- [ ] Ninguna

## Referencias

- Documentos, PRs, issues o ADRs relacionados.
```

- [x] **Paso 2: `docs/adr/README.md`**: traducción del README de ADRs de CheatSheet (qué es, cuándo escribir uno, cómo, reglas). Cambios: la lista de "cuándo" agrega "cambiar el modelo de ramas o los entornos" y aclara que **los cambios de reglas de negocio no llevan ADR** salvo que cambien la arquitectura o una regla de `CLAUDE.md`. Índice con los cuatro ADRs, todos `Aceptado`, fecha 2026-10-16.

- [x] **Paso 3: escribir los cuatro ADRs** con la plantilla. Contenido mínimo de cada uno:

  - **0001 — Organizar el repositorio como monolito modular Django.** Contexto: base existente Django + React, equipo chico, CheatSheet como referencia. Decisión: apps de Django como módulos, frontend por `features/<app>`, qué va en la raíz y qué en cada paquete (tabla del CLAUDE.md de CheatSheet adaptada: raíz = `pyproject.toml`, `requirements-dev.txt`, `.pre-commit-config.yaml`, `.gitleaks.toml`, `compose.yaml`, `Dockerfile`, `render.yaml`, `CLAUDE.md`, `README.md`, `docs/`, `.claude/`, `.github/`; paquete = `backend/pyproject.toml`, `backend/.env.example`, `frontend/package.json` y su configuración). Alternativas: hexagonal por bounded context como CheatSheet (descartada: duplica capas sobre el ORM de Django para un equipo chico y requisitos inestables); servicios separados (descartada: sin necesidad de escalar por separado); límites verificados por herramienta como `import-linter` (descartada por ahora; reconsiderar si las apps crecen).
  - **0002 — Usar GitFlow con `develop`.** Decisión: tabla de ramas del spec; `main` despliega a producción. Staging: no se implementa; se describe qué haría falta (servicio web + base en Render conectados a `develop`, un segundo Blueprint o servicio en `render.yaml`, job `deploy-staging` con `needs:` sobre todos los gates y `if: github.ref == 'refs/heads/develop'`, secretos en GitHub) y cuándo conviene (cuando Seba pruebe cambios antes de producción). Alternativa: trunk a `main` (descartada por elección de Juan Diego: separar integración de producción).
  - **0003 — Tratar requisitos y reglas de negocio como insumos vivos.** Contexto: relevamiento incompleto, el sistema se ajusta con el uso de Seba, pedidos por WhatsApp y llamadas. Decisión: catálogo `reglas-de-negocio.md`, historias con IDs estables y registro de cambios, issues "Pedido de Seba", unidades `ajuste-<tema>`, roadmap corto. Alternativas: AI-DLC de CheatSheet con insumos de solo lectura y ADR por cambio de historia (descartada: demasiado pesado para cambios frecuentes); `feedback.md` en el repo (descartada: anotar un pedido exigiría un PR); Notion u otra herramienta externa (descartada: separa el pedido del PR que lo resuelve).
  - **0004 — Exigir gates de calidad estrictos desde el inicio.** Decisión: ruff con las reglas de CheatSheet + `DJ`, mypy `--strict` con stubs de Django y DRF, coverage 80 %, tests siempre contra PostgreSQL, gitleaks, check de migraciones y de despliegue. Incluir las decisiones de configuración de la sección de abajo. Bajar un umbral requiere un ADR nuevo. Alternativas: gates graduales (mypy no estricto, 70 %) y básicos (sin mypy), ambas descartadas por elección de Juan Diego: cuando las reglas cambian seguido, los tests y los tipos son la red que avisa qué se rompió.

**Decisiones de configuración (para ADR-0004 y `docs/estandares-de-codigo.md`):**
- `RUF012` ignorado: Django y DRF declaran listas mutables como atributos de clase (`Meta.ordering`, `fields`, `permission_classes`). Pasarlas a tuplas cambia las opciones de los modelos y genera migraciones; anotarlas con `ClassVar` agrega ruido.
- Migraciones excluidas de ruff y mypy: código generado.
- Tests: se permiten `S101`, `S105`, `S106`, `S603` (subprocesos con `sys.executable` en los tests de settings de producción), y anotaciones opcionales; mypy relaja `disallow_untyped_defs`, `disallow_incomplete_defs` y `disallow_untyped_calls` solo en `tests.*`.
- `security.W005` y `security.W021` silenciados en producción: el dominio es un subdominio de `onrender.com` que no controlamos y el preload de HSTS es difícil de revertir. Se revisa si se usa un dominio propio.
- Frontend: el umbral de 80 % aplica a líneas y sentencias; funciones y ramas se informan.

- [x] **Paso 4: Commit**

```bash
git add docs/adr
git commit -m "docs: add architecture decision records"
```

#### Tarea 8: `CLAUDE.md` y `README.md`

**Archivos:**
- Crear: `CLAUDE.md`
- Modificar: `README.md`

**Interfaces:**
- Consume: `.claude/aidlc/AIDLC.md` (Tarea 5), documentos de las Tareas 6 y 7.

- [x] **Paso 1: Escribir `CLAUDE.md`** con las secciones 0–9 de la sección "Gobernanza → CLAUDE.md" del spec, en español. Requisitos concretos:
  - Primera línea de contenido: el archivo es normativo y gana ante cualquier otra instrucción de estilo; la versión larga está en `docs/estandares-de-codigo.md`.
  - Política de idioma (spec, "Política de idioma").
  - §0 contiene la línea `@.claude/aidlc/AIDLC.md` sola, para que Claude Code la importe.
  - §3 lista las ocho reglas absolutas del spec y, para cada una, quién la hace cumplir: 1 → pre-commit `no-commit-to-branch` + protección de ramas; 2 y 3 → gitleaks (CI y pre-commit) + `.gitignore`; 4 → protección de ramas; 5 → revisión del PR + estándares; 6 → revisión del PR; 7 → revisión del PR + tests de concurrencia cuando exista `reservas`; 8 → revisión del PR + ADR.
  - §4 tabla de ramas y el ciclo de comandos:

```bash
git switch develop && git pull
git switch -c feature/inventario-capacidad-por-cartel
# trabajo...
ruff format . && ruff check . && mypy backend && pytest
cd frontend && npm run format:check && npm run lint && npm run typecheck && npm run test:coverage && npm run build
git commit -m "feat(inventario): allow capacity override per poster"
# PR a develop con la plantilla completa
```

  - §7 Definition of Done: ruff, mypy, pytest con coverage, gates de frontend, gitleaks, `makemigrations --check`, `.env.example` actualizado si hay variables nuevas, `reglas-de-negocio.md` actualizado si cambió una regla, ADR si hubo decisión técnica, plantilla de PR completa.
  - §8 reglas para agentes (las cinco del spec) y: "nunca bajar un umbral ni excluir archivos para que pase CI".
  - §9 comandos de instalación (`py -3.12 -m venv .venv`, `pip install -r requirements-dev.txt`, `pip install -e backend/`, `pre-commit install`, `npm ci --prefix frontend`) y de verificación.

- [x] **Paso 2: Reducir `README.md`** a: qué es el sistema (dos oraciones), estado actual (inventario disponible; reservas no implementadas), cómo arrancar (enlace a `docs/operacion/desarrollo-local.md`), cómo se trabaja (enlaces a `CLAUDE.md`, `docs/README.md`, `docs/aidlc/roadmap.md`) y la nota sobre el PDF privado y el documento original de historias fuera de Git.

- [x] **Paso 3: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "docs: add repository constitution"
```

#### Tarea 9: Plantillas de GitHub

**Archivos:**
- Modificar: `.github/pull_request_template.md`
- Crear: `.github/ISSUE_TEMPLATE/pedido.yml`, `.github/ISSUE_TEMPLATE/config.yml`

- [x] **Paso 1: `.github/pull_request_template.md`**

```markdown
## Descripción

<!-- Qué resuelve este PR y por qué. -->

Closes #

## Módulos afectados

- [ ] `usuarios` — [ ] `inventario` — [ ] `clientes` — [ ] `campanias`
- [ ] `reservas` — [ ] `costos` — [ ] `facturacion` — [ ] `auditoria`
- [ ] `frontend` — [ ] `infra` — [ ] `docs`

## Tipo de cambio

- [ ] `feature/` — funcionalidad nueva
- [ ] `fix/` — corrección
- [ ] `docs/` — documentación, historias o reglas
- [ ] `chore/` — mantenimiento o configuración
- [ ] `hotfix/` — urgencia en `main`

## Reglas de negocio

- Reglas que este PR aplica o cambia: <!-- RN-xxx, o "ninguna" -->
- [ ] Si cambió una regla, se actualizó `docs/aidlc/reglas-de-negocio.md` (y el registro de cambios si cambió una historia)
- [ ] Los tests nuevos que verifican una regla llevan `@pytest.mark.regla("RN-xxx")`

## Definition of Done

- [ ] `ruff format --check . && ruff check .`
- [ ] `mypy backend`
- [ ] `pytest` en verde y coverage ≥ 80 %
- [ ] `python backend/manage.py makemigrations --check --dry-run`
- [ ] Frontend: `format:check`, `lint`, `typecheck`, `test:coverage`, `build`
- [ ] La rama sigue el formato y apunta a la base correcta
- [ ] Los commits siguen Conventional Commits

## Seguridad

- [ ] Sin credenciales, tokens ni secretos en el código
- [ ] Sin datos personales reales (ni en código, ni en tests, ni en logs)
- [ ] Si hay variables nuevas, se actualizó `backend/.env.example`

## Calidad y decisiones

- [ ] Tests agregados o actualizados
- [ ] Si es un bug, incluye primero el test que lo reproduce
- [ ] Si hubo una decisión técnica, hay ADR en `docs/adr/`
- [ ] No se desactivó ninguna regla para pasar CI

## Cómo se verificó

<!-- Comandos y resultado, o capturas para cambios de interfaz. -->
```

- [x] **Paso 2: `.github/ISSUE_TEMPLATE/pedido.yml`**

```yaml
name: Pedido de Seba
description: Algo que Seba pidió, reportó o comentó por WhatsApp o en una llamada.
title: "[Pedido] "
labels: ["pedido"]
body:
  - type: input
    id: fecha
    attributes:
      label: Fecha del pedido
      placeholder: "2026-10-20"
    validations:
      required: true
  - type: dropdown
    id: canal
    attributes:
      label: Canal
      options:
        - WhatsApp
        - Llamada
        - Reunión
        - Lo vio usando el sistema
    validations:
      required: true
  - type: textarea
    id: pedido
    attributes:
      label: Qué pidió, con sus palabras
      description: Copiá el mensaje o resumí lo que dijo. Sin datos personales de clientes.
    validations:
      required: true
  - type: input
    id: pantalla
    attributes:
      label: Pantalla o proceso afectado
      placeholder: "Carteles, catálogos, reservas…"
  - type: dropdown
    id: urgencia
    attributes:
      label: Urgencia
      options:
        - Le impide trabajar
        - Le molesta pero puede seguir
        - Idea para más adelante
    validations:
      required: true
  - type: textarea
    id: adjuntos
    attributes:
      label: Capturas o adjuntos
      description: Arrastrá capturas acá si las mandó.
```

- [x] **Paso 3: `.github/ISSUE_TEMPLATE/config.yml`**

```yaml
blank_issues_enabled: true
```

- [x] **Paso 4: Validar el YAML**

```bash
python -c "import yaml,sys; [yaml.safe_load(open(p, encoding='utf-8')) for p in sys.argv[1:]]; print('YAML válido')" .github/ISSUE_TEMPLATE/pedido.yml .github/ISSUE_TEMPLATE/config.yml
```

Esperado: `YAML válido`.

- [x] **Paso 5: Commit**

```bash
git add .github
git commit -m "docs: add pull request and issue templates"
```

#### Tarea 10: Verificación del PR 1

**Archivos:** ninguno nuevo.

- [x] **Paso 1: Verificar enlaces relativos en todo el Markdown**

```bash
python - <<'EOF'
import re, pathlib, sys
roto = 0
for md in pathlib.Path('.').rglob('*.md'):
    if 'node_modules' in md.parts or '.git' in md.parts:
        continue
    for destino in re.findall(r'\]\(([^)#\s]+)', md.read_text(encoding='utf-8')):
        if re.match(r'[a-z]+:', destino):
            continue
        if not (md.parent / destino).exists():
            print(f'{md}: enlace roto -> {destino}')
            roto = 1
sys.exit(roto)
EOF
```

Esperado: sin salida y código 0. Corregir cada enlace roto y volver a correr.

- [x] **Paso 2: Verificar que no quedaron carpetas viejas ni código tocado**

```bash
ls docs
git diff --stat develop -- backend frontend
```

Esperado: `docs` contiene solo `README.md`, `adr`, `aidlc`, `arquitectura.md`, `estandares-de-codigo.md`, `gestion-de-configuracion.md`, `operacion`, `superpowers` (solo con el patch). El diff de `backend` y `frontend` está vacío.

- [ ] **Paso 3: Completar "Próximas" del roadmap** preguntándole a Juan Diego qué épica sigue (ver Tarea 4, Paso 3) y commitear:

```bash
git add docs/aidlc/roadmap.md
git commit -m "docs: set next epics in roadmap"
```

- [ ] **Paso 4: Gate 2.** Mostrar a Juan Diego la salida de los pasos 1 y 2 y esperar su OK.

- [ ] **Paso 5: Gate 3, push y PR** (cuando lo pida):

```bash
git push -u origin docs/reestructura-gobernanza
gh pr create --base develop --title "docs: restructure repository governance" --body-file - <<'EOF'
## Descripción

Primera parte de la reestructura (unidad `reestructura-del-repositorio`): CLAUDE.md, documentos de
arquitectura, estándares y configuración, ADRs 0001–0004, workflow AI-DLC adaptado, catálogo de
reglas de negocio y migración de la documentación existente a `docs/aidlc/`.

No cambia código. El CI nuevo y los gates estrictos llegan en el PR `chore/gates-de-calidad`.
EOF
```

---

### PR 2 — `chore/gates-de-calidad` → `develop`

> Empezar después de mergear el PR 1. No abrir ramas de funcionalidad hasta mergear este PR: van a fallar los gates nuevos.

#### Tarea 11: Configuración de herramientas

**Archivos:**
- Crear: `pyproject.toml`, `requirements-dev.txt`, `.pre-commit-config.yaml`, `.gitleaks.toml`
- Modificar: `backend/pyproject.toml`, `.gitignore`

**Interfaces:**
- Produce: marcador `regla(id)`, configuración de pytest en la raíz (las Tareas 12–16 corren `pytest` desde la raíz).

- [ ] **Paso 1: Crear la rama**

```bash
git switch develop && git pull
git switch -c chore/gates-de-calidad
```

- [ ] **Paso 2: `pyproject.toml` (raíz)**

```toml
# Configuración de las herramientas de Python para todo el repositorio.
# Las reglas están explicadas en docs/estandares-de-codigo.md y ADR-0004.
# Las dependencias de la aplicación viven en backend/pyproject.toml.

[tool.ruff]
target-version = "py312"
line-length = 100
# Las migraciones son código generado por Django.
extend-exclude = ["frontend/node_modules", "**/migrations"]

[tool.ruff.lint]
select = [
    "E", "W",   # pycodestyle
    "F",        # pyflakes
    "I",        # orden de imports
    "UP",       # sintaxis moderna
    "B",        # bugbear
    "S",        # seguridad (bandit)
    "ANN",      # anotaciones de tipos
    "PT",       # pytest
    "C90",      # complejidad ciclomática
    "SIM",      # simplificaciones
    "RET",      # returns
    "ARG",      # argumentos sin usar
    "PTH",      # pathlib
    "DTZ",      # fechas sin zona horaria
    "T20",      # sin print()
    "BLE",      # sin except Exception
    "RUF",      # reglas propias de ruff
    "DJ",       # Django
    "PGH",       # sin noqa ni type: ignore generales (ADR-0004)
]
ignore = [
    "ANN401",   # Any solo en los bordes del sistema
    "E501",     # el largo de línea lo maneja el formateador
    "RUF012",   # Django y DRF declaran listas como atributos de clase (ADR-0004)
]

[tool.ruff.lint.per-file-ignores]
# S603: los tests de settings de producción lanzan sys.executable en un subproceso.
"**/tests/**/*.py" = ["S101", "S105", "S106", "S603", "ANN001", "ANN201", "ARG001"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true
show_error_codes = true
pretty = true
mypy_path = "backend"
explicit_package_bases = true
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
exclude = ['/migrations/']
enable_error_code = ["ignore-without-code"]

[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
disallow_untyped_calls = false

[tool.django-stubs]
django_settings_module = "config.settings"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
pythonpath = ["backend"]
testpaths = ["backend/tests"]
python_files = ["test_*.py"]
addopts = ["--strict-markers", "--strict-config", "-ra"]
markers = [
    "regla(id): verifica la regla de negocio RN-xxx de docs/aidlc/reglas-de-negocio.md",
]

[tool.coverage.run]
branch = true
source = ["backend"]
omit = [
    "backend/tests/*",
    "*/migrations/*",
    "backend/manage.py",
    "backend/config/asgi.py",
    "backend/config/wsgi.py",
]

[tool.coverage.report]
# Mínimo del proyecto. Bajarlo requiere un ADR (ADR-0004).
fail_under = 80
show_missing = true
skip_covered = true
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "raise NotImplementedError"]
```

- [ ] **Paso 3: `requirements-dev.txt`**

```text
# Herramientas de desarrollo y CI (no son dependencias de la aplicación).
# Versiones fijas: CI y todas las máquinas ven exactamente lo mismo.
# Actualizarlas es un cambio deliberado, en su propio PR.

ruff==0.14.2
mypy==1.18.2
django-stubs==6.1.2
django-stubs-ext==6.1.2
djangorestframework-stubs==3.18.1
types-PyYAML==6.0.12.20260906
pytest==9.1.1
pytest-django==4.14.0
pytest-cov==7.1.0
PyYAML==6.0.3
pre-commit==4.7.0
```

- [ ] **Paso 4: Reducir `backend/pyproject.toml`**: borrar la sección `[project.optional-dependencies]` y la sección `[tool.pytest.ini_options]`. El resto queda igual.

- [ ] **Paso 5: `.gitleaks.toml`**

```toml
# Detección de credenciales (CI y pre-commit). Extiende las reglas por defecto.
[extend]
useDefault = true

[allowlist]
description = "Plantillas, documentación y valores de prueba que no son secretos."
paths = ['''\.env\.example$''', '''.*\.md$''']
regexes = ['''test-only-[A-Za-z0-9-]+''', '''solo-pruebas[A-Za-z0-9-]*''', '''replace-with-local-[a-z-]+''']
```

- [ ] **Paso 6: `.pre-commit-config.yaml`**

```yaml
# Controles antes de cada commit. Son un subconjunto de los del CI: detectar un problema acá
# cuesta segundos; en el PR cuesta una vuelta de revisión. mypy corre solo en CI (con los stubs
# de Django es lento). Instalación, una vez: pre-commit install
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
        exclude: ^frontend/tsconfig.*\.json$   # tsconfig admite comentarios
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: check-added-large-files
        args: [--maxkb=1000]
      - id: detect-private-key
      - id: no-commit-to-branch
        args: [--branch, main, --branch, develop]
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.2
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
```

- [ ] **Paso 7: `.gitignore`**: agregar al final

```text
.venv/
.coverage
coverage.xml
frontend/coverage/
```

- [ ] **Paso 8: Instalar y probar la configuración**

```bash
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt -e backend/
.venv/Scripts/pre-commit.exe run check-toml --all-files
.venv/Scripts/pre-commit.exe run gitleaks --all-files
```

Esperado: ambos `Passed`. Si gitleaks marca un valor de prueba que no está cubierto por las expresiones de la allowlist, agregar una expresión específica para ese valor (nunca una ruta completa de código) y volver a correr.

- [ ] **Paso 9: Commit**

```bash
git add pyproject.toml requirements-dev.txt backend/pyproject.toml .gitleaks.toml .pre-commit-config.yaml .gitignore
git commit -m "chore(infra): add shared Python tooling configuration"
```

#### Tarea 12: Tests siempre contra PostgreSQL y `.env` en `backend/`

**Archivos:**
- Mover: `.env.example` → `backend/.env.example`
- Modificar: `backend/config/settings.py`, `compose.yaml`, `backend/tests/test_postgres_integration.py`, `docs/operacion/desarrollo-local.md`
- Crear: `backend/tests/test_settings.py`, `backend/tests/README.md`

**Interfaces:**
- Produce: `config.settings.ENV_FILE: Path` (ruta del `.env` que lee Django).

- [ ] **Paso 1: Escribir el test que falla** — `backend/tests/test_settings.py`

```python
"""Django reads its environment file from backend/, next to the process that uses it."""

from pathlib import Path

from django.conf import settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_settings_lee_backend_env():
    assert settings.ENV_FILE == BACKEND_DIR / ".env"
```

- [ ] **Paso 2: Correrlo y ver que falla**

Run: `.venv/Scripts/python.exe -m pytest backend/tests/test_settings.py -q`
Esperado: FAIL con `AttributeError: 'Settings' object has no attribute 'ENV_FILE'`.

- [ ] **Paso 3: Cambiar `backend/config/settings.py`**

Reemplazar:

```python
load_dotenv(BASE_DIR.parent / ".env")
```

por:

```python
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)
```

Y dentro del bloque `if PRODUCTION:` que define `SECURE_HSTS_SECONDS`, agregar al final:

```python
    # El dominio es un subdominio de onrender.com que no controlamos y el preload de HSTS es
    # difícil de revertir. Revisar si se usa un dominio propio (ADR-0004).
    SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W021"]
```

- [ ] **Paso 4: Mover el ejemplo y actualizar Compose**

```bash
git mv .env.example backend/.env.example
```

`compose.yaml`:

```yaml
services:
  db:
    image: postgres:17-alpine
    env_file: backend/.env
    ports:
      - "127.0.0.1:5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  postgres_data:
```

Mover el `.env` local: `Move-Item .env backend/.env` (no se commitea).

- [ ] **Paso 5: Quitar el flag del test de integración** — en `backend/tests/test_postgres_integration.py` borrar el decorador `@pytest.mark.skipif(...)` completo y el `import os` si queda sin usar.

- [ ] **Paso 6: Correr los tests**

```bash
docker compose up -d --wait db
.venv/Scripts/python.exe -m pytest backend/tests/test_settings.py backend/tests/test_postgres_integration.py -q
.venv/Scripts/python.exe -m pytest -q
```

Esperado: todo en verde y **ningún** `skipped` en el resumen.

- [ ] **Paso 7: Verificar `check --deploy`**

```bash
cd backend
$env:DJANGO_ENV='production'; $env:DJANGO_SECRET_KEY='test-only-production-secret-key-with-enough-characters'; $env:RENDER_EXTERNAL_HOSTNAME='bigmedia.onrender.com'; $env:DATABASE_URL='postgresql://u:p@localhost:5432/x'
..\.venv\Scripts\python.exe manage.py check --deploy --fail-level WARNING
Remove-Item Env:DJANGO_ENV, Env:DJANGO_SECRET_KEY, Env:RENDER_EXTERNAL_HOSTNAME, Env:DATABASE_URL
```

Esperado: `System check identified no issues (2 silenced).`

- [ ] **Paso 8: Actualizar `docs/operacion/desarrollo-local.md`**
  - `Copy-Item backend/.env.example backend/.env` en lugar del `.env` de la raíz, y una nota: "Si tenías un `.env` en la raíz de una versión anterior, movelo a `backend/.env`; la raíz ya no se lee."
  - Instalación: `py -3.12 -m venv .venv`, `.venv/Scripts/python.exe -m pip install -r requirements-dev.txt -e backend/`, `.venv/Scripts/pre-commit.exe install`.
  - Tests: `docker compose up -d --wait db` y `.venv/Scripts/python.exe -m pytest` desde la raíz; borrar la sección de `BIGMEDIA_RUN_DB_TESTS`; explicar que sin la base la suite se detiene con un mensaje.
  - Verificación completa: los comandos de la Definition of Done de `CLAUDE.md`.

- [ ] **Paso 9: `backend/tests/README.md`**: convenciones de tests (siempre PostgreSQL; sin red; nombre `test_<qué>_<condición>_<resultado>` en tests nuevos; marcador `regla`; todo bug empieza con su test; coverage 80 %; fixtures comunes en `conftest.py`).

- [ ] **Paso 10: Commit**

```bash
git add -A backend/.env.example .env.example backend/config/settings.py compose.yaml backend/tests docs/operacion/desarrollo-local.md
git commit -m "chore(infra): always test against PostgreSQL and read backend env file"
```

#### Tarea 13: Arreglos de ruff y mypy, y guarda de PostgreSQL

**Archivos:**
- Modificar: `backend/apps/inventario/{models,serializers,views,urls}.py`, `backend/config/{asgi,auth_views,health,settings,wsgi}.py`, `backend/manage.py`, `backend/tests/{conftest,test_carteles,test_inventory_catalogs,test_production_settings,test_render_blueprint}.py`
- Crear: `backend/tests/test_guardia_postgres.py`, `frontend/src/app/Login.test.tsx`
- Eliminar: `docs/superpowers/` (el patch)

**Interfaces:**
- Consume: `docs/superpowers/plans/2026-10-16-reestructura-repo-arreglos.patch` de la rama `docs/reestructura-repo` (verificado el 17/10/2026 contra `main` + las tres ramas: ruff y mypy en cero, 37 tests en verde contra PostgreSQL 17, coverage de backend 92 %, frontend 80,8 % de sentencias y 88,6 % de líneas).

- [ ] **Paso 1: Escribir primero el test de la guarda** — `backend/tests/test_guardia_postgres.py`

```python
"""Without PostgreSQL the suite stops with a clear message instead of skipping tests."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_suite_stops_when_postgresql_is_unreachable():
    env = {**os.environ, "DB_HOST": "127.0.0.1", "DB_PORT": "1"}

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "backend/tests/test_health.py", "-q"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 3
    assert "PostgreSQL no está disponible" in result.stdout + result.stderr
```

- [ ] **Paso 2: Correrlo y ver que falla**

Run: `.venv/Scripts/python.exe -m pytest backend/tests/test_guardia_postgres.py -q`
Esperado: FAIL en `assert result.returncode == 3`: sin guarda, la corrida interna termina con otro código (0 o 1) y sin el mensaje.

- [ ] **Paso 3: Aplicar el patch verificado**

```bash
git show docs/reestructura-repo:docs/superpowers/plans/2026-10-16-reestructura-repo-arreglos.patch > ../arreglos.patch
git apply --ignore-whitespace --whitespace=nowarn --exclude=backend/tests/test_guardia_postgres.py --exclude=backend/config/settings.py ../arreglos.patch
```

Se excluyen dos archivos: `test_guardia_postgres.py`, que ya se escribió en el paso 1, y `settings.py`, que la Tarea 12 ya modificó y haría fallar el contexto del patch. En `backend/config/settings.py` aplicar a mano los dos cambios del patch: agregar `from typing import Any` a los imports y anotar `DATABASES: dict[str, Any] = {`. El orden de imports lo corrige `ruff check --fix .`.

Si `git apply` rechaza otro archivo porque cambió desde el 17/10, aplicarlo a mano siguiendo los fragmentos de abajo y las decisiones de configuración de la Tarea 7.

Fragmentos clave que contiene el patch:

`backend/tests/conftest.py`:

```python
import psycopg
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client


def pytest_sessionstart(session: pytest.Session) -> None:
    """Stop the run when PostgreSQL is unreachable instead of failing test by test."""
    database = settings.DATABASES["default"]
    try:
        psycopg.connect(
            dbname=database["NAME"],
            user=database["USER"],
            password=database["PASSWORD"],
            host=database["HOST"],
            port=database["PORT"],
            connect_timeout=3,
        ).close()
    except psycopg.OperationalError as error:
        pytest.exit(
            "PostgreSQL no está disponible. Levantalo con `docker compose up -d db` "
            f"y revisá backend/.env. Detalle: {error}",
            returncode=3,
        )


@pytest.fixture
def operativo_client(db):
    user = get_user_model().objects.create_user(username="operativo", password="clave-segura-123")
    user.groups.add(Group.objects.get(name="Operativo"))
    client = Client()
    client.force_login(user)
    return client
```

> La guarda usa `psycopg` directo porque pytest-django bloquea `django.db.connection` fuera de los tests (`RuntimeError: Database access not allowed`).

`backend/apps/inventario/views.py` (cabecera y bases):

```python
from typing import Any

from django.db.models import QuerySet
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.views import APIView

# ...imports de models y serializers sin cambios...


class PuedeOperarInventario(permissions.BasePermission):
    def has_permission(self, request: Request, _view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_superuser or request.user.groups.filter(name="Operativo").exists()


class InventarioViewSet(viewsets.ModelViewSet[Any]):
    permission_classes = [permissions.IsAuthenticated, PuedeOperarInventario]
    http_method_names = ["get", "post", "patch", "head", "options"]


class CatalogoViewSet(InventarioViewSet):
    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        if self.action == "list" and self.request.query_params.get("incluir_inactivos") != "1":
            queryset = queryset.filter(activo=True)
        return queryset
```

`CartelViewSet` pasa a heredar de `InventarioViewSet` y su `get_queryset(self) -> QuerySet[Any]` empieza con `queryset = super().get_queryset()`.

`backend/apps/inventario/serializers.py`: `CatalogoSerializer(serializers.ModelSerializer[Catalogo])` con `model = cast(type[Catalogo], self.Meta.model)` y `model._default_manager.filter(...)`; `CartelSerializer(serializers.ModelSerializer[Cartel])`; validadores anotados (`value: str -> str`, `value: int -> int`, `attrs: dict[str, Any] -> dict[str, Any]`, `create(... ) -> Cartel`).

`backend/apps/inventario/models.py`: `__str__ -> str`, `save(self, *args: Any, **kwargs: Any) -> None`, `nombre_visible -> str`; en `Cartel`, orden `__str__`, `save`, `nombre_visible` (regla `DJ012`).

`backend/config/auth_views.py` y `health.py`: `request: HttpRequest`, retorno `JsonResponse`, `get_username()` en lugar de `.username`, `_request` en `health`. `settings.py`: `DATABASES: dict[str, Any]`. Tests: aserciones compuestas separadas (`PT018`), `("changes", "field")` en `parametrize` (`PT006`), `**changes: object`.

- [ ] **Paso 4: Marcar un test con su regla** — en `backend/tests/test_carteles.py`, sobre `test_cartel_inherits_capacity_and_shows_readable_name`, agregar `@pytest.mark.regla("RN-005")` debajo de `@pytest.mark.django_db`.

- [ ] **Paso 5: Correr todos los gates de Python**

```bash
docker compose up -d --wait db
.venv/Scripts/ruff.exe format --check .
.venv/Scripts/ruff.exe check .
.venv/Scripts/mypy.exe backend
.venv/Scripts/python.exe backend/manage.py makemigrations --check --dry-run
.venv/Scripts/python.exe -m pytest --cov --cov-report=term-missing
.venv/Scripts/python.exe -m pytest -m regla -q
```

Esperado: ruff `All checks passed!`; mypy `Success: no issues found`; `No changes detected`; todos los tests en verde (incluido `test_guardia_postgres`), ninguno salteado, `Required test coverage of 80% reached`; la última corrida selecciona 1 test.

- [ ] **Paso 6: Borrar el patch y `docs/superpowers/`**

```bash
git rm -r docs/superpowers
```

- [ ] **Paso 7: Commit**

```bash
git add -A backend frontend/src/app/Login.test.tsx docs
git commit -m "refactor: pass strict lint and type checks"
```

#### Tarea 14: Gates del frontend

**Archivos:**
- Crear: `frontend/.prettierrc.json`, `frontend/.prettierignore`
- Modificar: `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.ts`, `frontend/tsconfig.app.json`, `frontend/tsconfig.node.json`, todos los archivos de `frontend/src/` (formato)

**Interfaces:**
- Produce: scripts `npm run format:check`, `npm run typecheck`, `npm run test:coverage` (los usa el CI de la Tarea 15).

- [ ] **Paso 1: Dependencias**

```bash
cd frontend
npm install --save-dev --save-exact prettier@3.9.10
npm install --save-dev @vitest/coverage-v8@5.0.4
```

- [ ] **Paso 2: `frontend/.prettierrc.json`** (respeta el estilo actual: sin punto y coma, comillas simples)

```json
{
  "semi": false,
  "singleQuote": true,
  "printWidth": 100,
  "trailingComma": "all"
}
```

`frontend/.prettierignore`:

```text
dist
coverage
node_modules
package-lock.json
```

- [ ] **Paso 3: Scripts en `frontend/package.json`** (dentro de `"scripts"`, conservando los existentes)

```json
"typecheck": "tsc -b",
"format": "prettier --write .",
"format:check": "prettier --check .",
"test:coverage": "vitest run --coverage"
```

- [ ] **Paso 4: Umbral de coverage en `frontend/vite.config.ts`**

```ts
  test: {
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      // Líneas y sentencias son obligatorias; funciones y ramas se informan (ADR-0004).
      thresholds: { lines: 80, statements: 80 },
    },
  },
```

- [ ] **Paso 5: `"strict": true` explícito** al principio de la sección `/* Linting */` de `tsconfig.app.json` y de `tsconfig.node.json`.

- [ ] **Paso 6: Formatear y correr todo**

```bash
npm run format
npm run format:check
npm run lint
npm run typecheck
npm run test:coverage
npm run build
```

Esperado: todo en verde; coverage ≥ 80 % en sentencias (medido 80,8 %) y en líneas (88,6 %). Si sentencias queda por debajo de 80 % después de formatear, agregar un test a `CatalogosPage` (es el archivo con menos cobertura) y volver a medir; no bajar el umbral.

- [ ] **Paso 7: Commit**

```bash
cd ..
git add frontend
git commit -m "chore(frontend): add formatting, type and coverage gates"
```

#### Tarea 15: CI

**Archivos:**
- Crear: `.github/scripts/validar_convenciones.sh`, `.github/scripts/test_validar_convenciones.sh`
- Modificar: `.github/workflows/ci.yml`

**Interfaces:**
- Consume: scripts de frontend (Tarea 14), configuración de la Tarea 11.

- [ ] **Paso 1: Escribir el test del script** — `.github/scripts/test_validar_convenciones.sh`

```bash
#!/usr/bin/env bash
# Prueba validar_convenciones.sh. Lo corre el job `convenciones` antes de usarlo.
set -uo pipefail
script="$(dirname "$0")/validar_convenciones.sh"
fallos=0

acepta() { bash "$script" "$@" >/dev/null || { echo "Debía aceptar: $*"; fallos=1; }; }
rechaza() { ! bash "$script" "$@" >/dev/null || { echo "Debía rechazar: $*"; fallos=1; }; }

acepta rama feature/inventario-capacidad-por-cartel develop
acepta rama fix/reservas-dia-de-borde develop
acepta rama docs/historias-cancelacion develop
acepta rama chore/gates-de-calidad develop
acepta rama hotfix/login-caido main
acepta rama develop main
rechaza rama feature/capacidad develop
rechaza rama feature/ventas-algo develop
rechaza rama feature/inventario-capacidad main
rechaza rama hotfix/login-caido develop
rechaza rama docs/Historias develop
rechaza rama feat/inventario develop
rechaza rama main develop

acepta commit "feat(inventario): add poster capacity override"
acepta commit "docs: migrate requirements to aidlc inputs"
acepta commit "Merge pull request #12 from jdcaballero15/feature/x"
rechaza commit "WIP"
rechaza commit "feat(ventas): add something long enough"
rechaza commit "feat: corto"
rechaza commit "Feat(inventario): add poster capacity override"

[ "$fallos" -eq 0 ] && echo "validar_convenciones.sh: todos los casos pasan."
exit "$fallos"
```

- [ ] **Paso 2: Correrlo y ver que falla**

Run: `bash .github/scripts/test_validar_convenciones.sh`
Esperado: FAIL, con líneas "Debía aceptar…" (el script todavía no existe).

- [ ] **Paso 3: Escribir `.github/scripts/validar_convenciones.sh`**

```bash
#!/usr/bin/env bash
# Reglas de ramas y commits de CLAUDE.md §4 y §6. Lo usa el job `convenciones` del CI.
#
#   validar_convenciones.sh rama <rama> <destino>
#   validar_convenciones.sh commit "<asunto del commit>"
set -euo pipefail

MODULOS='usuarios|inventario|clientes|campanias|reservas|costos|facturacion|auditoria|frontend|infra|docs'
KEBAB='[a-z0-9]+(-[a-z0-9]+)*'

validar_rama() {
  local rama="$1" destino="$2"
  if [[ "$rama" =~ ^(feature|fix)/($MODULOS)-$KEBAB$ ]] \
    || [[ "$rama" =~ ^(docs|chore)/$KEBAB$ ]]; then
    [[ "$destino" == "develop" ]] && return 0
    echo "La rama '$rama' solo puede apuntar a develop (apunta a $destino)."
    return 1
  fi
  if [[ "$rama" =~ ^hotfix/$KEBAB$ ]]; then
    [[ "$destino" == "main" ]] && return 0
    echo "La rama '$rama' solo puede apuntar a main (apunta a $destino)."
    return 1
  fi
  if [[ "$rama" == "develop" && "$destino" == "main" ]]; then
    return 0
  fi
  echo "La rama '$rama' no sigue el formato. Usá feature/<modulo>-<descripcion>,"
  echo "fix/<modulo>-<descripcion>, docs/<descripcion>, chore/<descripcion> o hotfix/<descripcion>."
  return 1
}

validar_commit() {
  local asunto="$1"
  [[ "$asunto" == "Merge "* ]] && return 0
  if [[ "$asunto" =~ ^(feat|fix|docs|refactor|test|chore|perf|ci)(\(($MODULOS)\))?:\ .{10,}$ ]]; then
    return 0
  fi
  echo "Commit inválido: '$asunto'. Formato: <tipo>(<modulo>): <descripción> (CLAUDE.md §6)."
  return 1
}

case "${1:-}" in
  rama) validar_rama "$2" "$3" ;;
  commit) validar_commit "$2" ;;
  *) echo "Uso: $0 rama <rama> <destino> | commit <asunto>"; exit 2 ;;
esac
```

- [ ] **Paso 4: Correr el test y ver que pasa**

Run: `bash .github/scripts/test_validar_convenciones.sh`
Esperado: `validar_convenciones.sh: todos los casos pasan.`

- [ ] **Paso 5: Reescribir `.github/workflows/ci.yml`**

```yaml
name: CI

# Se ejecuta en cada PR y push a develop y main. Un PR no se puede mergear si falla un job.
# Las reglas están en CLAUDE.md y docs/estandares-de-codigo.md; las versiones de las
# herramientas, en requirements-dev.txt.

on:
  pull_request:
    branches: [develop, main]
  push:
    branches: [develop, main]

permissions:
  contents: read

defaults:
  run:
    shell: bash

env:
  PYTHON_VERSION: "3.12"
  NODE_VERSION: "24"

jobs:
  convenciones:
    name: Convenciones (rama y commits)
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Probar el validador
        run: bash .github/scripts/test_validar_convenciones.sh
      - name: Validar nombre y destino de la rama
        env:
          RAMA: ${{ github.head_ref }}
          DESTINO: ${{ github.base_ref }}
        run: |
          bash .github/scripts/validar_convenciones.sh rama "$RAMA" "$DESTINO" \
            || { echo "::error::Nombre o destino de rama inválido."; exit 1; }
      - name: Validar los commits
        env:
          BASE: ${{ github.event.pull_request.base.sha }}
          HEAD: ${{ github.event.pull_request.head.sha }}
        run: |
          fallos=0
          while IFS= read -r asunto; do
            [ -n "$asunto" ] || continue
            bash .github/scripts/validar_convenciones.sh commit "$asunto" \
              || { echo "::error::$asunto"; fallos=1; }
          done < <(git log --format=%s "$BASE..$HEAD")
          exit "$fallos"

  lint-python:
    name: Lint Python (ruff)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
          cache-dependency-path: requirements-dev.txt
      - run: pip install -r requirements-dev.txt
      - run: ruff format --check --diff .
      - run: ruff check --output-format=github .

  tipos:
    name: Tipos (mypy --strict)
    runs-on: ubuntu-latest
    env:
      # El plugin de django-stubs importa los settings.
      DJANGO_SECRET_KEY: test-only-ci-secret-key-with-enough-characters-123456789
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
          cache-dependency-path: requirements-dev.txt
      - run: pip install -r requirements-dev.txt -e backend/
      - run: mypy backend

  check-deploy:
    name: Configuración de producción (check --deploy)
    runs-on: ubuntu-latest
    env:
      DJANGO_ENV: production
      DJANGO_SECRET_KEY: test-only-production-secret-key-with-enough-characters-123
      RENDER_EXTERNAL_HOSTNAME: bigmedia.onrender.com
      DATABASE_URL: postgresql://test-only:test-only@localhost:5432/test-only
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
          cache-dependency-path: backend/pyproject.toml
      - run: pip install -e backend/
      - run: python backend/manage.py check --deploy --fail-level WARNING

  tests-backend:
    name: Tests backend (PostgreSQL)
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_DB: bigmedia_test
          POSTGRES_USER: bigmedia_test
          POSTGRES_PASSWORD: test-only-ci-password
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U bigmedia_test -d bigmedia_test"
          --health-interval 5s --health-timeout 3s --health-retries 10
    env:
      DJANGO_SECRET_KEY: test-only-ci-secret-key-with-enough-characters-123456789
      DJANGO_DEBUG: "false"
      POSTGRES_DB: bigmedia_test
      POSTGRES_USER: bigmedia_test
      POSTGRES_PASSWORD: test-only-ci-password
      DB_HOST: 127.0.0.1
      DB_PORT: "5432"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
          cache-dependency-path: requirements-dev.txt
      - run: pip install -r requirements-dev.txt -e backend/
      - name: Verificar que no faltan migraciones
        run: python backend/manage.py makemigrations --check --dry-run
      - name: Tests y coverage
        run: pytest --cov --cov-report=term-missing | tee pytest.txt
      - name: Verificar que no se salteó ningún test
        run: |
          if grep -qE "[0-9]+ skipped" pytest.txt; then
            echo "::error::Hay tests salteados. En CI todos deben correr contra PostgreSQL."
            exit 1
          fi

  frontend:
    name: Frontend
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run format:check
      - run: npm run lint
      - run: npm run typecheck
      - run: npm run test:coverage
      - run: npm run build

  secretos:
    name: Credenciales (gitleaks)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Instalar gitleaks
        run: |
          VERSION=8.21.2
          curl -sSfL "https://github.com/gitleaks/gitleaks/releases/download/v${VERSION}/gitleaks_${VERSION}_linux_x64.tar.gz" \
            | tar -xz gitleaks
          sudo mv gitleaks /usr/local/bin/
      - run: gitleaks detect --source . --no-git --redact -v

  imagen:
    name: Imagen de producción
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t bigmedia:ci .
```

- [ ] **Paso 6: Validar el YAML**

```bash
.venv/Scripts/python.exe -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml', encoding='utf-8')); print('YAML válido')"
.venv/Scripts/pre-commit.exe run check-yaml --all-files
```

Esperado: `YAML válido` y `Passed`.

- [ ] **Paso 7: Commit**

```bash
git add .github
git commit -m "ci: split pipeline into strict quality gates"
```

#### Tarea 16: Verificación final, PRs y release

- [ ] **Paso 1: Correr la verificación completa localmente**

```bash
docker compose up -d --wait db
.venv/Scripts/pre-commit.exe run --all-files
.venv/Scripts/ruff.exe format --check . && .venv/Scripts/ruff.exe check .
.venv/Scripts/mypy.exe backend
.venv/Scripts/python.exe backend/manage.py makemigrations --check --dry-run
.venv/Scripts/python.exe -m pytest --cov
bash .github/scripts/test_validar_convenciones.sh
cd frontend && npm run format:check && npm run lint && npm run typecheck && npm run test:coverage && npm run build && cd ..
docker build -t bigmedia:local .
```

Esperado: todo en verde. La primera corrida de `pre-commit run --all-files` puede corregir espacios finales o el fin de archivo en archivos viejos (por ejemplo, los CSV): revisar el diff, commitear con `chore: normalize whitespace` y volver a correr. Si `check-json` falla en un archivo JSON con comentarios (JSONC, como `.vscode/settings.json`), agregarlo al `exclude` de ese hook.

- [ ] **Paso 2: Prueba de humo de la guarda** — con la base apagada (`docker compose stop db`), `.venv/Scripts/python.exe -m pytest` debe terminar con el mensaje "PostgreSQL no está disponible…" y código 3. Volver a levantarla.

- [ ] **Paso 3: Gate 2.** Mostrar a Juan Diego la salida real de los pasos 1 y 2 y esperar su OK. Registrar el resultado en `docs/aidlc/units/reestructura-del-repositorio.md` (sección "Registro de gates") y commitear: `git commit -am "docs: record restructure verification"`.

- [ ] **Paso 4: Gate 3, push y PR** (cuando lo pida):

```bash
git push -u origin chore/gates-de-calidad
gh pr create --base develop --title "chore(infra): add strict quality gates" --body-file - <<'EOF'
## Descripción

Segunda parte de la reestructura: configuración compartida de ruff, mypy, pytest y coverage;
pre-commit y gitleaks; tests siempre contra PostgreSQL (con guarda); `.env` en `backend/`;
arreglos de tipado y lint; gates del frontend; CI dividido en jobs.

## Cómo se verificó

<pegar la salida de la Tarea 16, paso 1>
EOF
gh pr checks --watch
```

Esperado: todos los checks en verde. Si falla `convenciones` por el mensaje de un commit, no reescribir la historia por cuenta propia: informar a Juan Diego qué commit falla y que decida.

- [ ] **Paso 5: Configuración manual en GitHub** — pedirle a Juan Diego que siga la sección "Configuración manual en GitHub" de `docs/gestion-de-configuracion.md` (protección de ramas con los ocho jobs, `develop` como rama por defecto, etiquetas). El ejecutor puede ofrecer crear las etiquetas con `gh label create` si Juan Diego lo autoriza.

- [ ] **Paso 6: Release a producción** (cuando lo pida): actualizar el estado de la unidad a `mergeada` en `units.md` en un PR `docs/` corto, y después:

```bash
gh pr create --base main --head develop --title "chore: release repository restructure" --body "Integra la reestructura del repositorio (gobernanza + gates de calidad)."
```

Render despliega `main` solo con los checks en verde (`autoDeployTrigger: checksPass`).

## Registro de gates

- Gate 1 (plan): 2026-10-17 — aprobado por Juan Diego
- Gate 2 (verificación): pendiente
- Gate 3 (PR): pendiente
