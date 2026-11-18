"""Optional real PostgreSQL checks; CI supplies a disposable service database."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from app.core.settings import Settings
from app.db.connection import Database, migration_settings
from app.main import create_app


def test_unconfigured_database_is_not_ready():
    database = Database(Settings(_env_file=None, database_url=None))
    assert database.check() == "not_configured"
    database.close()


def test_migrations_use_direct_neon_host_without_changing_runtime_credentials():
    source = "postgresql://owner:synthetic-test-password@ep-example-pooler.ap-southeast-1.aws.neon.tech/agentshield?sslmode=require"
    settings = Settings(_env_file=None, database_url=source)
    migrated = migration_settings(settings)
    assert settings.database_url.get_secret_value() == source
    direct = make_url(migrated.database_url.get_secret_value())
    assert direct.host == "ep-example.ap-southeast-1.aws.neon.tech"
    assert direct.password == "synthetic-test-password" and direct.query["sslmode"] == "require"
    local = Settings(_env_file=None, database_url="postgresql://owner@127.0.0.1/test")
    assert migration_settings(local) is local


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
