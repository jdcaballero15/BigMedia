# Documentación de Big Media

Punto de entrada a `docs/`. Las reglas absolutas del repositorio están en [`CLAUDE.md`](../CLAUDE.md); el resumen para quien llega por primera vez, en el [`README.md`](../README.md) de la raíz.

## Guías

| Documento | Para qué sirve |
| --- | --- |
| [`arquitectura.md`](arquitectura.md) | Estilo (monolito modular), árbol del repositorio, apps con su responsabilidad y riesgo, dependencias permitidas, regla crítica de disponibilidad y frontend. |
| [`estandares-de-codigo.md`](estandares-de-codigo.md) | Reglas de Python, Django, TypeScript y tests, con ejemplos correctos e incorrectos y cómo se verifica cada una. |
| [`gestion-de-configuracion.md`](gestion-de-configuracion.md) | Ramas, commits, entornos, credenciales, jobs de CI y configuración manual en GitHub. |

## Decisiones

| Documento | Para qué sirve |
| --- | --- |
| [`adr/`](adr/README.md) | Registro de decisiones de arquitectura: cuándo escribir una, plantilla e índice. |

## `operacion/`

| Documento | Para qué sirve |
| --- | --- |
| [`operacion/desarrollo-local.md`](operacion/desarrollo-local.md) | Instalar dependencias y ejecutar base, API y frontend en tu máquina. |
| [`operacion/despliegue-render.md`](operacion/despliegue-render.md) | Poner en marcha, verificar y recuperar la instalación en Render. |

## `aidlc/`

Documentos de trabajo del workflow de desarrollo (ver [ADR-0003](adr/0003-requisitos-evolutivos.md)).

| Documento | Para qué sirve |
| --- | --- |
| [`aidlc/roadmap.md`](aidlc/roadmap.md) | Épica en curso, las próximas y lo que queda para más adelante. Corto y reordenable. |
| [`aidlc/units.md`](aidlc/units.md) | Mapa de todas las unidades de trabajo con su épica, dueño, rama y estado. |
| [`aidlc/units/`](aidlc/units.md) | Un archivo por unidad: plan y registro de sus gates. Las unidades mergeadas son histórico. |
| [`aidlc/reglas-de-negocio.md`](aidlc/reglas-de-negocio.md) | Catálogo de reglas con ID (`RN-xxx`), estado y valor actual. |
| [`aidlc/inputs/historias-de-usuario.md`](aidlc/inputs/historias-de-usuario.md) | Historias de usuario con IDs estables (`HU-xxx`). |
| [`aidlc/inputs/registro-de-cambios.md`](aidlc/inputs/registro-de-cambios.md) | Cada cambio a historias o reglas: fecha, quién lo pidió, qué cambió y por qué. |
| [`aidlc/inputs/importacion/`](aidlc/inputs/importacion/README.md) | Plantillas CSV de importación de inventario. |
| [`aidlc/inputs/ux/`](aidlc/inputs/ux/recorrido-disponibilidad-y-reservas.md) | Recorrido de UX de disponibilidad y reservas. |

**Las historias y las reglas son insumos vivos**, no documentos cerrados: cambian a medida que Seba usa el sistema. Se modifican por PR `docs/`, con IDs que nunca se reutilizan y una entrada en el registro de cambios.
