import json
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client


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
    assert client.get("/api/auth/me/").json() == {"username": "seba"}

    new_token = login_response.cookies["csrftoken"].value
    assert client.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=new_token).status_code == 200
    assert client.get("/api/auth/me/").status_code == 401
