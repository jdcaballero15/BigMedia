from unittest.mock import patch

from django.db import OperationalError
from django.test import Client


def test_health_with_database():
    with patch("config.health.connection.ensure_connection"):
        response = Client().get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_without_database():
    with patch("config.health.connection.ensure_connection", side_effect=OperationalError):
        response = Client().get("/api/health/")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
