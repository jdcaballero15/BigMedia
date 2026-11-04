from datetime import date

import psycopg
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client


def pytest_sessionstart(session: pytest.Session) -> None:
    """Stop the run when PostgreSQL is unreachable instead of failing test by test."""
    database = settings.DATABASES["default"]
    try:
        psycopg.connect(
            dbname=database["NAME"],
            user=database["USER"],
            password=database["PASSWORD"],
            host=database["HOST"],
            port=database["PORT"],
            connect_timeout=3,
        ).close()
    except psycopg.OperationalError as error:
        pytest.exit(
            "PostgreSQL no está disponible. Levantalo con `docker compose up -d db` "
            f"y revisá backend/.env. Detalle: {error}",
            returncode=3,
        )


@pytest.fixture(autouse=True)
def hoy_fijo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fija el «hoy» de RN-012 antes de las fechas de 2026 que usan los tests.

    Así las reservas de los tests no pasan a ser "con fecha pasada" a medida que pasan los días.
    Los tests de RN-012 fijan su propio día.
    """
    from apps.reservas import services

    monkeypatch.setattr(services, "hoy", lambda: date(2026, 1, 1))


@pytest.fixture
def operativo_client(db):
    user = get_user_model().objects.create_user(username="operativo", password="clave-segura-123")
    user.groups.add(Group.objects.get(name="Operativo"))
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def lector_client(db):
    user = get_user_model().objects.create_user(username="lector", password="clave-segura-123")
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def gerencia_client(db):
    user = get_user_model().objects.create_user(username="gerente", password="clave-segura-123")
    user.groups.add(Group.objects.get(name="Gerencia"))
    client = Client()
    client.force_login(user)
    return client
