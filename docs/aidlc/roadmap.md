# Roadmap

Corto y reordenable: la épica en curso, las próximas y lo que queda para más adelante. Se reordena
cuando cambian las prioridades de Big Media; cada cambio de orden se anota abajo con fecha y motivo.
Las épicas vienen del mapa de [`inputs/historias-de-usuario.md`](inputs/historias-de-usuario.md).

## Hecho

- **E0 Plataforma base** — base del repositorio y despliegue en Render, y parámetros del motor de disponibilidad configurables desde la
  aplicación (HU-001).
- **Reestructura del repositorio** (unidad técnica) — gobernanza, CI estricto y protección de ramas.
- **E2 Inventario de soportes** — HU-008 a HU-014. HU-015 (importación) espera los relevamientos (RN-009).
- **E3 Clientes, marcas y CRM** — clientes y marcas (HU-016, HU-017, HU-018) y aviso de marcas
  duplicadas (HU-019; su criterio 3 espera un importador de marcas) y contactos del intermediario
  formal (HU-068; sus criterios 5 y 7 llegan con HU-020). Faltan las interacciones (HU-020).
- **E4 Campañas** — crear campañas y sus estados (HU-023, HU-024).
- **E5 Reservas y motor de disponibilidad** — reservas, ciclo de vida y motor de disponibilidad
  (HU-028 a HU-040).
- **E6 Vista de disponibilidad** — disponibilidad de hoy y calendario a futuro (HU-041, HU-042).
- **E7 Costos y rentabilidad** — costos y márgenes de reserva y de campaña (HU-043, HU-044, HU-025, HU-045).
- **E8 Reportes y paneles** — panel, reparto de ingresos, ingresos por cliente/marca, ocupación,
  análisis por rubro y exportación a CSV y PDF (HU-047, HU-051, HU-049, HU-048, HU-050 parte rubro,
  HU-052). Queda el grupo económico de HU-050 (pregunta 16, RN-016).
- **Entornos: producción paga y staging gratis** (unidad técnica) — producción paga en Render y staging
  con base en Neon ([ADR-0002](../adr/0002-gitflow-con-develop.md),
  [ADR-0005](../adr/0005-base-de-staging-en-neon.md)).
- **E1 Seguridad y acceso** — grupo Gerencia para ver ingresos (HU-052 criterio 2), auditoría
  de reservas, campañas y tarifas con su pantalla (HU-007), expiración de sesión por inactividad
  (HU-003 criterio 4), bloqueo temporal por intentos fallidos (HU-003 criterio 3), roles Operativo,
  Administrador y Lectura (HU-004), gestión de usuarios (HU-005) y baja lógica (HU-006).

## En curso

- Ninguna.

## Próximas

1. **Resto de E3** — interacciones comerciales (HU-020), que completan los criterios 5 y 7 de HU-068.

El orden sigue las dependencias entre historias. Se reordena si Seba necesita usar otra parte antes.

## Más adelante

E9 Entrega y traspaso · E10 Armado de campañas y reserva masiva · E11 Facturación mensual.

E5 es el núcleo: si hubo que recortar alcance, se recortó alrededor de ella y nunca adentro.

## Cambios de orden

| Fecha | Cambio | Motivo |
| --- | --- | --- |
| 2026-10-18 | Se agrega la unidad técnica de entornos como próxima prioridad | La base gratis de producción vence el 17/11/2026; Juan Diego decidió producción paga y staging gratis |
| 2026-10-21 | Roadmap puesto al día: E2 a E8 pasan a Hecho y la unidad de entornos queda como próxima | El roadmap había quedado atrás respecto del trabajo ya mergeado (E3 a E8) |
| 2026-10-23 | Entornos, el cierre de E8 (salvo grupo económico) y parte de E1 pasan a Hecho; E1 queda primera | El roadmap había quedado atrás respecto de las unidades ya mergeadas |
| 2026-10-26 | HU-005, HU-006 y HU-001 pasan a Hecho; el resto de E3 queda primero | Gestión de usuarios, baja lógica y parámetros configurables quedaron mergeadas (PR #65, #66 y #67) |
