# Mapa de unidades

Una fila por unidad de trabajo. La columna `Épica` coincide con el nombre en
[`roadmap.md`](roadmap.md). El estado de una épica se deriva de sus unidades.

Estados: `pendiente` · `en curso` · `en revisión` (PR abierto) · `mergeada`.

| Épica | Unidad | App dueña | HUs / RN / issue | Depende de | Responsable | Rama | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E0 Plataforma base | [base-del-repositorio](units/base-del-repositorio.md) | infra | HU-002 | — | Juan Diego | main (inicial) | mergeada |
| E2 Inventario de soportes | [inventario](units/inventario.md) | inventario | HU-008…HU-014, RN-004, RN-005, RN-008, RN-010 | base-del-repositorio | Juan Diego | feat/inventario | mergeada |
| E0 Plataforma base | [despliegue-render](units/despliegue-render.md) | infra | HU-002 | base-del-repositorio | Juan Diego | chore/render-deploy | mergeada |
| — (unidad técnica) | [reestructura-del-repositorio](units/reestructura-del-repositorio.md) | docs, infra | — | despliegue-render | Juan Diego | docs/reestructura-gobernanza, chore/gates-de-calidad | mergeada |
| — (unidad técnica) | [entornos](units/entornos.md) | infra | roadmap (antes del 17/11/2026) | despliegue-render | Juan Diego | feature/infra-entornos | mergeada |
| E3 Clientes, marcas y CRM | [clientes-y-marcas](units/clientes-y-marcas.md) | clientes | HU-016, HU-017, HU-018 | base-del-repositorio | Juan Diego | feature/clientes-clientes-y-marcas | mergeada |
| E4 Campañas | [campanias](units/campanias.md) | campanias | HU-023, HU-024 (RN-011, RN-014) | clientes-y-marcas | Juan Diego | feature/campanias-crear-y-estados | mergeada |
| E5 Reservas y motor de disponibilidad | [reservas-base](units/reservas-base.md) | reservas | HU-028, HU-029, HU-030, HU-035, HU-037, HU-040 (RN-004, RN-005, RN-006) | campanias | Juan Diego | feature/reservas-base | mergeada |
| E5 Reservas y motor de disponibilidad | [reservas-motor-disponibilidad](units/reservas-motor-disponibilidad.md) | reservas | HU-031, HU-032, HU-033, HU-034 (RN-001, RN-002, RN-003) | reservas-base | Juan Diego | feature/reservas-motor-disponibilidad | mergeada |
| E6 Vista de disponibilidad | [disponibilidad-hoy](units/disponibilidad-hoy.md) | reservas | HU-041 (RN-004, RN-005) | reservas-motor-disponibilidad | Juan Diego | feature/reservas-disponibilidad-hoy | mergeada |
| E6 Vista de disponibilidad | [calendario-disponibilidad](units/calendario-disponibilidad.md) | reservas | HU-042 (RN-001, RN-003, RN-013) | disponibilidad-hoy | Juan Diego | feature/reservas-calendario-disponibilidad | mergeada |
| E7 Costos y rentabilidad | [costos-y-margen](units/costos-y-margen.md) | costos | HU-043, HU-044 (RN-007) | reservas-base | Juan Diego | feature/costos-costos-y-margen | mergeada |
| — (unidad técnica) | [navegacion-lateral](units/navegacion-lateral.md) | frontend, costos | pedido 19/10/2026 | costos-y-margen | Juan Diego | feature/frontend-navegacion-lateral | mergeada |
| E7 Costos y rentabilidad | [margen-campania](units/margen-campania.md) | costos | HU-025, HU-045 (RN-006) | costos-y-margen | Juan Diego | feature/costos-margen-campania | mergeada |
| E8 Reportes y paneles | [panel-principal](units/panel-principal.md) | reservas | HU-047 | costos-y-margen | Juan Diego | feature/reservas-panel-principal | mergeada |
| E8 Reportes y paneles | [reparto-ingresos](units/reparto-ingresos.md) | reservas | HU-051 | panel-principal | Juan Diego | feature/reservas-reparto-ingresos | mergeada |
| E8 Reportes y paneles | [reporte-ingresos](units/reporte-ingresos.md) | facturacion | HU-049 (RN-014) | reparto-ingresos, clientes-y-marcas | Juan Diego | feature/facturacion-reporte-ingresos | mergeada |
| E8 Reportes y paneles | [reporte-ingresos-frontend](units/reporte-ingresos-frontend.md) | frontend | HU-049 (pantalla) | reporte-ingresos | Juan Diego | feature/frontend-reporte-ingresos | mergeada |
| E8 Reportes y paneles | [reporte-ocupacion](units/reporte-ocupacion.md) | reservas | HU-048 (RN-004) | reservas-base | Juan Diego | feature/reservas-reporte-ocupacion | mergeada |
| E8 Reportes y paneles | [reporte-ocupacion-frontend](units/reporte-ocupacion-frontend.md) | frontend | HU-048 (pantalla) | reporte-ocupacion | Juan Diego | feature/frontend-reporte-ocupacion | mergeada |
| E8 Reportes y paneles | [exportar-reportes-csv](units/exportar-reportes-csv.md) | frontend | HU-052 (CSV) | reporte-ingresos-frontend, reporte-ocupacion-frontend | Juan Diego | feature/frontend-exportar-reportes | mergeada |
| E1 Seguridad y acceso | [permiso-ingresos](units/permiso-ingresos.md) | usuarios | HU-052 (criterio 2) | reporte-ingresos | Juan Diego | feature/usuarios-permiso-ingresos | mergeada |
| — (unidad técnica) | [ajuste-entornos-neon](units/ajuste-entornos-neon.md) | infra | decisión 21/10/2026 (ADR-0005) | entornos | Juan Diego | chore/infra-entornos-neon | mergeada |
| E8 Reportes y paneles | [exportar-reportes-pdf](units/exportar-reportes-pdf.md) | frontend | HU-052 (PDF) | exportar-reportes-csv | Juan Diego | feature/frontend-exportar-pdf | mergeada |
| E8 Reportes y paneles | [reporte-por-rubro](units/reporte-por-rubro.md) | facturacion | HU-050 (rubro, RN-004) | reporte-ingresos, reporte-ocupacion | Juan Diego | feature/facturacion-reporte-por-rubro | mergeada |
| E1 Seguridad y acceso | [auditoria-base](units/auditoria-base.md) | auditoria | HU-007 (base + reservas) | permiso-ingresos | Juan Diego | feature/auditoria-base | mergeada |
| E1 Seguridad y acceso | [auditoria-pantalla](units/auditoria-pantalla.md) | frontend | HU-007 (pantalla) | auditoria-base | Juan Diego | feature/frontend-auditoria | mergeada |
| E1 Seguridad y acceso | [auditoria-campania-cartel](units/auditoria-campania-cartel.md) | campanias, inventario | HU-007 (campaña y tarifa) | auditoria-base | Juan Diego | feature/auditoria-campania-cartel | mergeada |
| E1 Seguridad y acceso | [sesion-inactividad](units/sesion-inactividad.md) | usuarios, frontend | HU-003 (criterio 4) | — | Juan Diego | feature/usuarios-sesion-inactividad | mergeada |
| E1 Seguridad y acceso | [bloqueo-intentos-fallidos](units/bloqueo-intentos-fallidos.md) | usuarios | HU-003 (criterio 3) | sesion-inactividad | Gonza | feature/usuarios-bloqueo-intentos-fallidos | mergeada |
| E1 Seguridad y acceso | [roles-y-permisos](units/roles-y-permisos.md) | usuarios | HU-004 | bloqueo-intentos-fallidos | Gonza | feature/usuarios-roles-y-permisos | mergeada |
| — (unidad técnica) | [ajuste-datos-ejemplo](units/ajuste-datos-ejemplo.md) | usuarios, infra | pedido 23/10/2026 (demo en staging) | entornos | Gonza | chore/infra-datos-ejemplo-demo | mergeada |
| E1 Seguridad y acceso | [gestion-de-usuarios](units/gestion-de-usuarios.md) | usuarios | HU-005 (RN-021) | roles-y-permisos | Gonza | feature/usuarios-gestion-de-usuarios | mergeada |
| E1 Seguridad y acceso | [baja-logica](units/baja-logica.md) | reservas | HU-006 | gestion-de-usuarios | Gonza | feature/reservas-baja-logica | mergeada |
| E0 Plataforma base | [parametros-configurables](units/parametros-configurables.md) | reservas | HU-001 (RN-001, RN-002) | reservas-motor-disponibilidad, gestion-de-usuarios | Gonza | feature/reservas-parametros-configurables | mergeada |
| E3 Clientes, marcas y CRM | [marcas-duplicadas](units/marcas-duplicadas.md) | clientes | HU-019 | clientes-y-marcas | Gonza | feature/clientes-marcas-duplicadas | mergeada |
| E3 Clientes, marcas y CRM | [contactos-intermediario](units/contactos-intermediario.md) | clientes | HU-068 (RN-015) | clientes-y-marcas | Gonza | feature/clientes-contactos-intermediario | mergeada |
| E5 Reservas y motor de disponibilidad | [sobreventa-finalizada](units/sobreventa-finalizada.md) | reservas | HU-031, HU-035 (RN-002) | reservas-motor-disponibilidad | Juan Diego | fix/reservas-sobreventa-finalizada | mergeada |
| E3 Clientes, marcas y CRM | [interacciones](units/interacciones.md) | campanias | HU-020, HU-068 (criterios 5 y 7) | contactos-intermediario, campanias | Juan Diego | feature/campanias-interacciones | mergeada |
| — (unidad técnica) | [ajuste-selector-de-fechas](units/ajuste-selector-de-fechas.md) | frontend | prueba manual 24/10/2026 | — | Juan Diego | fix/frontend-selector-de-fechas | mergeada |
| E10 Armado de campañas y reserva masiva | [posiciones-por-formato](units/posiciones-por-formato.md) | campanias | HU-055, HU-058 (criterios 1 y 2) | campanias, reservas-base | Gonza | feature/campanias-posiciones-por-formato | mergeada |
| E10 Armado de campañas y reserva masiva | [reserva-masiva](units/reserva-masiva.md) | reservas | HU-056, HU-057 (RN-001, RN-002, RN-003, RN-004, RN-005) | posiciones-por-formato | Gonza | feature/reservas-reserva-masiva | mergeada |
| E10 Armado de campañas y reserva masiva | [confirmacion-en-bloque](units/confirmacion-en-bloque.md) | reservas | HU-059, HU-058 (criterios 3 y 4) (RN-001, RN-002, RN-003, RN-011) | reserva-masiva | Gonza | feature/reservas-confirmacion-en-bloque | mergeada |
| E11 Facturación mensual | [items-a-facturar](units/items-a-facturar.md) | facturacion | HU-060, HU-061, HU-065 (RN-022, RN-023) | clientes-y-marcas, campanias | Gonza | feature/facturacion-items-a-facturar | mergeada |
| E11 Facturación mensual | [cierre-de-mes](units/cierre-de-mes.md) | facturacion | HU-066 (RN-022, RN-024, RN-025) | items-a-facturar | Gonza | feature/facturacion-cierre-de-mes | mergeada |
| E9 Entrega y traspaso | [entrega-y-traspaso](units/entrega-y-traspaso.md) | docs | HU-053, HU-054 | — | Gonza | docs/entrega-y-traspaso | mergeada |
| E11 Facturación mensual | [orden-de-compra-y-grupos](units/orden-de-compra-y-grupos.md) | facturacion | HU-062, HU-064 (RN-024) | cierre-de-mes | Gonza | feature/facturacion-orden-de-compra-y-grupos | mergeada |
| E11 Facturación mensual | [costos-del-item](units/costos-del-item.md) | facturacion | HU-063, HU-066 criterio 1 (RN-024) | cierre-de-mes, costos-y-margen | Gonza | feature/facturacion-costos-del-item | mergeada |
| E11 Facturación mensual | [reabrir-item](units/reabrir-item.md) | facturacion | HU-067 (RN-022) | cierre-de-mes, auditoria-base | Gonza | feature/facturacion-reabrir-item | mergeada |

## Notas

- HU-015 (importación de inventario) queda fuera de la unidad `inventario` hasta tener los relevamientos (RN-009).
