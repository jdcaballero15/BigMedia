# Desarrollo local (Windows / PowerShell)

## Requisitos

- Python 3.12 o posterior.
- Node.js 24 o posterior y npm.
- Docker Desktop con el motor Linux en ejecución.

## PostgreSQL

Desde la raíz del repositorio:

```powershell
Copy-Item backend/.env.example backend/.env
```

Reemplazá `POSTGRES_PASSWORD` y `DJANGO_SECRET_KEY` en `backend/.env` por valores locales propios. Nunca subas `.env` a Git. Django y Compose leen ese archivo.

> Si tenías un `.env` en la raíz de una versión anterior, movelo a `backend/.env`; la raíz ya no se lee.

Luego:

```powershell
docker compose up -d --wait db
docker compose ps
```

PostgreSQL queda en `127.0.0.1:5433`. Los datos persisten en el volumen `postgres_data` de Compose.

## Instalación

Desde la raíz, una sola vez (no hace falta activar el entorno virtual):

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt -e backend/
.venv/Scripts/pre-commit.exe install
```

Si `ensurepip` falla porque Windows deniega la ruta temporal, establecé `TEMP` y `TMP` a una carpeta escribible dentro del proyecto antes de crear el entorno virtual.

## API

Desde la raíz:

```powershell
.venv/Scripts/python.exe backend/manage.py migrate
.venv/Scripts/python.exe backend/manage.py createsuperuser
.venv/Scripts/python.exe backend/manage.py runserver 127.0.0.1:8000
```

La migración crea los siete formatos, los nueve departamentos y los estados físicos. No crea carteles reales. Ingresá a `http://127.0.0.1:8000/admin/` con el superusuario para crear usuarios de Seba y Ale y asignarlos al grupo **Operativo**. El grupo permite administrar el inventario; cualquier usuario autenticado puede consultarlo. Las bajas de carteles se hacen cambiando su estado a **De baja**, y los catálogos se inactivan sin borrar el registro.

`http://127.0.0.1:8000/api/health/` responde `{"status":"ok"}` si la API accede a PostgreSQL y HTTP 503 si no puede conectarse.

## Tests

Los tests corren siempre contra PostgreSQL. Con la base levantada (`docker compose up -d --wait db`), desde la raíz:

```powershell
.venv/Scripts/python.exe -m pytest
```

Si la base no está levantada, la suite se detiene con un único mensaje que lo explica, en lugar de saltear tests o llenar la salida de errores. Las convenciones de los tests están en [`backend/tests/README.md`](../../backend/tests/README.md).

## Verificación completa

Antes de dar un cambio por terminado, corré los comandos de la Definition of Done de [`CLAUDE.md`](../../CLAUDE.md) (§7 y §9), desde la raíz y desde una rama de trabajo (el hook `no-commit-to-branch` hace fallar `pre-commit run --all-files` en `main` y `develop`):

```powershell
.venv/Scripts/ruff.exe format --check .
.venv/Scripts/ruff.exe check .
.venv/Scripts/mypy.exe backend
.venv/Scripts/python.exe backend/manage.py makemigrations --check --dry-run
.venv/Scripts/python.exe -m pytest --cov
.venv/Scripts/pre-commit.exe run --all-files
```

El hook de gitleaks de pre-commit revisa solo los cambios preparados (staged). La revisión completa del árbol la hace el job `secretos` del CI; si tenés el binario de gitleaks instalado, el equivalente local es:

```powershell
gitleaks detect --source . --no-git --redact
```

## Frontend

En otra terminal:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Abrí la URL que muestra Vite, normalmente `http://localhost:5173`. El proxy de desarrollo dirige `/api/` hacia Django. Para verificar el frontend (los mismos pasos que el job `frontend` del CI), desde `frontend/`:

```powershell
npm run format:check
npm run lint
npm run typecheck
npm run test:coverage
npm run build
```

> En un clon de Windows existente con `core.autocrlf=true`, `npm run format:check` puede marcar archivos que no tocaste (por los finales de línea CRLF). Corré una vez `npm run format` en `frontend/`: Git no muestra diferencias porque `.gitattributes` los guarda como LF.

Iniciá sesión con un usuario creado en Django. En **Carteles** podés filtrar por departamento, formato, modalidad y estado, buscar por dirección, crear o editar carteles y darles de baja. En **Catálogos** podés agregar o editar departamentos, formatos, proveedores y estados físicos. La capacidad de cada cartel se puede ajustar al cargarlo; los formatos parten de capacidad 1 hasta tener el relevamiento real. Ningún cartel debe cargarse con datos ficticios en la base operativa.

## Repositorio y datos

Los archivos `.env`, entornos virtuales, dependencias instaladas, compilados y el PDF privado están ignorados por Git. Usá datos ficticios o anonimizados en desarrollo y pruebas.

Si `git push` falla por credenciales, los commits locales permanecen intactos. Iniciá sesión en GitHub con el método habitual del equipo y luego ejecutá `git push -u origin <tu-rama>` y abrí el PR a `develop` (`main` solo recibe releases y hotfixes; ver [gestión de configuración](../gestion-de-configuracion.md)); no uses `--force`.
