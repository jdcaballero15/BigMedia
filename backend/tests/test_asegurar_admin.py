import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.fixture
def credenciales(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "admin-render")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "clave-larga-de-prueba-123")


def test_asegurar_admin_sin_variables_no_crea_usuario(db, monkeypatch):
    monkeypatch.delenv("DJANGO_SUPERUSER_USERNAME", raising=False)
    monkeypatch.delenv("DJANGO_SUPERUSER_PASSWORD", raising=False)

    call_command("asegurar_admin")

    assert not get_user_model().objects.exists()


def test_asegurar_admin_crea_superusuario_si_no_existe(db, credenciales):
    call_command("asegurar_admin")

    usuario = get_user_model().objects.get(username="admin-render")
    assert usuario.is_superuser
    assert usuario.is_staff
    assert usuario.check_password("clave-larga-de-prueba-123")


def test_asegurar_admin_existente_no_cambia_la_clave(db, credenciales):
    get_user_model().objects.create_superuser(
        username="admin-render", password="clave-cambiada-en-admin"
    )

    call_command("asegurar_admin")

    usuario = get_user_model().objects.get(username="admin-render")
    assert usuario.check_password("clave-cambiada-en-admin")
    assert get_user_model().objects.count() == 1


def test_asegurar_admin_con_usuario_sin_clave_falla(db, monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "admin-render")
    monkeypatch.delenv("DJANGO_SUPERUSER_PASSWORD", raising=False)

    with pytest.raises(CommandError, match="DJANGO_SUPERUSER_PASSWORD"):
        call_command("asegurar_admin")

    assert not get_user_model().objects.exists()
