"""Guard the production resources and deployment gate."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def blueprint():
    return yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))


def test_blueprint_uses_paid_private_postgres_and_private_connection():
    manifest = blueprint()
    web = manifest["services"][0]
    database = manifest["databases"][0]
    env = {item["key"]: item for item in web["envVars"]}

    assert web["plan"] != "free"
    assert database["plan"] != "free"
    assert database["ipAllowList"] == []
    assert web["region"] == database["region"]
    assert env["DATABASE_URL"]["fromDatabase"] == {
        "name": database["name"],
        "property": "connectionString",
    }
    assert env["DJANGO_SECRET_KEY"]["generateValue"] is True
    assert env["DJANGO_ENV"]["value"] == "production"


def test_blueprint_only_deploys_checked_main_commits_after_migration():
    web = blueprint()["services"][0]

    assert web["runtime"] == "docker"
    assert web["branch"] == "main"
    assert web["autoDeployTrigger"] == "checksPass"
    assert web["preDeployCommand"] == "python manage.py migrate --noinput"
    assert web["healthCheckPath"] == "/api/health/"
