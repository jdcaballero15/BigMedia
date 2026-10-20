# Mapa de unidades

Una fila por unidad de trabajo. La columna `Épica` coincide con el nombre en
[`roadmap.md`](roadmap.md). El estado de una épica se deriva de sus unidades.

Estados: `pendiente` · `en curso` · `en revisión` (PR abierto) · `mergeada`.

| Épica | Unidad | App dueña | HUs / RN / issue | Depende de | Responsable | Rama | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E0 Plataforma base | [base-del-repositorio](units/base-del-repositorio.md) | infra | HU-002 | — | Juan Diego | main (inicial) | mergeada |
| E2 Inventario de soportes | [inventario](units/inventario.md) | inventario | HU-008…HU-014, RN-004, RN-005, RN-008, RN-010 | base-del-repositorio | Juan Diego | feat/inventario | mergeada |
| E0 Plataforma base | [despliegue-render](units/despliegue-render.md) | infra | HU-002 | base-del-repositorio | Juan Diego | chore/render-deploy | mergeada |
| — (unidad técnica) | [reestructura-del-repositorio](units/reestructura-del-repositorio.md) | docs, infra | — | despliegue-render | Juan Diego | docs/reestructura-gobernanza, chore/gates-de-calidad | en curso |
| E3 Clientes, marcas y CRM | [clientes-y-marcas](units/clientes-y-marcas.md) | clientes | HU-016, HU-017, HU-018 | base-del-repositorio | Juan Diego | feature/clientes-clientes-y-marcas | mergeada |
| E4 Campañas | [campanias](units/campanias.md) | campanias | HU-023, HU-024 (RN-011, RN-014) | clientes-y-marcas | Juan Diego | feature/campanias-crear-y-estados | mergeada |
| E5 Reservas y motor de disponibilidad | [reservas-base](units/reservas-base.md) | reservas | HU-028, HU-029, HU-030, HU-035, HU-037, HU-040 (RN-004, RN-005, RN-006) | campanias | Juan Diego | feature/reservas-base | mergeada |
| E5 Reservas y motor de disponibilidad | [reservas-motor-disponibilidad](units/reservas-motor-disponibilidad.md) | reservas | HU-031, HU-032, HU-033, HU-034 (RN-001, RN-002, RN-003) | reservas-base | Juan Diego | feature/reservas-motor-disponibilidad | mergeada |
| E6 Vista de disponibilidad | [disponibilidad-hoy](units/disponibilidad-hoy.md) | reservas | HU-041 (RN-004, RN-005) | reservas-motor-disponibilidad | Juan Diego | feature/reservas-disponibilidad-hoy | mergeada |
| E6 Vista de disponibilidad | [calendario-disponibilidad](units/calendario-disponibilidad.md) | reservas | HU-042 (RN-001, RN-003, RN-013) | disponibilidad-hoy | Juan Diego | feature/reservas-calendario-disponibilidad | mergeada |
| E7 Costos y rentabilidad | [costos-y-margen](units/costos-y-margen.md) | costos | HU-043, HU-044 (RN-007) | reservas-base | Juan Diego | feature/costos-costos-y-margen | mergeada |
| — (unidad técnica) | [navegacion-lateral](units/navegacion-lateral.md) | frontend, costos | pedido 19/10/2026 | costos-y-margen | Juan Diego | feature/frontend-navegacion-lateral | mergeada |
| E7 Costos y rentabilidad | [margen-campania](units/margen-campania.md) | costos | HU-025, HU-045 (RN-006) | costos-y-margen | Juan Diego | feature/costos-margen-campania | en curso |

## Notas

- HU-015 (importación de inventario) queda fuera de la unidad `inventario` hasta tener los relevamientos (RN-009).
