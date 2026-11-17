"""Export lifecycle over real PostgreSQL, including restart regeneration."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_local_runs import harness as local_harness
from test_local_runs import submit

from app import main, run_queue
from app.api import reports
from app.core.settings import Settings
from app.db.models import Guest
from app.db.runs import Event, Report, Result, Run
from app.reporting import render_html
from app.suite import PRIVATE_MARKER

harness = local_harness


def test_html_escapes_every_value_and_links_only_local_evidence():
    attack = '<script>alert("x")</script><img src=x onerror=alert(1)>'
    result = render_html(
        {
            "metadata": attack,
            "findings": [
                {
                    "scenario_id": attack,
                    "severity": "high",
                    "summary": attack,
                    "remediation": attack,
                    "evidence_id": '" onclick="alert(1)',
                }
            ],
            "evidence": [
                {
                    "id": '" onclick="alert(1)',
                    "scenario_id": attack,
                    "sequence": 1,
                    "kind": attack,
                    "payload": {"answer": attack},
                }
            ],
        }
    )
    assert "<script>" not in result and "<img" not in result
    assert "&lt;script&gt;" in result and "&quot;" in result
    assert "default-src 'none'" in result


def test_report_ownership_regeneration_comparison_and_cleanup(harness, monkeypatch):
    client, workspace, engine, settings = harness
    auth, version = workspace("vulnerable")
    other, other_version = workspace()
    first = submit(client, auth, version, scenarios=["AS-003", "AS-011"]).json()["id"]
    path = "runs/" + first + "/reports"
    assert client.post(path, headers=auth, json={"format": "json"}).status_code == 409
    worker = uuid4()
    for _ in range(15):
        run_queue.tick(engine, worker)
    second = submit(client, auth, version, scenarios=["AS-011"], key="second").json()["id"]
    foreign = submit(client, other, other_version).json()["id"]
    for _ in range(15):
        run_queue.tick(engine, worker)
    comp = client.post(
        "benchmarks/compare",
        headers=auth,
        json={"baseline_run_id": first, "candidate_run_id": second},
    ).json()["id"]
    assert (
        client.post(
            "runs/" + foreign + "/reports", headers=auth, json={"format": "html"}
        ).status_code
        == 404
    )
    assert client.post(path, headers=other, json={"format": "html"}).status_code == 404
    assert client.post(path, headers=auth, json={"format": "pdf"}).status_code == 422
    foreign_second = submit(client, other, other_version, key="other-second").json()["id"]
    for _ in range(15):
        run_queue.tick(engine, worker)
    foreign_comp = client.post(
        "benchmarks/compare",
        headers=other,
        json={"baseline_run_id": foreign, "candidate_run_id": foreign_second},
    ).json()["id"]
    assert (
        client.post(
            path,
            headers=auth,
            json={"format": "json", "comparison_id": foreign_comp},
        ).status_code
        == 404
    )

    def create():
        return client.post(path, headers=auth, json={"format": "json", "comparison_id": comp})

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(create) for _ in range(2)]
        responses = [f.result(timeout=10) for f in futures]
    assert sorted(r.status_code for r in responses) == [200, 201]
    assert responses[0].json() == responses[1].json()
    record = responses[0].json()
    download = "reports/" + record["id"] + "/download"
    body = client.get(download, headers=auth)
    assert body.status_code == 200
    payload = body.json()
    assert payload["metrics"]["coverage"]["numerator"] == 2
    assert payload["comparison"]["baseline"]["id"] == first
    assert payload["findings"] and payload["severity_breakdown"]
    assert "credential" not in body.text and PRIVATE_MARKER not in body.text
    assert auth["Authorization"].split()[1] not in body.text
    ids = {e["id"] for e in payload["evidence"]}
    assert all(f["evidence_id"] in ids for f in payload["findings"])
    assert client.get("reports", headers=auth).json()[0]["id"] == record["id"]
    for suffix in ("", "/download"):
        assert client.get("reports/" + record["id"] + suffix, headers=other).status_code == 404
        assert client.get("reports/" + record["id"] + suffix).status_code == 401
    # A new API/application instance regenerates the identical export from PostgreSQL.
    fresh = main.create_app(
        Settings(
            _env_file=None,
            app_env="test",
            local_runs_enabled=True,
            database_url=settings.database_url,
        )
    )
    with TestClient(
        fresh, base_url="http://127.0.0.1/api/v1/", client=("127.0.0.1", 3333)
    ) as restarted:
        assert restarted.get(download, headers=auth).content == body.content
    assert 'attachment; filename="agentshield-' in body.headers["content-disposition"]
    assert "sandbox" in body.headers["content-security-policy"]

    html = client.post(path, headers=auth, json={"format": "html"}).json()
    # Stored user/model values stay escaped even if historical evidence contains markup.
    with Session(engine) as s, s.begin():
        result = s.query(Result).filter(Result.run_id == UUID(first)).first()
        event = (
            s.query(Event)
            .filter(Event.result_id == result.id, Event.kind == "agent_output")
            .first()
        )
        event.payload = {"answer": '<img src=x onerror="alert(1)">'}
    output = client.get("reports/" + html["id"] + "/download", headers=auth).text
    assert "<img" not in output and "&lt;img" in output
    monkeypatch.setattr(reports, "MAX_REPORTS_PER_GUEST", 0)
    assert create().status_code == 200
    assert (
        client.post(
            "runs/" + second + "/reports", headers=auth, json={"format": "html"}
        ).status_code
        == 503
    )
    with Session(engine) as s, s.begin():
        source = s.get(Run, UUID(second))
        s.delete(source)
    assert client.get(download, headers=auth).status_code == 404
    assert client.get("reports/" + html["id"], headers=auth).status_code == 200
    with Session(engine) as s, s.begin():
        source = s.get(Run, UUID(first))
        guest = s.get(Guest, source.owner_id)
        guest.expires_at = run_queue.now() - timedelta(seconds=1)
    assert client.get("reports/" + html["id"] + "/download", headers=auth).status_code == 401
    from app.api.workspaces import cleanup

    cleanup(engine)
    with Session(engine) as s:
        assert s.get(Report, UUID(html["id"])) is None


def test_cancelled_run_report_keeps_inconclusive_evidence(harness):
    client, workspace, _, _ = harness
    auth, version = workspace()
    run = submit(client, auth, version).json()["id"]
    client.post("runs/" + run + "/cancel", headers=auth)
    report = client.post("runs/" + run + "/reports", headers=auth, json={"format": "json"}).json()
    payload = client.get("reports/" + report["id"] + "/download", headers=auth).json()
    assert payload["run"]["status"] == "cancelled"
    assert payload["metrics"]["coverage"]["numerator"] == 0
    assert payload["metrics"]["pass_rate"]["denominator"] == 0
    assert payload["scenarios"][0]["outcome"] == "inconclusive"
