# AI-DLC de Big Media

Workflow de desarrollo del repositorio, adaptado a requisitos que cambian con el uso.
Detalle de pasos y plantillas: `.claude/aidlc/workflow.md`.

## 1. Qué es

- Se aplica a toda funcionalidad, corrección, refactor o migración, sin que haga falta pedirlo.
- Al recibir trabajo de desarrollo, decí en una línea qué unidad es y cargá `.claude/aidlc/workflow.md`.

## 2. Los tres gates

| Gate | Qué es | Regla |
| --- | --- | --- |
| 1. Plan de unidad | Plan en `docs/aidlc/units/<unidad>.md` | No se escribe nada en `backend/` ni `frontend/` sin aprobación. |
| 2. Verificación | Correr los comandos de CI | Reportar la salida real y esperar a Juan Diego. |
| 3. Pull Request | Push y PR | Solo cuando se pidan. |

Entre gates no se inventan aprobaciones extra.

## 3. No negociables

- `CLAUDE.md` manda sobre este workflow.
- Un gate es una parada real: el silencio no es aprobación.
- Nunca se esquiva una regla de CI o de pre-commit.
- Los documentos de trabajo viven en `docs/aidlc/`.
- Las preguntas se hacen en español, con opciones concretas, y la respuesta se anota en el plan de unidad.

## 4. Requisitos vivos

Las historias y las reglas pueden cambiar.

- Antes de planificar, revisá `docs/aidlc/inputs/registro-de-cambios.md` y `docs/aidlc/reglas-de-negocio.md`.
- Un cambio de historia o de regla va en un PR `docs/historias-<descripcion>`, sin mezclar código.
- Una unidad mergeada no se reescribe: el ajuste es una unidad nueva `ajuste-<tema>`.

## 5. De dónde sale el trabajo

- Una épica de `docs/aidlc/roadmap.md`.
- Un issue triado con etiqueta `pedido`, `bug` o `regla`.

## 6. Retomar

Si `docs/aidlc/units.md` tiene una unidad `en curso`, leé su plan y retomala sin volver a preguntar lo que el plan ya registra.

## 7. Trabajo trivial

- Una conversación sin cambios no lleva gates.
- Un cambio más chico que su plan (typo, versión) se declara en una línea y se hace directo, siempre en rama y por PR.
