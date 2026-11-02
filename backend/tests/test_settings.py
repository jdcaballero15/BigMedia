"""Django reads its environment file from backend/, next to the process that uses it."""

from pathlib import Path

from django.conf import settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_settings_lee_backend_env():
    assert settings.ENV_FILE == BACKEND_DIR / ".env"


def test_session_save_every_request_esta_activo():
    assert settings.SESSION_SAVE_EVERY_REQUEST is True


def test_session_cookie_age_es_1800_por_defecto():
    # 30 minutos * 60 segundos = 1800 (HU-003 criterio 4)
    assert settings.SESSION_COOKIE_AGE == 1800


def test_settings_bloqueo_por_defecto_cinco_intentos_quince_minutos():
    assert settings.LOGIN_MAX_INTENTOS == 5
    assert settings.LOGIN_BLOQUEO_MINUTOS == 15
    assert settings.AUTHENTICATION_BACKENDS == ["apps.usuarios.backends.BackendConBloqueo"]
