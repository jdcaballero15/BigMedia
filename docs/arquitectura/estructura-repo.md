# Estructura del repositorio

Big Media usa un monorepo. La [estructura de CheatSheet](https://github.com/cheatsheet12/CheatSheet) sirvió como referencia para separar aplicaciones, documentación y controles del repositorio; sus módulos y tecnologías responden a otro negocio.

| Ruta | Responsabilidad |
| --- | --- |
| `backend/` | API Django, modelos, migraciones, autenticación y pruebas. Las aplicaciones de negocio viven en `backend/apps/<modulo>/` cuando se implementan. |
| `frontend/` | Web React + TypeScript. Cada flujo de negocio vive en `frontend/src/features/<modulo>/`; `app/` compone pantallas y `shared/` contiene código realmente compartido. |
| `docs/requisitos/` | Historias de usuario y reglas acordadas. |
| `docs/arquitectura/` | Decisiones de estructura y límites de módulos. |
| `docs/operacion/` | Desarrollo local, despliegue y recuperación. |
| `docs/superpowers/` | Especificaciones y planes de implementación. |
| `analytics/` | Futuras vistas y archivos de Power BI. |
| `.github/` | CI y plantilla de PR. |
| raíz | Archivos que gobiernan ambos lados: `README.md`, `compose.yaml`, `Dockerfile`, `render.yaml` y reglas de Git. |

Los módulos se nombran por conceptos de Big Media: inventario, clientes, campañas, reservas y reportes cuando existan. Un módulo no importa detalles internos de otro para tomar decisiones de negocio; las reglas compartidas se ubican en una interfaz explícita o en código compartido acotado. No se crean carpetas vacías para funciones futuras.

El flujo de ramas sigue `CONTRIBUTING.md` cuando el PR de inventario se integre: rama de trabajo y PR hacia `main`, con CI obligatorio. No se adopta la rama permanente `develop` de CheatSheet porque Big Media aún tiene un equipo y una cadencia de despliegue pequeños. Django y Vite permanecen: esta guía es de **organización**, no una migración a FastAPI o Next.js.
