"""Django reads its environment file from backend/, next to the process that uses it."""

from pathlib import Path

from django.conf import settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_settings_lee_backend_env():
    assert settings.ENV_FILE == BACKEND_DIR / ".env"
