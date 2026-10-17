FROM node:24-alpine AS frontend

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app/backend
COPY backend/ ./
RUN pip install --no-cache-dir .
COPY --from=frontend /app/frontend/dist/ ./frontend_dist/
RUN DJANGO_ENV=production \
    DJANGO_SECRET_KEY=build-only \
    DATABASE_URL=postgresql://build:build@localhost:5432/build \
    RENDER_EXTERNAL_HOSTNAME=build.invalid \
    python manage.py collectstatic --noinput

EXPOSE 10000
CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000}"]
