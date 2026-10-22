# Roadmap

Corto y reordenable: la épica en curso, las próximas y lo que queda para más adelante. Se reordena
cuando cambian las prioridades de Big Media; cada cambio de orden se anota abajo con fecha y motivo.
Las épicas vienen del mapa de [`inputs/historias-de-usuario.md`](inputs/historias-de-usuario.md).

## Hecho

- **E0 Plataforma base** — base del repositorio y despliegue en Render. HU-001 (parámetros) sigue pendiente.
- **Reestructura del repositorio** (unidad técnica) — gobernanza, CI estricto y protección de ramas.
- **E2 Inventario de soportes** — HU-008 a HU-014. HU-015 (importación) espera los relevamientos (RN-009).
- **E3 Clientes, marcas y CRM** — clientes y marcas (HU-016, HU-017, HU-018). Faltan avisos de
  duplicados (HU-019), contactos (HU-068) e interacciones (HU-020).
- **E4 Campañas** — crear campañas y sus estados (HU-023, HU-024).
- **E5 Reservas y motor de disponibilidad** — reservas, ciclo de vida y motor de disponibilidad
  (HU-028 a HU-040).
- **E6 Vista de disponibilidad** — disponibilidad de hoy y calendario a futuro (HU-041, HU-042).
- **E7 Costos y rentabilidad** — costos y márgenes de reserva y de campaña (HU-043, HU-044, HU-025, HU-045).
- **E8 Reportes y paneles** — panel, reparto de ingresos, ingresos por cliente/marca, ocupación y
  exportación a CSV (HU-047, HU-051, HU-049, HU-048, HU-052 parte CSV). Quedan HU-050 (grupo económico,
  pregunta 16) y HU-052 (PDF y rechazo por permiso de facturación).

## En curso

- [ajuste-entornos-neon](units/ajuste-entornos-neon.md): producción paga en Render y base de staging en
  Neon.

## Próximas

1. **Entornos: producción paga y staging gratis** (unidad técnica, **antes del 17/11/2026**, cuando
   vence la base gratis actual). Producción (`main`) pasa a web y PostgreSQL pagos, con copias de
   seguridad. Se agrega staging conectado a `develop`, con la web gratis en Render y la base gratis en
   Neon (no vence), y un comando que carga datos de ejemplo (nunca datos reales). En curso:
   [ajuste-entornos-neon](units/ajuste-entornos-neon.md). Detalle en el
   [ADR-0002](../adr/0002-gitflow-con-develop.md) y el [ADR-0005](../adr/0005-base-de-staging-en-neon.md).
2. **Cerrar E8** — HU-050 (análisis por rubro y grupo económico, bloqueada por la pregunta 16) y lo que
   falta de HU-052 (PDF y el permiso de ingresos).
3. **E1 Seguridad y acceso** — cuentas, sesión y permisos finos (incluye el grupo "Gerencia" para ver
   ingresos, que destraba el gate de HU-052).

El orden sigue las dependencias entre historias. Se reordena si Seba necesita usar otra parte antes.

## Más adelante

E9 Entrega y traspaso · E10 Armado de campañas y reserva masiva · E11 Facturación mensual.

E5 es el núcleo: si hubo que recortar alcance, se recortó alrededor de ella y nunca adentro.

## Cambios de orden

| Fecha | Cambio | Motivo |
| --- | --- | --- |
| 2026-10-18 | Se agrega la unidad técnica de entornos como próxima prioridad | La base gratis de producción vence el 17/11/2026; Juan Diego decidió producción paga y staging gratis |
| 2026-10-21 | Roadmap puesto al día: E2 a E8 pasan a Hecho y la unidad de entornos queda como próxima | El roadmap había quedado atrás respecto del trabajo ya mergeado (E3 a E8) |
