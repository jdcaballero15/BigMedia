import pytest
from django.db import connection
from django.test import Client


@pytest.mark.django_db
def test_health_with_real_postgresql():
    assert connection.vendor == "postgresql"
    response = Client().get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
