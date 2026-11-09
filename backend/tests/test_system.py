"""Exercise HTTP behavior and injected database boundaries without a live server."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.settings import Settings
from app.main import create_app


class Probe:
    def __init__(self, status="connected", exception=None):
        self.status = status
        self.exception = exception
        self.calls = 0
        self.closed = False

    def check(self):
        self.calls += 1
        if self.exception:
            raise self.exception
        return self.status

    def close(self):
        self.closed = True


def config(**kwargs):
    return Settings(_env_file=None, app_env="test", database_url=None, **kwargs)


def test_health_does_not_touch_database_and_cleans_up():
    probe = Probe(exception=RuntimeError("database must not be called"))
    with TestClient(create_app(config(), probe)) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["phase"] == 0
        assert probe.calls == 0
        UUID(response.headers["X-Request-ID"])
        assert response.headers["Cache-Control"] == "no-store"
    assert probe.closed


@pytest.mark.parametrize(
    ("database_status", "http_status", "status"),
    [("connected", 200, "ready"), ("not_configured", 503, "not_ready")],
)
def test_readiness_reflects_database(database_status, http_status, status):
    probe = Probe(status=database_status)
    with TestClient(create_app(config(), probe)) as client:
        response = client.get("/api/v1/ready")
        assert response.status_code == http_status
        assert response.json()["status"] == status
        assert response.json()["database"] == database_status
        assert probe.calls == 1


def test_database_failure_is_sanitized_and_recovers():
    probe = Probe(exception=RuntimeError("postgresql://owner:private-password@private-host/db"))
    with TestClient(create_app(config(), probe)) as client:
        failed = client.get("/api/v1/ready")
        assert failed.status_code == 503
        assert failed.json()["database"] == "unavailable"
        assert "private-password" not in failed.text
        assert "private-host" not in failed.text
        probe.exception = None
        assert client.get("/api/v1/ready").status_code == 200


def test_cors_allows_only_configured_origins():
    with TestClient(
        create_app(config(cors_origins=["https://frontend.example"]), Probe())
    ) as client:
        allowed = client.get("/api/v1/health", headers={"Origin": "https://frontend.example"})
        denied = client.get("/api/v1/health", headers={"Origin": "https://other.example"})
        assert allowed.headers["Access-Control-Allow-Origin"] == "https://frontend.example"
        assert "Access-Control-Allow-Origin" not in denied.headers
        preflight = client.options(
            "/api/v1/health",
            headers={"Origin": "https://frontend.example", "Access-Control-Request-Method": "POST"},
        )
        assert preflight.status_code == 400


def test_feature_mutations_are_not_available():
    with TestClient(create_app(config(), Probe())) as client:
        for path in ("/api/v1/runs", "/api/v1/agents", "/api/v1/guest-sessions"):
            response = client.post(path, json={})
            assert response.status_code == 404
            assert response.json()["error"]["code"] == "not_found"
            assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_unexpected_exception_returns_safe_error_with_cors():
    application = create_app(config(cors_origins=["https://frontend.example"]), Probe())

    @application.get("/test-failure")
    def failure():
        raise RuntimeError("private exception text")

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/test-failure", headers={"Origin": "https://frontend.example"})
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "internal_error"
        assert "private exception text" not in response.text
        assert response.headers["Access-Control-Allow-Origin"] == "https://frontend.example"


def test_production_does_not_expose_interactive_docs():
    settings = Settings(_env_file=None, app_env="production", database_url=None)
    with TestClient(create_app(settings, Probe())) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404


@pytest.mark.parametrize("flag", ["public_runs_enabled", "public_llm_enabled"])
def test_phase_zero_rejects_execution_flags(flag):
    with pytest.raises(ValidationError):
        config(**{flag: True})


@pytest.mark.parametrize(
    "origin", ["*", "https://*.example", "https://example/path", "file://host"]
)
def test_cors_rejects_unsafe_configuration(origin):
    with pytest.raises(ValidationError):
        config(cors_origins=[origin])


def test_invalid_database_configuration_is_sanitized():
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, database_url="invalid://owner:private-password@host/db")
    assert "private-password" not in str(error.value)
