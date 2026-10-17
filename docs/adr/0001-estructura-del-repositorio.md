# ADR-0001 — Organizar el repositorio como monolito modular Django

- **Estado:** Aceptado
- **Fecha:** 2026-10-16
- **Decidido por:** Juan Diego
- **Módulos afectados:** usuarios, inventario, clientes, campanias, reservas, costos, facturacion, auditoria, frontend, infra, docs

---

## Contexto

Big Media ya tenía una base en Django + Django REST Framework y React + Vite + TypeScript, con una sola base PostgreSQL y despliegue en Render. El equipo es chico y los requisitos todavía se están ajustando con el uso (ver [ADR-0003](0003-requisitos-evolutivos.md)).

Hacía falta una organización clara de carpetas y de dependencias entre áreas de negocio, sin migrar de tecnología. El repositorio [CheatSheet](https://github.com/cheatsheet12/CheatSheet) sirvió de referencia: tiene gobernanza, documentación y controles que conviene adoptar, pero responde a otro negocio y a otro stack.

## Decisión

> Vamos a organizar Big Media como un monolito modular: cada área de negocio es una app de Django y el frontend espeja esas áreas en `features/<app>`.

- **Backend:** una app de Django por módulo en `backend/apps/<app>/`, con las apps `usuarios`, `inventario`, `clientes`, `campanias`, `reservas`, `costos`, `facturacion` y `auditoria`. Qué app puede importar de cuál está en la tabla de [`arquitectura.md`](../arquitectura.md#4-dependencias-permitidas-entre-apps) y se revisa en el PR.
- **Frontend:** `frontend/src/{app,features/<app>,shared}/`. Una feature no importa de otra; lo común sube a `shared/`.
- **Qué va en la raíz y qué en cada paquete:**

| Ubicación | Qué contiene |
| --- | --- |
| Raíz | `pyproject.toml` (ruff, mypy, pytest, coverage), `requirements-dev.txt`, `.pre-commit-config.yaml`, `.gitleaks.toml`, `compose.yaml`, `Dockerfile`, `render.yaml`, `CLAUDE.md`, `README.md`, `docs/`, `.claude/`, `.github/` |
| `backend/` | `backend/pyproject.toml` (solo empaquetado y dependencias de la aplicación), `backend/.env.example`, `manage.py`, `config/`, `apps/`, `tests/` |
| `frontend/` | `frontend/package.json` y su configuración (Prettier, oxlint, TypeScript, Vite) |

- No se crean carpetas nuevas en la raíz sin un ADR aprobado.

## Alternativas consideradas

| Alternativa | Ventajas | Por qué se descartó |
| --- | --- | --- |
| Arquitectura hexagonal por bounded context, como CheatSheet | Límites explícitos y dominio aislado del framework | Duplica capas sobre el ORM de Django para un equipo chico y con requisitos inestables: cada cambio de regla tocaría más archivos |
| Servicios separados | Despliegue y escala independientes por área | No hay necesidad de escalar por separado; sumaría operación (redes, versiones, múltiples bases) a un equipo chico |
| Límites entre apps verificados por herramienta (`import-linter`) | Una violación de dependencias rompe el CI | Descartada por ahora: con ocho apps la revisión del PR alcanza. Reconsiderar si las apps crecen |

## Consecuencias

**Positivas**
- Se aprovecha el stack existente sin migrar tecnología.
- Una sola unidad de despliegue y una sola base: transacciones de PostgreSQL simples para reglas críticas como la disponibilidad.
- El frontend y el backend comparten vocabulario (`features/<app>` espeja `apps/<app>`).

**Negativas / costo que aceptamos**
- Los límites entre apps dependen de la disciplina y de la revisión del PR; ninguna herramienta los verifica.
- Django y su ORM quedan acoplados al dominio.

**Qué se vuelve más difícil**
- Extraer una app a un servicio propio más adelante.
- Detectar a tiempo una dependencia indebida entre apps si la revisión del PR falla.

## Impacto en las reglas del repositorio

- [x] `CLAUDE.md`
- [ ] `docs/estandares-de-codigo.md`
- [ ] `pyproject.toml`, `requirements-dev.txt` o la configuración del frontend
- [ ] `.github/workflows/ci.yml`
- [ ] `backend/.env.example`
- [ ] Ninguna

## Referencias

- [`../arquitectura.md`](../arquitectura.md)
- [`CLAUDE.md`](../../CLAUDE.md)
- Unidad [`base-del-repositorio`](../aidlc/units/base-del-repositorio.md)
- Repositorio de referencia: [CheatSheet](https://github.com/cheatsheet12/CheatSheet)
