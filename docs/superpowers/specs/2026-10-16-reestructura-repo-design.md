# Big Media — reestructura del repositorio

Estado: para revisión de Juan Diego, 16 de octubre de 2026.

## Propósito

Adoptar la organización del repositorio de referencia [CheatSheet](https://github.com/cheatsheet12/CheatSheet): gobernanza escrita, ADRs, CI con gates estrictos y un workflow de desarrollo con puntos de aprobación. La lógica de negocio de CheatSheet no aplica a Big Media; solo se toma su estructura, sus convenciones y su configuración.

Hay una diferencia de contexto que condiciona todo el diseño: CheatSheet parte de requisitos cerrados y trata las historias de usuario como insumo de solo lectura. En Big Media el relevamiento es incompleto y no hay tiempo para mejorarlo antes de construir. Las reglas de negocio, las historias y el alcance van a cambiar a medida que Seba use el sistema. Por eso se conserva lo que ayuda cuando todo cambia (CI estricto, tests, unidades chicas, ADRs técnicos) y se aligera lo que estorba (roadmap completo por adelantado, planes largos, historias inmutables).

## Alcance

**Se adopta**

- Gobernanza y documentación: `CLAUDE.md` normativo, documentos de arquitectura, estándares y gestión de configuración, ADRs, PR template y plantilla de issues.
- CI y calidad estrictos: ruff, mypy `--strict` con stubs de Django, coverage mínimo de 80 % en backend y frontend, gitleaks, pre-commit.
- Workflow AI-DLC adaptado a requisitos evolutivos.
- GitFlow con `develop`.

**No se adopta**

- Hooks de Claude Code (`.claude/hooks/`). El cumplimiento de reglas queda en CI, pre-commit y la protección de ramas de GitHub.
- Arquitectura hexagonal por bounded context. El backend sigue organizado como apps de Django.
- Entorno de staging. Queda documentado en ADR-0002 como el siguiente paso, sin implementar.

## Precondiciones

Antes de empezar, se integran a `main` las ramas en curso, en este orden y sin modificarlas:

1. `docs/decisiones-importacion-ux` (decisiones pendientes, plantillas de importación, recorrido de UX).
2. `feat/inventario` (app `inventario`, autenticación, PR template y `CONTRIBUTING.md`).
3. `chore/render-deploy` (Dockerfile, `render.yaml`, CI inicial, settings de producción).

Después se crea `develop` desde ese `main`. La reestructura parte de `develop` y absorbe lo que esas ramas agregaron: el CI, el PR template y `CONTRIBUTING.md` se reescriben; `docs/arquitectura/estructura-repo.md` se integra en `docs/arquitectura.md`.

## Entrega en dos PRs

1. **`docs/reestructura-gobernanza`** — gobernanza, ADRs, workflow AI-DLC, migración de documentos y plantillas de GitHub. Solo documentación y plantillas; no cambia código.
2. **`chore/gates-de-calidad`** — configuración de herramientas, CI nuevo y los arreglos de código necesarios para que el código existente pase los gates estrictos.

Ambos apuntan a `develop`. Al terminar, se abre el PR `develop` → `main`.

## Estructura resultante

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

### Movimientos de documentos

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

## Política de idioma

Todo el repositorio se escribe en español: `CLAUDE.md`, documentación, ADRs, PR template, plantillas de issues, descripciones de PR y mensajes de CI. Excepciones:

- **Commits:** Conventional Commits en inglés, como hasta ahora (`feat(inventario): add poster capacity override`). El tipo y el módulo son vocabulario fijo; mantener el resto en inglés conserva la coherencia con el historial.
- **Código:** identificadores técnicos en inglés cuando ya lo están; el lenguaje del dominio queda en español sin tildes (`Cartel`, `Reserva`, `Campania`, `Formato`), como ya hace la app `inventario`. No se renombra código existente.

## Gobernanza

### `CLAUDE.md`

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

### Apps y dependencias

Las apps de Django cumplen el rol de los bounded contexts de CheatSheet: `usuarios`, `inventario`, `clientes`, `campanias`, `reservas`, `costos`, `facturacion` y `auditoria`. `docs/arquitectura.md` declara qué app puede depender de cuál (por ejemplo, `reservas → inventario`, `reservas → campanias`). Una app no importa modelos de otra fuera de esas dependencias. Esto se revisa en el PR; ninguna herramienta lo verifica.

### Ramas (GitFlow)

| Tipo | Patrón | Destino |
|---|---|---|
| Funcionalidad | `feature/<modulo>-<descripcion>` | `develop` |
| Corrección | `fix/<modulo>-<descripcion>` | `develop` |
| Documentación | `docs/<descripcion>` | `develop` |
| Mantenimiento | `chore/<descripcion>` | `develop` |
| Emergencia | `hotfix/<descripcion>` | `main`, y después merge a `develop` |
| Release | `develop` | `main` |

`<descripcion>` va en kebab-case. Módulos válidos: los ocho nombres de app, más `frontend`, `infra` y `docs`. `main` es producción y despliega en Render; `develop` integra y solo corre CI.

### Commits

```
<tipo>(<modulo>): <qué hace el commit>
```

Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`. El módulo es opcional y, si está, es uno de los válidos. Mínimo 10 caracteres de descripción. CI rechaza los mensajes que no cumplen el formato, salvo los commits de merge de GitHub.

### PR template

En español, con estas secciones: descripción; issue que cierra (`Closes #N`); módulos afectados; tipo de cambio; reglas de negocio tocadas (RN-xxx) y si se actualizó `reglas-de-negocio.md`; Definition of Done (ruff, mypy, pytest con coverage, frontend, gitleaks, migraciones); seguridad (sin credenciales ni datos reales, `.env.example` actualizado si hay variables nuevas); calidad y decisiones (tests nuevos, test que reproduce el bug si es un fix, ADR si hubo decisión técnica, ninguna regla desactivada).

### Plantilla de issues

`.github/ISSUE_TEMPLATE/pedido.yml`, formulario "Pedido de Seba" pensado para cargarse desde el celular después de una llamada o un WhatsApp: fecha, canal, qué pidió con sus palabras, pantalla o proceso afectado, urgencia y adjuntos. Etiquetas: `pedido`, `bug`, `regla`, `descartado`. `docs/gestion-de-configuracion.md` documenta cómo crear las etiquetas.

### ADRs

`docs/adr/` copia el modelo de CheatSheet, traducido: plantilla con contexto, decisión, alternativas consideradas, consecuencias e impacto en reglas del repositorio; índice en el README; un ADR aceptado no se edita, se reemplaza por otro que lo referencia. Hace falta un ADR cuando una decisión afecta a más de una app o es costosa de revertir. Los cambios de reglas de negocio no requieren ADR, salvo que obliguen a cambiar la arquitectura o una regla de `CLAUDE.md`.

ADRs iniciales:

- **0001 — Estructura del repositorio.** Monolito modular Django con apps como módulos; frontend por `features/<app>`; qué va en la raíz y qué dentro de cada paquete; alternativas descartadas (arquitectura hexagonal de CheatSheet, separar en servicios).
- **0002 — GitFlow con `develop`.** Modelo de ramas y por qué. Staging como siguiente paso: un servicio web y una base en Render conectados a `develop`, y un job `deploy-staging` en CI con `needs:` sobre todos los gates. Se recomienda activarlo cuando Seba empiece a probar cambios antes de que lleguen a producción.
- **0003 — Requisitos evolutivos.** Catálogo de reglas de negocio, historias vivas con IDs estables, issues para los pedidos y unidades de ajuste. Explica en qué se aparta del AI-DLC de CheatSheet y por qué.
- **0004 — Gates de calidad estrictos.** mypy `--strict` con stubs de Django, coverage mínimo de 80 %, tests siempre contra PostgreSQL. Bajar un umbral requiere un ADR nuevo.

Las decisiones ya tomadas sobre Render e inventario no se convierten en ADRs retroactivos; quedan registradas en sus planes de unidad migrados.

## Requisitos evolutivos

### Catálogo de reglas de negocio

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

### Historias vivas

- `docs/aidlc/inputs/historias-de-usuario.md` es la fuente de verdad. El archivo original fuera del repositorio queda como histórico.
- Las historias se cambian en un PR `docs/historias-<descripcion>`, nunca mezclado con código.
- Los IDs no se reutilizan ni se renumeran. Una historia eliminada se marca `(retirada AAAA-MM-DD: motivo)`; una fusionada, `(fusionada en HU-xxx)`. Las nuevas toman el siguiente número libre.
- Cada cambio agrega una entrada a `docs/aidlc/inputs/registro-de-cambios.md`: fecha, quién lo pidió, issue, HUs afectadas, qué cambió y por qué, y qué regla abre o cierra.
- El mismo PR actualiza `roadmap.md` y `units.md` si el cambio mueve historias entre épicas o afecta unidades.
- Cuando se toca una historia, sus reglas pasan a referenciarse por ID en lugar de repetirse. No se reescribe el documento completo por adelantado.

### Pedidos de Seba

Los pedidos llegan por WhatsApp y llamadas. Se cargan como issues con la plantilla "Pedido de Seba". El triage clasifica cada issue en una de cuatro salidas: cambia una regla, es una historia nueva o ajustada, es un bug, o se descarta (con motivo). El PR que lo resuelve lo cierra con `Closes #N`, y queda la traza pedido → PR → regla o test. El repositorio guarda solo lo decidido.

## Workflow AI-DLC adaptado

### Archivos

- `.claude/aidlc/AIDLC.md`: se carga siempre desde `CLAUDE.md`. Contiene los tres gates, las reglas no negociables y cómo retomar trabajo.
- `.claude/aidlc/workflow.md`: los pasos y las plantillas de `roadmap.md`, `units.md` y el plan de unidad. Se carga al empezar trabajo de desarrollo.

### Documentos de trabajo

- `roadmap.md`: corto y reordenable. Épica actual, las dos o tres siguientes y una lista "más adelante". Se reordena cuando cambian las prioridades de Big Media; no reparte todo el catálogo de una vez.
- `units.md`: una tabla para todo el proyecto con épica, unidad, app dueña, HUs/RN/issue, dependencias, responsable, rama y estado (`pendiente`, `en curso`, `en revisión`, `mergeada`). El estado de una épica se deriva de sus unidades.
- `units/<unidad>.md`: plan de una página y registro de sus gates.

### Ciclo de una unidad

0. **Origen.** Una épica del roadmap o un issue triado.
1. **Encuadre** (sin gate). Leer historias y reglas involucradas y revisar el registro de cambios por si se movieron desde que se mapeó la unidad. Decir en tres líneas qué app es dueña, qué capas toca y si implica migraciones o reglas nuevas. Si no está claro, preguntar en español con opciones concretas.
2. **Gate 1 — Plan de unidad.** Objetivo; HUs, RN e issue; cambios por app; migraciones; cómo se prueba; reglas en `provisoria` que se usan. No se toca `backend/` ni `frontend/` hasta que se apruebe.
3. **Implementación.** TDD; tests con marcador de regla; lo provisorio como parámetro cuando sea posible.
4. **Gate 2 — Verificación.** Correr los mismos comandos que CI y reportar la salida real.
5. **Gate 3 — Pull Request.** Push y PR solo cuando se pidan. El PR cierra su issue y actualiza `units.md` y, si corresponde, `reglas-de-negocio.md`.

### Diferencias con CheatSheet

- Historias y reglas son insumos vivos: cambian por PR `docs/` con registro, sin ADR.
- El roadmap es corto y se reordena; no es un catálogo completo repartido al inicio.
- Una unidad mergeada es histórico inmutable. Un cambio posterior se hace en una unidad nueva `ajuste-<tema>` que referencia el cambio.
- Un cambio trivial (typo, versión) se declara en una línea y se implementa directo, siempre en rama y por PR.

### Roadmap inicial

E0 (base) y E2 (inventario, sin la importación de HU-015) figuran como hechas; las unidades mergeadas se registran en `units.md`. La épica siguiente se elige con Juan Diego al escribir el roadmap, según lo que Seba necesite usar primero.

## CI y calidad

### Workflow

`.github/workflows/ci.yml` corre en pull requests y pushes a `develop` y `main`. Jobs:

| Job | Qué hace | Falla cuando |
|---|---|---|
| `convenciones` (solo PR) | Valida rama contra destino según la tabla de ramas y el formato de cada commit | Rama mal nombrada o con destino incorrecto; commit fuera de formato |
| `lint-python` | `ruff format --check` y `ruff check` | Formato o reglas de ruff |
| `tipos` | `mypy --strict` con `django-stubs` y `djangorestframework-stubs` | Código sin tipar o tipos inconsistentes |
| `migraciones` | `manage.py makemigrations --check --dry-run` y `manage.py check --deploy` con settings de producción | Modelo cambiado sin migración; configuración insegura |
| `tests-backend` | pytest contra PostgreSQL 17 en un service container, coverage mínimo de 80 % | Test fallido, coverage bajo el umbral, o algún test salteado por falta de base |
| `frontend` | Prettier, oxlint, `tsc --noEmit`, vitest con coverage mínimo de 80 %, `vite build` | Cualquiera de esos pasos |
| `secretos` | gitleaks sobre el árbol de trabajo | Credencial detectada |
| `imagen` | `docker build` del Dockerfile de producción | La imagen no compila |

Render sigue desplegando `main` con `autoDeployTrigger: checksPass`, de modo que producción solo recibe commits con CI verde. Los mensajes de error de CI se escriben en español.

### Configuración

- **`pyproject.toml` (raíz):** ruff con Python 3.12, línea 100 y las reglas de CheatSheet (`E`, `W`, `F`, `I`, `UP`, `B`, `S`, `ANN`, `PT`, `C90`, `SIM`, `RET`, `ARG`, `PTH`, `DTZ`, `T20`, `BLE`, `RUF`), con excepciones por archivo para tests y migraciones; mypy `strict` con el plugin de django-stubs; pytest con `DJANGO_SETTINGS_MODULE`, `--strict-markers`, `--strict-config` y el marcador `regla`; coverage con `branch = true` y `fail_under = 80`, sin contar migraciones.
- **`backend/pyproject.toml`:** solo empaquetado y dependencias de la aplicación. Pierde `[tool.pytest.ini_options]` y el extra `dev`, que pasan a la raíz y a `requirements-dev.txt`.
- **`requirements-dev.txt`:** versiones fijas de ruff, mypy, django-stubs, djangorestframework-stubs, pytest, pytest-django, pytest-cov y pre-commit. Actualizarlas es un cambio deliberado, en su propio PR.
- **`.pre-commit-config.yaml`:** trailing whitespace, fin de archivo, YAML/TOML/JSON válidos, conflictos de merge, archivos grandes, `detect-private-key`, `no-commit-to-branch` para `main` y `develop`, ruff y gitleaks. mypy queda solo en CI porque con stubs de Django es lento.
- **`.gitleaks.toml`:** reglas por defecto, con allowlist para `.env.example` y archivos Markdown.
- **Frontend:** Prettier con su configuración e ignore; scripts `typecheck`, `format`, `format:check` y `test:coverage`; umbral de coverage en `vite.config.ts`. `strict: true` ya está activo en TypeScript.

### Tests siempre contra PostgreSQL

Se elimina `BIGMEDIA_RUN_DB_TESTS`. La suite completa corre siempre contra PostgreSQL: local con `docker compose up db`, en CI con el service container. El job `tests-backend` falla si algún test queda salteado. Así una regla de disponibilidad no puede pasar en un modo de ejecución y fallar en otro. `docs/operacion/desarrollo-local.md` y `backend/tests/README.md` se actualizan.

### Arreglos de código

El PR 2 ajusta el código existente (configuración, salud, autenticación, app `inventario` y sus tests, frontend) para que pase ruff, mypy `--strict` y el coverage de 80 %. Si algo no se puede tipar sin pelearse con Django, se usa `# type: ignore[codigo]` con un comentario que explique por qué. No se usan ignores generales, no se excluyen archivos del linter y no se baja ningún umbral. Si el coverage del código existente queda por debajo de 80 %, se agregan los tests que falten en este mismo PR.

### Protección de ramas

`docs/gestion-de-configuracion.md` documenta la configuración manual en GitHub: `main` y `develop` requieren PR y todos los jobs de CI en verde antes de mergear; `main` además solo recibe PRs desde `develop` o `hotfix/*`. Activarla lo hace Juan Diego desde la configuración del repositorio.

## Criterios de aceptación

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

## Riesgos

- **Rebase de trabajo en paralelo.** Si se empieza otra rama antes de que el PR 2 llegue a `develop`, va a fallar los gates nuevos. Mitigación: mergear el PR 2 enseguida después del PR 1 y no abrir ramas de funcionalidad en el medio.
- **mypy strict con Django.** Los stubs no cubren todo; puede haber `type: ignore` justificados en serializers y querysets. Se aceptan con su comentario.
- **Ceremonia contra velocidad.** Si el workflow resulta pesado en la práctica, se aligera con un ADR que reemplace a ADR-0003; no se saltean pasos en silencio.
