"""The browser app shares Django's origin without shadowing API or admin routes."""

from unittest.mock import patch

from django.conf import settings
from django.test import Client, override_settings


def test_root_serves_built_frontend(tmp_path):
    (tmp_path / "index.html").write_text("<main>BIGMEDIA_SPA</main>", encoding="utf-8")
    templates = [{**settings.TEMPLATES[0], "DIRS": [tmp_path]}]

    with override_settings(TEMPLATES=templates):
        response = Client().get("/")

    assert response.status_code == 200
    assert b"BIGMEDIA_SPA" in response.content


def test_api_and_admin_routes_keep_their_meaning():
    with patch("config.health.connection.ensure_connection"):
        health = Client().get("/api/health/")
    admin = Client().get("/admin/")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert admin.status_code == 302
    assert admin["Location"].startswith("/admin/login/")
