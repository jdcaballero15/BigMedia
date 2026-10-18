# Big Media Argentina

Sistema de inventario, campañas y reservas de publicidad de vía pública. Es un monorepo con una API Django REST Framework sobre PostgreSQL y una aplicación web React + TypeScript.

## Estado

El inventario está disponible: inicio de sesión y administración de carteles y sus catálogos. Las campañas y las reservas **no están implementadas**: esta versión no permite confirmar reservas ni calcula disponibilidad.

## Cómo arrancar

Seguí [desarrollo local](docs/operacion/desarrollo-local.md) para instalar dependencias y ejecutar base, API y frontend. Abrí la carpeta raíz `bigMedia` en VS Code. Para la versión online, [despliegue en Render](docs/operacion/despliegue-render.md).

## Cómo se trabaja

- [`docs/guia-para-socios.md`](docs/guia-para-socios.md): explicación para un socio sin conocimientos de software.
- [`CLAUDE.md`](CLAUDE.md): reglas del repositorio (ramas GitFlow, commits, estándares y Definition of Done). Los cambios se integran por Pull Request a `develop`; `main` recibe solo releases y hotfixes.
- [`docs/README.md`](docs/README.md): índice de la documentación.
- [`docs/aidlc/roadmap.md`](docs/aidlc/roadmap.md): qué se está haciendo y qué viene.

## Material fuera de Git

El PDF de orden de compra de la carpeta local es una referencia privada y no forma parte del repositorio. Las historias originales también siguen fuera de Git; el repositorio guarda una copia en `docs/aidlc/inputs/`.
