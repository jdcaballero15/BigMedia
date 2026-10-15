# Big Media Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar el repositorio BigMedia listo para desarrollar y ejecutar localmente una web React, una API Django y PostgreSQL sin perder los documentos existentes.

**Architecture:** Monorepo con `frontend/` y `backend/`, un PostgreSQL local mediante Compose y documentación en la raíz. La API se sirve bajo `/api/`; Vite redirige ese prefijo al servidor Django en desarrollo. Los módulos de negocio se crean cuando se implementa cada área, salvo una estructura mínima de usuarios y reservas si la requiere el arranque.

**Tech Stack:** Python 3.12, Django 5.2, Django REST Framework, PostgreSQL 17, React, TypeScript, Vite, Node 24, npm, Docker Compose.

**Spec:** `outputs/bigmedia-diseno-repositorio.md` (copiar a `docs/superpowers/specs/2026-10-14-bigmedia-repo-design.md` dentro del repositorio durante la tarea 1).

## Global Constraints

- Ruta local: `C:\Users\Juan Diego\Desktop\MendoData\proyectos\bigMedia`.
- Remoto: `https://github.com/jdcaballero15/BigMedia`.
- Conservar el documento de historias existente; no versionar el PDF de la orden de compra.
- No incluir secretos, datos personales reales ni archivos `.env` en Git.
- Esta entrega es infraestructura de desarrollo; no declara implementadas las 68 historias.
- El repositorio se abre desde su raíz en VS Code.

## Review Focus

1. Carpeta destino con archivos previos: la inicialización de Git los conserva; verificar sus hashes antes y después.
2. PDF privado en la raíz: `git status` y `git ls-files` deben demostrar que no entra al commit.
3. PostgreSQL sin arrancar: la API debe indicar que no está lista, sin devolver falsamente `ok`.
4. Base vacía: `migrate` debe crear el esquema estándar sin SQL manual.
5. Remoto sin acceso o credenciales: los commits locales deben quedar intactos y el README debe indicar cómo vincular/publicar cuando vuelva el acceso.

---

## Mapa de archivos de la primera entrega

- Raíz: `README.md`, `.gitignore`, `.env.example`, `compose.yaml`, `.vscode/extensions.json`, `.vscode/settings.json`.
- Requisitos: `docs/requisitos/historias-de-usuario.md`, `docs/superpowers/specs/2026-10-14-bigmedia-repo-design.md`, `docs/superpowers/plans/2026-10-15-bigmedia-base.md`.
- Backend: `backend/pyproject.toml`, `backend/manage.py`, `backend/config/settings.py`, `backend/config/urls.py`, `backend/config/asgi.py`, `backend/config/wsgi.py`, `backend/config/health.py`, `backend/tests/test_health.py`.
- Frontend: archivos generados por Vite bajo `frontend/`, más `frontend/src/app/`, `frontend/src/features/`, `frontend/src/shared/` cuando exista código real en ellos.
- Analítica y operaciones: crear `analytics/sql/`, `analytics/powerbi/`, `docs/operacion/` y `scripts/` cuando la siguiente etapa agregue contenido.

### Task 1: Repositorio local y protección de documentos

**Files:**
- Create: `.gitignore`, `README.md`, `.vscode/extensions.json`, `.vscode/settings.json`, `docs/requisitos/historias-de-usuario.md`, `docs/superpowers/specs/2026-10-14-bigmedia-repo-design.md`, `docs/superpowers/plans/2026-10-15-bigmedia-base.md`.
- Preserve: los dos archivos que hoy existen en la carpeta destino.

**Interfaces:**
- Consumes: carpeta destino y URL del remoto.
- Produces: raíz Git con `origin` configurado, documentos versionables y PDF excluido.

- [ ] **Step 1: Registrar el estado previo.** En PowerShell, listar la carpeta y obtener hashes SHA-256 de los dos archivos existentes con `Get-FileHash -LiteralPath` y `-Algorithm SHA256`. Guardar los hashes en las notas de ejecución, no en el repositorio.
- [ ] **Step 2: Inicializar Git de forma no destructiva.** Si `.git` no existe, ejecutar `git init -b main` en la carpeta destino. Si existe, leer `git status` y `git remote -v` antes de cambiar nada. Configurar `origin` con `git remote add origin https://github.com/jdcaballero15/BigMedia.git` solamente si no existe; si existe con otra URL, detenerse para investigar.
- [ ] **Step 3: Proteger el PDF y secretos.** Crear `.gitignore` con estas entradas:

```gitignore
.env
.env.*
!.env.example
**/.venv/
**/__pycache__/
**/.pytest_cache/
frontend/node_modules/
frontend/dist/
370 - OC 0001-00002111 - BigMedia - Exhibición - Arajet - Sept 2026.pdf
Historias de usuario - Sistema de reservas OOH (desarrollo a medida).md
```

- [ ] **Step 4: Incorporar los documentos.** Copiar las historias a `docs/requisitos/historias-de-usuario.md` y la especificación y este plan a las rutas indicadas. Conservar los originales. Crear un README inicial que explique el objetivo, la estructura y que la primera entrega todavía no implementa reservas.
- [ ] **Step 5: Verificar.** Ejecutar `git status --short`, `git check-ignore -v -- '370 - OC 0001-00002111 - BigMedia - Exhibición - Arajet - Sept 2026.pdf'` y repetir los hashes de los archivos originales. Deben coincidir.
- [ ] **Step 6: Commit.** Agregar solo los archivos previstos con rutas explícitas y crear `chore: initialize BigMedia repository`. Si GitHub no es accesible, conservar el commit local y registrar la causa exacta.

### Task 2: PostgreSQL y API Django mínima

**Files:**
- Create: `compose.yaml`, `.env.example`, `backend/pyproject.toml`, `backend/manage.py`, `backend/config/__init__.py`, `backend/config/settings.py`, `backend/config/urls.py`, `backend/config/asgi.py`, `backend/config/wsgi.py`, `backend/config/health.py`, `backend/tests/test_health.py`.
- Modify: `README.md`.

**Interfaces:**
- Consumes: variables `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_HOST`, `DB_PORT`.
- Produces: `GET /api/health/` con HTTP 200 y `{"status":"ok"}` cuando PostgreSQL responde; HTTP 503 y `{"status":"unavailable"}` cuando no responde.

- [ ] **Step 1: Definir dependencias y proyecto Django.** En `backend/pyproject.toml`, fijar Python `>=3.12`, Django `>=5.2,<6`, DRF `>=3.16,<4`, `psycopg[binary]>=3.2,<4`, pytest y pytest-django para desarrollo. Configurar pytest con `DJANGO_SETTINGS_MODULE = "config.settings"`. Crear `backend/.venv`, instalar el proyecto con sus dependencias de desarrollo y ejecutar `python -m django startproject config backend` desde la raíz.
- [ ] **Step 2: Escribir la prueba de salud.** `backend/tests/test_health.py` prueba ambas respuestas. El caso de error parchea `connection.ensure_connection()` para levantar `OperationalError`, sin detener Docker:

```python
from unittest.mock import patch

from django.db import OperationalError
from django.test import Client


def test_health_with_database(db):
    response = Client().get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_without_database(db):
    with patch("config.health.connection.ensure_connection", side_effect=OperationalError):
        response = Client().get("/api/health/")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
```

- [ ] **Step 3: Ejecutar la prueba en rojo.** Desde `backend/`, correr `python -m pytest tests/test_health.py -q`; debe fallar porque todavía no existe el endpoint.
- [ ] **Step 4: Crear la configuración mínima.** `settings.py` lee `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` y las variables de base desde el entorno, registra `rest_framework`, utiliza zona horaria `America/Argentina/Buenos_Aires`, y desactiva `DEBUG` salvo valor explícito de desarrollo. `config/health.py` implementa el endpoint y `urls.py` registra `path("api/health/", health)`:

```python
# backend/config/health.py
from django.db import OperationalError, connection
from django.http import JsonResponse


def health(request):
    try:
        connection.ensure_connection()
    except OperationalError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
```

- [ ] **Step 5: Configurar PostgreSQL local.** `compose.yaml` define un servicio `db` con `postgres:17-alpine`, volumen persistente y puerto local `5433:5432`. `.env.example` contiene `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_HOST`, `DB_PORT`, `DJANGO_SECRET_KEY` y `DJANGO_DEBUG`, con valores de ejemplo no productivos; el README indica copiarlo a `.env` y cambiar los secretos.
- [ ] **Step 6: Verificar la base limpia.** Ejecutar `docker compose up -d db`; instalar dependencias en `backend/.venv`; correr `python manage.py check`, `python manage.py migrate` y `python -m pytest tests/test_health.py -q`. El endpoint debe responder 200 con la base activa.
- [ ] **Step 7: Commit.** Crear `chore: add Django API and local PostgreSQL` después de revisar `git diff --check` y `git status --short`.

### Task 3: Frontend React y conexión de desarrollo

**Files:**
- Create: `frontend/package.json`, `frontend/package-lock.json`, `frontend/index.html`, `frontend/tsconfig*.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`, `frontend/src/app/App.tsx`, estilos mínimos.
- Modify: `README.md`, `.vscode/extensions.json`, `.vscode/settings.json`.

**Interfaces:**
- Consumes: `GET /api/health/` del backend.
- Produces: pantalla inicial que muestra el nombre del sistema y si la API responde, sin presentar módulos todavía no implementados.

- [ ] **Step 1: Generar la plantilla oficial.** Ejecutar `npm create vite@latest frontend -- --template react-ts`, luego `npm install` dentro de `frontend/`. Conservar `package-lock.json`.
- [ ] **Step 2: Configurar el proxy.** En `vite.config.ts`, agregar `server.proxy["/api"] = "http://127.0.0.1:8000"`; el frontend usa rutas relativas `/api/...`.
- [ ] **Step 3: Crear una pantalla de arranque honesta.** `App.tsx` solicita `/api/health/` al montar, muestra «API disponible» si recibe `status: ok` y «API no disponible» ante error o HTTP 503. Incluye el encabezado «Big Media» y una nota de que el sistema está en preparación.
- [ ] **Step 4: Verificar.** Ejecutar `npm run build` y `npm run lint`. Con backend y frontend levantados, abrir la web y comprobar ambos estados del indicador apagando y encendiendo la API.
- [ ] **Step 5: Commit.** Crear `chore: add React TypeScript frontend` tras revisar `git diff --check`.

### Task 4: Guía de trabajo y cierre de la primera entrega

**Files:**
- Modify: `README.md`.
- Create: `docs/operacion/desarrollo-local.md`.

**Interfaces:**
- Consumes: los tres componentes funcionando.
- Produces: instrucciones reproducibles para otra persona del equipo.

- [ ] **Step 1: Documentar comandos exactos de Windows.** Incluir clonación o apertura del repo, copia de `.env.example`, `docker compose up -d db`, creación de `backend/.venv`, instalación de Python, migración, arranque de Django, `npm ci`, `npm run dev`, URLs locales y comandos de verificación.
- [ ] **Step 2: Documentar límites.** Aclarar que ninguna historia funcional se considera terminada, que la confirmación de reservas será responsabilidad de la API y PostgreSQL, y dónde registrar decisiones de Seba.
- [ ] **Step 3: Prueba desde entorno limpio.** Con base y dependencias recreadas, ejecutar todos los comandos del README; comprobar migraciones, prueba de salud, compilación del frontend y ausencia de archivos privados en `git status` y `git ls-files`.
- [ ] **Step 4: Commit final.** Crear `docs: document local development` y confirmar `git status --short` limpio; el PDF y el documento original quedan ignorados, con una copia de este último versionada bajo `docs/requisitos/`.
- [ ] **Step 5: Publicar si el remoto responde.** Ejecutar `git fetch origin` antes de cualquier `push`; si el remoto tiene commits, integrar su historia sin forzar. Si está vacío y la autenticación funciona, ejecutar `git push -u origin main`. Nunca usar `--force`.
