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
