"""Settings for the Big Media API."""

import os
from pathlib import Path
from typing import Any

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend_dist"
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
PRODUCTION = os.environ.get("DJANGO_ENV") == "production"
DEBUG = not PRODUCTION and os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = (
    [os.environ["RENDER_EXTERNAL_HOSTNAME"]] if PRODUCTION else ["127.0.0.1", "localhost"]
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.inventario",
    "apps.clientes",
    "apps.campanias",
    "apps.reservas",
    "apps.costos",
    "apps.facturacion",
    "apps.usuarios",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if PRODUCTION:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [FRONTEND_DIST] if FRONTEND_DIST.exists() else [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"

DATABASES: dict[str, Any] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "bigmedia"),
        "USER": os.environ.get("POSTGRES_USER", "bigmedia"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5433"),
    }
}
if PRODUCTION:
    DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"])}
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600
    # El dominio es un subdominio de onrender.com que no controlamos y el preload de HSTS es
    # difícil de revertir. Revisar si se usa un dominio propio (ADR-0004).
    SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W021"]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [FRONTEND_DIST] if FRONTEND_DIST.exists() else []
if PRODUCTION:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Motor de disponibilidad (HU-033). Día de borde (RN-001) y si la tentativa bloquea (RN-002).
# Provisorios y configurables por entorno hasta que exista la configuración por pantalla (HU-001).
DISPONIBILIDAD_BORDE_INCLUSIVO = (
    os.environ.get("DISPONIBILIDAD_BORDE_INCLUSIVO", "true").lower() == "true"
)
DISPONIBILIDAD_TENTATIVA_BLOQUEA = (
    os.environ.get("DISPONIBILIDAD_TENTATIVA_BLOQUEA", "false").lower() == "true"
)

# Panel principal (HU-047): ventana de "reservas por vencer" en días.
PANEL_DIAS_POR_VENCER = int(os.environ.get("PANEL_DIAS_POR_VENCER", "30"))
