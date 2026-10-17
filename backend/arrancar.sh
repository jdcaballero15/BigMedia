#!/bin/sh
# Arranque del servicio web: migra, asegura el primer administrador y levanta Gunicorn.
# Corre en cada arranque porque el plan gratis de Render no tiene comando previo al deploy.
set -e
python manage.py migrate --noinput
python manage.py asegurar_admin
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}"
