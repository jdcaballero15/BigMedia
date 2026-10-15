# Desarrollo local (Windows / PowerShell)

## Requisitos

- Python 3.12 o posterior.
- Node.js 24 o posterior y npm.
- Docker Desktop con el motor Linux en ejecución.

## PostgreSQL

Desde la raíz del repositorio:

```powershell
Copy-Item .env.example .env
```

Reemplazá `POSTGRES_PASSWORD` y `DJANGO_SECRET_KEY` en `.env` por valores locales propios. Nunca subas `.env` a Git. Luego:

```powershell
docker compose up -d db
docker compose ps
```

PostgreSQL queda en `127.0.0.1:5433`. Los datos persisten en el volumen `postgres_data` de Compose.

## API

Desde la raíz:

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -e './backend[dev]'
backend/.venv/Scripts/python.exe backend/manage.py migrate
backend/.venv/Scripts/python.exe backend/manage.py runserver 127.0.0.1:8000
```

Si `ensurepip` falla porque Windows deniega la ruta temporal, establecé `TEMP` y `TMP` a una carpeta escribible dentro del proyecto antes de crear el entorno virtual.

En otra terminal:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
backend/.venv/Scripts/python.exe backend/manage.py check
```

`http://127.0.0.1:8000/api/health/` responde `{"status":"ok"}` si la API accede a PostgreSQL y HTTP 503 si no puede conectarse.

## Frontend

En otra terminal:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Abrí la URL que muestra Vite, normalmente `http://localhost:5173`. El proxy de desarrollo dirige `/api/` hacia Django. Para verificar el frontend:

```powershell
npm test
npm run lint
npm run build
```

## Repositorio y datos

Los archivos `.env`, entornos virtuales, dependencias instaladas, compilados y el PDF privado están ignorados por Git. Usá datos ficticios o anonimizados en desarrollo y pruebas.

Si `git push` falla por credenciales, los commits locales permanecen intactos. Iniciá sesión en GitHub con el método habitual del equipo y luego ejecutá `git push -u origin main`; no uses `--force`.
