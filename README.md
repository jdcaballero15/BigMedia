# Big Media Argentina

Monorepo del sistema de inventario, campañas y reservas de publicidad de vía pública.

## Estado

La base de desarrollo contiene una aplicación React + TypeScript, una API Django REST Framework y PostgreSQL mediante Docker Compose. El primer módulo funcional permite iniciar sesión y administrar el inventario de carteles y sus catálogos. Las campañas y reservas siguen pendientes; esta versión **no permite confirmar reservas ni calcula disponibilidad**.

## Carpetas

- `frontend/`: aplicación web y pruebas de interfaz.
- `backend/`: API, configuración de Django y pruebas.
- `docs/requisitos/`: historias de usuario vigentes.
- `docs/superpowers/`: diseño y plan de la primera entrega.
- `docs/operacion/`: pasos para ejecutar el proyecto.
- `analytics/`: futuras vistas SQL y archivos de Power BI.

Abrí la carpeta raíz `bigMedia` en VS Code. Seguí [desarrollo local](docs/operacion/desarrollo-local.md) para instalar dependencias y ejecutar los tres componentes.

Todo cambio se integra a `main` mediante Pull Request. Consultá el [flujo de trabajo](CONTRIBUTING.md) antes de comenzar una tarea.

## Reglas de trabajo

La API será la autoridad para confirmar reservas. La disponibilidad se protegerá con transacciones en PostgreSQL y pruebas de concurrencia. Las decisiones pendientes de Seba y Administración deben registrarse en `docs/decisiones/` antes de cerrar las reglas afectadas. No se cargan datos personales reales en desarrollo o pruebas.

El PDF de orden de compra que está en la carpeta local es una referencia privada y no forma parte del repositorio. Las historias originales siguen allí; Git guarda una copia en `docs/requisitos/`.
