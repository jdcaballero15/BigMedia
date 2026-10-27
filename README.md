# Big Media Argentina

Sistema de inventario, campañas y reservas de publicidad de vía pública. Es un monorepo con una API Django REST Framework sobre PostgreSQL y una aplicación web React + TypeScript.

## Estado

Están disponibles el inventario de carteles, los clientes y marcas, las campañas con sus posiciones por formato, las reservas con su disponibilidad y su confirmación, los costos, los reportes, la auditoría y los ítems a facturar con su envío mensual. Qué hace cada pantalla está en el [manual de uso](docs/manual/manual-de-uso.md).

## Cómo arrancar

Seguí [desarrollo local](docs/operacion/desarrollo-local.md) para instalar dependencias y ejecutar base, API y frontend, en Windows, macOS o Linux. Para la versión online, [despliegue en Render](docs/operacion/despliegue-render.md).

## Si llegás a mantener el sistema

- [Guía de contribución](docs/guia-de-contribucion.md): qué leer y cómo llevar un cambio hasta el PR.
- [Modelo de datos](docs/modelo-de-datos.md): qué guarda cada app.
- [Traspaso de accesos](docs/operacion/traspaso-de-accesos.md): qué cuentas pasan a Big Media y cómo.

## Para quienes usan el sistema

- [Manual de uso](docs/manual/manual-de-uso.md).
- [Guion de capacitación](docs/manual/guion-de-capacitacion.md).

## Cómo se trabaja

- [`docs/guia-para-socios.md`](docs/guia-para-socios.md): explicación para un socio sin conocimientos de software.
- [`CLAUDE.md`](CLAUDE.md): reglas del repositorio (ramas GitFlow, commits, estándares y Definition of Done). Los cambios se integran por Pull Request a `develop`; `main` recibe solo releases y hotfixes.
- [`docs/README.md`](docs/README.md): índice de la documentación.
- [`docs/aidlc/roadmap.md`](docs/aidlc/roadmap.md): qué se está haciendo y qué viene.

## Material fuera de Git

El PDF de orden de compra de la carpeta local es una referencia privada y no forma parte del repositorio. Las historias originales también siguen fuera de Git; el repositorio guarda una copia en `docs/aidlc/inputs/`.
