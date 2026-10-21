"""Production settings as Django loads them in a fresh process."""

import json
import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def production_environment():
    return {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings",
        "DJANGO_ENV": "production",
        "DJANGO_DEBUG": "false",
        "DJANGO_SECRET_KEY": "test-only-production-secret-key-with-enough-characters",
        "RENDER_EXTERNAL_HOSTNAME": "bigmedia.onrender.com",
        "DATABASE_URL": "postgresql://u:p@db.internal:5432/bigmedia",
    }


def staging_environment():
    return {**production_environment(), "DJANGO_ENV": "staging"}


def run_django(script, env=None):
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_DIR,
        env=env or production_environment(),
        capture_output=True,
        text=True,
        check=False,
    )


def test_production_uses_render_database_host_and_https_settings():
    script = """
import json
from django.conf import settings
print(json.dumps({
    'db_host': settings.DATABASES['default']['HOST'],
    'allowed_hosts': settings.ALLOWED_HOSTS,
    'secure_cookies': settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE,
    'ssl_redirect': settings.SECURE_SSL_REDIRECT,
    'proxy_header': settings.SECURE_PROXY_SSL_HEADER,
    'hsts': settings.SECURE_HSTS_SECONDS,
}))
"""
    result = run_django(script)
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    assert config == {
        "db_host": "db.internal",
        "allowed_hosts": ["bigmedia.onrender.com"],
        "secure_cookies": True,
        "ssl_redirect": True,
        "proxy_header": ["HTTP_X_FORWARDED_PROTO", "https"],
        "hsts": 3600,
    }


def test_staging_is_hardened_like_production():
    script = """
import json
from django.conf import settings
print(json.dumps({
    'db_host': settings.DATABASES['default']['HOST'],
    'allowed_hosts': settings.ALLOWED_HOSTS,
    'secure_cookies': settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE,
    'ssl_redirect': settings.SECURE_SSL_REDIRECT,
    'debug': settings.DEBUG,
}))
"""
    result = run_django(script, staging_environment())
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    assert config == {
        "db_host": "db.internal",
        "allowed_hosts": ["bigmedia.onrender.com"],
        "secure_cookies": True,
        "ssl_redirect": True,
        "debug": False,
    }


def test_production_requires_database_url():
    env = production_environment()
    env.pop("DATABASE_URL")
    result = run_django(
        "from django.conf import settings; print(settings.DATABASES['default']['HOST'])", env
    )
    assert result.returncode != 0
    assert "DATABASE_URL" in result.stderr


def test_production_rejects_unknown_host_and_redirects_http():
    script = """
import json
import django
django.setup()
from django.test import Client
unknown = Client().get('/', HTTP_HOST='otro.example', HTTP_X_FORWARDED_PROTO='https')
http = Client().get('/', HTTP_HOST='bigmedia.onrender.com', HTTP_X_FORWARDED_PROTO='http')
print(json.dumps({'unknown': unknown.status_code, 'http': http.status_code, 'location': http.get('Location')}))
"""
    result = run_django(script)
    assert result.returncode == 0, result.stderr
    responses = json.loads(result.stdout)
    assert responses == {
        "unknown": 400,
        "http": 301,
        "location": "https://bigmedia.onrender.com/",
    }
