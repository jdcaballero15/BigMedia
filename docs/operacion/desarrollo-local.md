# Desarrollo local

Cómo levantar base, API y frontend en tu máquina, desde un clon nuevo. Cada paso tiene los
comandos para **Windows (PowerShell)** y para **macOS o Linux (bash o zsh)**. Todos se corren
desde la raíz del repositorio, salvo que se indique otra carpeta.

## Requisitos

- Python 3.12 o posterior.
- Node.js 24 (la versión del CI) y npm.
- Docker con el motor en ejecución: Docker Desktop en Windows y macOS, o Docker Engine con el
  plugin Compose en Linux.
- Git.

## Clonar

```bash
git clone https://github.com/jdcaballero15/BigMedia.git
cd BigMedia
git switch develop
```

## PostgreSQL

Copiá el archivo de variables de ejemplo:

```powershell
# Windows
Copy-Item backend/.env.example backend/.env
```

```bash
# macOS o Linux
cp backend/.env.example backend/.env
```

Reemplazá `POSTGRES_PASSWORD` y `DJANGO_SECRET_KEY` en `backend/.env` por valores locales propios
(cualquier texto largo sirve en desarrollo). Nunca subas `.env` a Git. Django y Compose leen ese
archivo.

> Si tenías un `.env` en la raíz de una versión anterior, movelo a `backend/.env`; la raíz ya no
> se lee.

Luego, igual en los tres sistemas:

```bash
docker compose up -d --wait db
docker compose ps
```

PostgreSQL queda en `127.0.0.1:5433`. Los datos persisten en el volumen `postgres_data` de
Compose.

### Si el puerto 5433 está ocupado

Pasa si ya tenés otro PostgreSQL en ese puerto. Creá en la raíz un `compose.override.yaml` que
publique la base en otro puerto (por ejemplo 5434):

```yaml
# Archivo local: no se commitea.
services:
  db:
    ports: !override
      - "127.0.0.1:5434:5432"
```

Poné el mismo puerto en `DB_PORT` de `backend/.env` y volvé a correr `docker compose up -d --wait
db`. Compose lee el override solo, sin cambiar los comandos.

## Instalación

Una sola vez. No hace falta activar el entorno virtual:

```powershell
# Windows
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt -e backend/
.venv/Scripts/pre-commit.exe install
```

```bash
# macOS o Linux
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt -e backend/
.venv/bin/pre-commit install
```

Si en Windows `ensurepip` falla porque se deniega la ruta temporal, establecé `TEMP` y `TMP` a una
carpeta escribible dentro del proyecto antes de crear el entorno virtual.

Cuando una actualización suma dependencias (por ejemplo `openpyxl`), repetí la segunda línea.

## API

```powershell
# Windows
.venv/Scripts/python.exe backend/manage.py migrate
.venv/Scripts/python.exe backend/manage.py createsuperuser
.venv/Scripts/python.exe backend/manage.py runserver 127.0.0.1:8000
```

```bash
# macOS o Linux
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py createsuperuser
.venv/bin/python backend/manage.py runserver 127.0.0.1:8000
```

La migración crea los siete formatos, los nueve departamentos, los estados físicos, los grupos de
usuarios y los catálogos de facturación. No crea carteles ni clientes.

`http://127.0.0.1:8000/api/health/` responde `{"status":"ok"}` si la API accede a PostgreSQL y
HTTP 503 si no puede conectarse.

### Datos de ejemplo

Para tener carteles, clientes, campañas y reservas inventados con los que probar:

```powershell
# Windows
.venv/Scripts/python.exe backend/manage.py cargar_datos_ejemplo
```

```bash
# macOS o Linux
.venv/bin/python backend/manage.py cargar_datos_ejemplo
```

Todos los datos son ficticios (regla 6 de [`CLAUDE.md`](../../CLAUDE.md)). El comando se puede
repetir sin duplicar nada y se niega a correr en producción. Si `DJANGO_DEMO_PASSWORD` tiene un
valor en `backend/.env`, crea además los usuarios de demo `demo-operativo`, `demo-gerencia` y
`demo-lectura` con esa contraseña.

### Usuarios

Ingresá a la aplicación con el superusuario y creá las cuentas desde **Administración ›
Usuarios**, una por persona, con el rol que corresponda (Administrador, Operativo o Lectura) y,
si va a ver ingresos y auditoría, el permiso de Gerencia. Con **Link de contraseña** el sistema
genera un link de un solo uso para que la persona defina su contraseña; copialo y pasáselo. También
se puede hacer desde `http://127.0.0.1:8000/admin/`.

## Tests

Los tests corren siempre contra PostgreSQL. Con la base levantada:

```powershell
# Windows
.venv/Scripts/python.exe -m pytest
```

```bash
# macOS o Linux
.venv/bin/python -m pytest
```

Si la base no está levantada, la suite se detiene con un único mensaje que lo explica, en lugar de
saltear tests o llenar la salida de errores. Las convenciones de los tests están en
[`backend/tests/README.md`](../../backend/tests/README.md).

## Frontend

En otra terminal:

```powershell
# Windows
Set-Location frontend
npm ci
npm run dev
```

```bash
# macOS o Linux
cd frontend
npm ci
npm run dev
```

Abrí la URL que muestra Vite, normalmente `http://localhost:5173`, e ingresá con un usuario creado
en Django. El proxy de desarrollo manda `/api/` a Django en `http://127.0.0.1:8000`, así que la
API tiene que estar en ese puerto (está fijo en `frontend/vite.config.ts`).

Si al levantar Vite falta un paquete (pasa cuando una actualización suma uno), volvé a correr
`npm ci` en `frontend/`.

## Verificación completa

Antes de dar un cambio por terminado, corré los comandos de la Definition of Done de
[`CLAUDE.md`](../../CLAUDE.md) (§7 y §9), desde una rama de trabajo: el hook `no-commit-to-branch`
hace fallar `pre-commit run --all-files` en `main` y `develop`.

```powershell
# Windows
.venv/Scripts/ruff.exe format --check .
.venv/Scripts/ruff.exe check .
.venv/Scripts/mypy.exe backend
.venv/Scripts/python.exe backend/manage.py makemigrations --check --dry-run
.venv/Scripts/python.exe -m pytest --cov
.venv/Scripts/pre-commit.exe run --all-files
```

```bash
# macOS o Linux
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy backend
.venv/bin/python backend/manage.py makemigrations --check --dry-run
.venv/bin/python -m pytest --cov
.venv/bin/pre-commit run --all-files
```

Y desde `frontend/` (los mismos pasos que el job `frontend` del CI):

```bash
npm run format:check
npm run lint
npm run typecheck
npm run test:coverage
npm run build
```

El hook de gitleaks de pre-commit revisa solo los cambios preparados (staged). La revisión completa
del árbol la hace el job `secretos` del CI; si tenés el binario de gitleaks instalado, el
equivalente local es:

```bash
gitleaks detect --source . --no-git --redact
```

> En un clon de Windows existente con `core.autocrlf=true`, `npm run format:check` puede marcar
> archivos que no tocaste (por los finales de línea CRLF). Corré una vez `npm run format` en
> `frontend/`: Git no muestra diferencias porque `.gitattributes` los guarda como LF.

## Qué hay en la aplicación

Cómo usar cada pantalla está en el [manual de uso](../manual/manual-de-uso.md). Ningún dato
ficticio se carga en la base operativa: los datos de ejemplo son solo para desarrollo y staging.

## Repositorio y datos

Los archivos `.env`, entornos virtuales, dependencias instaladas, compilados y el PDF privado están
ignorados por Git. Usá datos ficticios o anonimizados en desarrollo y pruebas.

Si `git push` falla por credenciales, los commits locales permanecen intactos. Iniciá sesión en
GitHub con el método habitual del equipo y luego ejecutá `git push -u origin <tu-rama>` y abrí el
PR a `develop` (`main` solo recibe releases y hotfixes; ver
[gestión de configuración](../gestion-de-configuracion.md)); no uses `--force`.
