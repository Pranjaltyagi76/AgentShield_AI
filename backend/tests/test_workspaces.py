"""Phase 1 acceptance tests. CI migrates a disposable PostgreSQL database first."""

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.workspaces import cleanup, digest
from app.core.settings import Settings
from app.db.models import Agent, Guest, Version
from app.main import create_app


@pytest.fixture
def workspace():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not configured")
    app = create_app(Settings(_env_file=None, app_env="test", database_url=url))
    guests = []
    with TestClient(app, base_url="http://testserver/api/v1/") as c:

        def issue():
            response = c.post("guest-sessions")
            assert response.status_code == 201, response.text
            token = response.json()["credential"]
            guests.append(digest(token))
            return {"Authorization": "Bearer " + token}

        try:
            yield c, issue, app.state.database.engine
        finally:
            with Session(app.state.database.engine) as db, db.begin():
                for g in db.scalars(select(Guest).where(Guest.credential_hash.in_(guests))):
                    db.delete(g)


def test_isolation_and_versions(workspace):
    c, issue, engine = workspace
    a, b = issue(), issue()
    profile = c.post("agents", json={"name": "Private"}, headers=a).json()
    path = "agents/" + profile["id"]
    v1 = profile["versions"][0]
    assert c.get(path, headers=a).json()["name"] == "Private"
    assert c.get(path, headers=b).status_code == 404
    assert c.get(path).status_code == 404
    assert profile["id"] not in c.get("agents", headers=b).text
    assert c.patch(path, json={"name": "Changed"}, headers=b).status_code == 404
    assert c.post(path + "/versions", json={}, headers=b).status_code == 404
    assert c.get(path + "/versions/" + v1["id"], headers=b).status_code == 404
    own = c.post("agents", json={"name": "B"}, headers=b).json()
    assert c.get("agents/" + own["id"] + "/versions/" + v1["id"], headers=b).status_code == 404
    assert (
        c.patch(path, json={"description": "Updated only"}, headers=a).json()["name"] == "Private"
    )
    assert c.patch(path, json={"name": "Renamed"}, headers=a).json()["name"] == "Renamed"
    assert (
        c.post(path + "/versions", json={"system_prompt": "Second revision"}, headers=a).json()[
            "version_number"
        ]
        == 2
    )
    assert c.get(path + "/versions/" + v1["id"], headers=a).json() == v1
    assert c.post("agents", json={"name": "spoof", "is_shared": True}, headers=a).status_code == 422
    assert c.post("agents", json={"name": "anonymous"}).status_code == 401
    shared = c.get("agents").json()
    assert len(shared) == 2
    for item in shared:
        assert (
            c.patch("agents/" + item["id"], json={"name": "overwrite"}, headers=a).status_code
            == 403
        )
        assert c.post("agents/" + item["id"] + "/versions", json={}, headers=a).status_code == 403
    assert c.delete("guest-session", headers=a).status_code == 204
    assert c.get(path, headers=a).status_code == 401
    with Session(engine) as s:
        assert s.get(Agent, UUID(profile["id"])) is None
        assert s.get(Version, UUID(v1["id"])) is None


def test_expiry_before_and_after_cleanup(workspace):
    c, issue, engine = workspace
    a = issue()
    token = a["Authorization"].split()[1]
    obj = c.post("agents", headers=a, json={"name": "Expires"}).json()
    with Session(engine) as s, s.begin():
        g = s.scalar(select(Guest).where(Guest.credential_hash == digest(token)))
        assert g.credential_hash != token
        assert timedelta(days=6) < g.expires_at - datetime.now(UTC) <= timedelta(days=7)
        g.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert c.get("guest-session", headers=a).status_code == 401
    assert c.post("agents", headers=a, json={"name": "Expired"}).status_code == 401
    cleanup(engine)
    with Session(engine) as s:
        assert s.get(Agent, UUID(obj["id"])) is None
        assert s.get(Version, UUID(obj["versions"][0]["id"])) is None


def test_curated_catalog_and_limits(workspace):
    c, issue, _ = workspace
    rows = c.get("scenarios").json()
    assert [r["id"] for r in rows] == [f"AS-{i:03}" for i in range(1, 13)]
    for r in rows:
        assert set(r) == {"id", "name", "description", "version", "category", "severity"}
        assert c.get("scenarios/" + r["id"]).json() == r
    assert len(c.get("scenario-suites").json()[0]["members"]) == 12
    assert c.get("scenarios?q=AS-004").json() == [rows[3]]
    assert not c.get("scenarios?category=unknown").json()
    a = issue()
    assert (
        c.post(
            "agents",
            headers=a,
            json={"name": "bad", "configuration": {"system_prompt": "é" * 9000}},
        ).status_code
        == 422
    )
    assert c.post("agents", headers=a, content=b" " * 65537).status_code == 413
    path = "agents/" + c.post("agents", json={"name": "Bounded"}, headers=a).json()["id"]
    for _ in range(3):
        assert c.post(path + "/versions", json={}, headers=a).status_code == 201
    assert c.post(path + "/versions", json={}, headers=a).status_code == 409
    for _ in range(7):
        assert c.post("agents", json={"name": "Bounded"}, headers=a).status_code == 201
    assert c.post("agents", json={"name": "Full"}, headers=a).status_code == 409
    for _ in range(7):
        issue()
    limited = c.post("guest-sessions")
    assert limited.status_code == 429 and int(limited.headers["Retry-After"]) > 0
