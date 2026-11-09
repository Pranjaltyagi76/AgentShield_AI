"""Optional real PostgreSQL checks; CI supplies a disposable service database."""

import os

import pytest
from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.db.connection import Database
from app.main import create_app


def test_unconfigured_database_is_not_ready():
    database = Database(Settings(_env_file=None, database_url=None))
    assert database.check() == "not_configured"
    database.close()


@pytest.mark.integration
def test_real_postgresql_connectivity():
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to verify a real PostgreSQL connection")
    settings = Settings(_env_file=None, app_env="test", database_url=database_url)
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        assert response.json()["database"] == "connected"
