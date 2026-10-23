import json
from datetime import timedelta
from typing import Any
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone


def test_me_anonymous_returns_401_and_csrf_cookie():
    response = Client(enforce_csrf_checks=True).get("/api/auth/me/")

    assert response.status_code == 401
    assert response.json() == {"detail": "Iniciá sesión."}
    assert "csrftoken" in response.cookies


def test_login_requires_csrf():
    response = Client(enforce_csrf_checks=True).post(
        "/api/auth/login/",
        data=json.dumps({"username": "seba", "password": "incorrecta"}),
        content_type="application/json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_login_rejects_wrong_password():
    client = Client(enforce_csrf_checks=True)
    token = client.get("/api/auth/me/").cookies["csrftoken"].value
    with patch("config.auth_views.authenticate", return_value=None):
        response = client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "seba", "password": "incorrecta"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Usuario o contraseña incorrectos."}


def test_logout_requires_csrf_and_is_idempotent():
    client = Client(enforce_csrf_checks=True)
    token = client.get("/api/auth/me/").cookies["csrftoken"].value

    assert client.post("/api/auth/logout/").status_code == 403
    response = client.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=token)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_login_me_and_logout_revoke_session():
    get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    client = Client(enforce_csrf_checks=True)
    token = client.get("/api/auth/me/").cookies["csrftoken"].value

    login_response = client.post(
        "/api/auth/login/",
        data=json.dumps({"username": "seba", "password": "clave-segura-123"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert login_response.status_code == 200
    assert login_response.json() == {"username": "seba", "es_gerencia": False, "rol": "lectura"}
    assert client.get("/api/auth/me/").json() == {
        "username": "seba",
        "es_gerencia": False,
        "rol": "lectura",
    }

    new_token = login_response.cookies["csrftoken"].value
    assert client.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=new_token).status_code == 200
    assert client.get("/api/auth/me/").status_code == 401


@pytest.mark.django_db
def test_me_marca_es_gerencia_para_el_grupo_gerencia(gerencia_client):
    assert gerencia_client.get("/api/auth/me/").json()["es_gerencia"] is True


MENSAJE_BLOQUEO = "Demasiados intentos fallidos. Probá de nuevo en unos minutos."


def _cliente_con_csrf() -> tuple[Client, str]:
    client = Client(enforce_csrf_checks=True)
    token = client.get("/api/auth/me/").cookies["csrftoken"].value
    return client, token


def _ingresar(client: Client, token: str, username: str, password: str) -> Any:
    return client.post(
        "/api/auth/login/",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )


def _fallar(client: Client, token: str, username: str, veces: int) -> None:
    for _ in range(veces):
        _ingresar(client, token, username, "incorrecta")


@pytest.mark.django_db
def test_login_quinto_fallo_seguido_bloquea_la_cuenta():
    get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    client, token = _cliente_con_csrf()

    for _ in range(4):
        assert _ingresar(client, token, "seba", "incorrecta").status_code == 401
    respuesta = _ingresar(client, token, "seba", "incorrecta")

    assert respuesta.status_code == 429
    assert respuesta.json() == {"detail": MENSAJE_BLOQUEO}


@pytest.mark.django_db
def test_login_bloqueado_rechaza_la_contrasenia_correcta_con_429():
    get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    client, token = _cliente_con_csrf()
    _fallar(client, token, "seba", 5)

    respuesta = _ingresar(client, token, "seba", "clave-segura-123")

    assert respuesta.status_code == 429
    assert respuesta.json() == {"detail": MENSAJE_BLOQUEO}
    assert client.get("/api/auth/me/").status_code == 401


@pytest.mark.django_db
def test_login_bloqueado_usuario_inexistente_responde_igual_que_existente():
    get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    client, token = _cliente_con_csrf()
    _fallar(client, token, "seba", 5)
    _fallar(client, token, "nadie", 5)

    existente = _ingresar(client, token, "seba", "incorrecta")
    inexistente = _ingresar(client, token, "nadie", "incorrecta")

    assert existente.status_code == inexistente.status_code == 429
    assert existente.json() == inexistente.json()


@pytest.mark.django_db
def test_login_correcto_reinicia_el_contador_de_fallos():
    get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    client, token = _cliente_con_csrf()
    _fallar(client, token, "seba", 4)
    respuesta = _ingresar(client, token, "seba", "clave-segura-123")
    assert respuesta.status_code == 200

    client, token = _cliente_con_csrf()
    for _ in range(4):
        assert _ingresar(client, token, "seba", "incorrecta").status_code == 401


@pytest.mark.django_db
def test_login_bloqueo_vencido_permite_ingresar():
    from apps.usuarios.models import IntentoIngreso

    get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    client, token = _cliente_con_csrf()
    _fallar(client, token, "seba", 5)
    IntentoIngreso.objects.filter(username="seba").update(
        bloqueado_hasta=timezone.now() - timedelta(seconds=1)
    )

    assert _ingresar(client, token, "seba", "clave-segura-123").status_code == 200


@pytest.mark.django_db
def test_login_bloqueo_vencido_arranca_el_contador_de_cero():
    from apps.usuarios.models import IntentoIngreso

    client, token = _cliente_con_csrf()
    _fallar(client, token, "seba", 5)
    IntentoIngreso.objects.filter(username="seba").update(
        bloqueado_hasta=timezone.now() - timedelta(seconds=1)
    )

    assert _ingresar(client, token, "seba", "incorrecta").status_code == 401


@pytest.mark.django_db
def test_admin_login_respeta_el_bloqueo():
    get_user_model().objects.create_superuser(username="admin", password="clave-segura-123")
    client, token = _cliente_con_csrf()
    _fallar(client, token, "admin", 5)

    admin_client = Client()
    respuesta = admin_client.post(
        "/admin/login/?next=/admin/",
        {"username": "admin", "password": "clave-segura-123"},
    )

    assert respuesta.status_code == 200
    assert "_auth_user_id" not in admin_client.session


@pytest.mark.django_db
def test_login_usuario_se_normaliza_sin_distinguir_mayusculas():
    get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    client, token = _cliente_con_csrf()
    _fallar(client, token, "SEBA", 3)
    _fallar(client, token, "Seba", 2)

    assert _ingresar(client, token, "seba", "clave-segura-123").status_code == 429


@pytest.mark.django_db
def test_aauthenticate_respeta_el_bloqueo():
    from asgiref.sync import async_to_sync
    from django.core.exceptions import PermissionDenied

    from apps.usuarios.backends import BackendConBloqueo

    get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    client, token = _cliente_con_csrf()
    _fallar(client, token, "seba", 5)

    with pytest.raises(PermissionDenied):
        async_to_sync(BackendConBloqueo().aauthenticate)(
            None, username="seba", password="clave-segura-123"
        )
