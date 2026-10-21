#!/bin/sh
# Arranque del servicio web: migra, asegura el primer administrador y levanta Gunicorn.
# Corre en cada arranque porque el plan gratis de Render no tiene comando previo al deploy.
set -e
python manage.py migrate --noinput
python manage.py asegurar_admin
# Solo staging arranca con datos de ejemplo (el comando se niega a correr en producción).
if [ "$DJANGO_ENV" = "staging" ]; then
  python manage.py cargar_datos_ejemplo
fi
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}"
