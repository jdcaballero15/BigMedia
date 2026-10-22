"""Without PostgreSQL the suite stops with a clear message instead of skipping tests."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_suite_stops_when_postgresql_is_unreachable():
    env = {**os.environ, "DB_HOST": "127.0.0.1", "DB_PORT": "1"}

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "backend/tests/test_health.py", "-q"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 3
    assert "PostgreSQL no está disponible" in result.stdout + result.stderr
