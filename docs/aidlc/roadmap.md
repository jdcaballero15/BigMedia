# Roadmap

Corto y reordenable: la épica en curso, las próximas y lo que queda para más adelante. Se reordena
cuando cambian las prioridades de Big Media; cada cambio de orden se anota abajo con fecha y motivo.
Las épicas vienen del mapa de [`inputs/historias-de-usuario.md`](inputs/historias-de-usuario.md).

## Hecho

- **E0 Plataforma base** — base del repositorio y despliegue en Render. HU-001 (parámetros) sigue pendiente.
- **E2 Inventario de soportes** — HU-008 a HU-014. HU-015 espera los relevamientos (RN-009).
- **Reestructura del repositorio** (unidad técnica): gobernanza, CI estricto y protección de ramas.

## En curso

- **E3 Clientes, marcas y CRM** — unidad `clientes-y-marcas` (HU-016, HU-017, HU-018).

## Próximas

1. **Entornos: producción paga y staging gratis** (unidad técnica, **antes del 17/11/2026**, cuando vence
   la base gratis actual). Producción (`main`) pasa a web y PostgreSQL pagos, con copias de seguridad.
   Se agrega staging conectado a `develop` con web y PostgreSQL del plan gratis, y un comando que carga
   datos de ejemplo (nunca datos reales). Límite a tener en cuenta: la base gratis de staging vence cada
   30 días y hay que recrearla y volver a cargarle los datos de ejemplo. Detalle en el
   [ADR-0002](../adr/0002-gitflow-con-develop.md).
2. **E3 Clientes, marcas y CRM** — después de `clientes-y-marcas`: aviso de duplicados (HU-019),
   contactos (HU-068) e interacciones (HU-020).
3. **E4 Campañas** — HU-023 a HU-027. Una campaña agrupa reservas y se arma con marca y cliente que factura.
4. **E5 Reservas y motor de disponibilidad** — HU-028 a HU-040. Es el objetivo central; cada reserva pertenece a una campaña, por eso va después de E3 y E4.

El orden sigue las dependencias entre historias. Se reordena si Seba necesita usar otra parte antes.

## Más adelante

E1 Seguridad y acceso · E3 Clientes, marcas y CRM · E4 Campañas · E5 Reservas y motor de
disponibilidad · E6 Vista de disponibilidad · E7 Costos y rentabilidad · E8 Reportes y paneles ·
E9 Entrega y traspaso · E10 Armado de campañas y reserva masiva · E11 Facturación mensual.

E5 es el núcleo: si hay que recortar alcance, se recorta alrededor de ella y nunca adentro.

## Cambios de orden

| Fecha | Cambio | Motivo |
| --- | --- | --- |
| 2026-10-18 | Se agrega la unidad técnica de entornos antes de E4 | La base gratis de producción vence el 17/11/2026; Juan Diego decidió producción paga y staging gratis |
