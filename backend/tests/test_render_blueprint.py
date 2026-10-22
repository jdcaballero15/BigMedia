"""Guard the production resources and deployment gate."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def blueprint():
    return yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))


def test_blueprint_uses_paid_plan_with_private_connection():
    manifest = blueprint()
    web = manifest["services"][0]
    database = manifest["databases"][0]
    env = {item["key"]: item for item in web["envVars"]}

    # Producción en planes pagos de Render (ADR-0005).
    assert web["plan"] == "starter"
    assert database["plan"] == "basic-256mb"
    assert database["ipAllowList"] == []
    assert web["region"] == database["region"]
    assert env["DATABASE_URL"]["fromDatabase"] == {
        "name": database["name"],
        "property": "connectionString",
    }
    assert env["DJANGO_SECRET_KEY"]["generateValue"] is True
    assert env["DJANGO_ENV"]["value"] == "production"


def test_blueprint_staging_reads_neon_url_from_secret():
    manifest = blueprint()
    staging = manifest["services"][1]
    env = {item["key"]: item for item in staging["envVars"]}

    # La base de staging vive en Neon (ADR-0005): su URL se carga en el panel, nunca en Git.
    assert staging["name"] == "bigmedia-web-staging"
    assert staging["plan"] == "free"
    assert staging["branch"] == "develop"
    assert env["DJANGO_ENV"]["value"] == "staging"
    assert env["DATABASE_URL"] == {"key": "DATABASE_URL", "sync": False}
    assert [db["name"] for db in manifest["databases"]] == ["bigmedia-db"]


def test_blueprint_asks_admin_credentials_without_storing_them():
    web = blueprint()["services"][0]
    env = {item["key"]: item for item in web["envVars"]}

    for clave in ("DJANGO_SUPERUSER_USERNAME", "DJANGO_SUPERUSER_PASSWORD"):
        assert env[clave] == {"key": clave, "sync": False}


def test_blueprint_only_deploys_checked_main_commits():
    web = blueprint()["services"][0]

    assert web["runtime"] == "docker"
    assert web["branch"] == "main"
    assert web["autoDeployTrigger"] == "checksPass"
    assert web["healthCheckPath"] == "/api/health/"
    # Sin comando previo al deploy: el arranque lo define la imagen (backend/arrancar.sh).
    assert "preDeployCommand" not in web
    assert "dockerCommand" not in web


def test_image_migrates_and_ensures_admin_before_serving():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    arranque = (ROOT / "backend" / "arrancar.sh").read_bytes().decode("utf-8")

    assert 'CMD ["sh", "arrancar.sh"]' in dockerfile
    assert "\r" not in arranque
    assert "set -e" in arranque
    migrar = arranque.index("python manage.py migrate --noinput")
    admin = arranque.index("python manage.py asegurar_admin")
    servidor = arranque.index("exec gunicorn config.wsgi:application")
    assert migrar < admin < servidor


def test_shell_scripts_keep_lf_line_endings():
    atributos = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()

    assert "*.sh text eol=lf" in atributos
