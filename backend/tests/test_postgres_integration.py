import os

import pytest
from django.db import connection
from django.test import Client


@pytest.mark.skipif(
    os.environ.get("BIGMEDIA_RUN_DB_TESTS") != "1",
    reason="requires a running PostgreSQL service",
)
@pytest.mark.django_db
def test_health_with_real_postgresql():
    assert connection.vendor == "postgresql"
    response = Client().get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
