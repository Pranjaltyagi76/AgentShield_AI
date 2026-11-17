import os
from datetime import timedelta
from time import monotonic, sleep
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import main, run_queue
from app.api import runs
from app.core.settings import Settings
from app.db.runs import Result, Run
from app.policy import PRIVATE_MARKER, gateway
from app.simulation import decide


def test_production_and_remote_database_reject_execution():
    for env, host in [("production", "localhost"), ("development", "db.example")]:
        with pytest.raises(ValidationError):
            Settings(
                _env_file=None,
                app_env=env,
                local_runs_enabled=True,
                database_url=f"postgresql://user@{host}/test",
            )


def test_inference_is_disabled_and_run_mode_cannot_be_overridden(harness):
    client, workspace, engine, _ = harness
    auth, version = workspace()
    status = client.get("demo/status").json()
    assert status["execution_enabled"] is True
    assert status["inference"]["enabled"] is False
    assert status["requires_api_key"] is False
    response = client.post(
        "runs",
        headers={**auth, "Idempotency-Key": "provider-override"},
        json={"agent_version_id": version, "scenarios": ["AS-011"], "provider": "gemini"},
    )
    assert response.status_code == 422
    with Session(engine) as session:
        assert session.scalar(select(Run).where(Run.request_key == "provider-override")) is None


def test_gateway_authority_and_profile_decisions():
    for tool, args, allowed, expected in [
        ("unknown", {}, ["unknown"], "invalid"),
        ("search_docs", {"query": "guide", "owner": "admin"}, ["search_docs"], "invalid"),
        ("search_docs", {"query": "x" * 17000}, ["search_docs"], "invalid"),
        ("get_customer_record", {"record": "sample"}, [], "blocked"),
        (
            "export_file_simulated",
            {"destination": "mock-inbox"},
            ["export_file_simulated"],
            "requires_confirmation",
        ),
        (
            "send_message_simulated",
            {"destination": "mock-inbox"},
            ["send_message_simulated"],
            "requires_confirmation",
        ),
    ]:
        verdict = gateway({"tool": tool, "arguments": args}, allowed, 0)
        assert (verdict.decision, verdict.result) == (expected, None)
    context = {"available_tools": [], "repeat": False}
    assert "answer" in decide("hardened", context, None, 0)
    assert "tool" in decide("vulnerable", context, None, 0)


@pytest.fixture
def harness(request, monkeypatch):
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("requires migrated local PostgreSQL")
    live = getattr(request, "param", False)
    if not live:
        monkeypatch.setattr(main, "consume", lambda engine, stop, wake: None)
    app = main.create_app(
        Settings(_env_file=None, app_env="test", local_runs_enabled=True, database_url=url)
    )
    headers = []
    with TestClient(
        app, base_url="http://127.0.0.1/api/v1/", client=("127.0.0.1", 52100)
    ) as client:

        def workspace(profile="hardened", prompt="Use the synthetic guide", allowed_tools=None):
            issued = client.post("guest-sessions")
            assert issued.status_code == 201
            h = {"Authorization": "Bearer " + issued.json()["credential"]}
            headers.append(h)
            agent = client.post(
                "agents",
                headers=h,
                json={
                    "name": "Fixture",
                    "configuration": {
                        "allowed_tools": ["search_docs"]
                        if allowed_tools is None
                        else allowed_tools,
                        "demo_profile": profile,
                        "system_prompt": prompt,
                    },
                },
            )
            return h, agent.json()["versions"][0]["id"]

        try:
            yield client, workspace, app.state.database.engine, app.state.settings
        finally:
            for h in headers:
                client.delete("guest-session", headers=h)


def submit(client, h, version, scenarios=("AS-011",), key="one"):
    return client.post(
        "runs",
        headers={**h, "Idempotency-Key": key},
        json={"agent_version_id": version, "scenarios": list(scenarios)},
    )


@pytest.mark.parametrize("harness", [True], indirect=True)
def test_live_consumer_and_ordered_trace(harness):
    c, workspace, _, _ = harness
    for profile in ("hardened", "vulnerable"):
        h, version = workspace(profile)
        response = submit(c, h, version)
        assert response.status_code == 202, response.text
        path = "runs/" + response.json()["id"]
        until = monotonic() + 8
        while monotonic() < until and c.get(path, headers=h).json()["status"] in (
            "queued",
            "running",
        ):
            sleep(0.05)
        assert c.get(path, headers=h).json()["status"] == "completed"
        events = c.get(path + "/traces", headers=h).json()
        assert [e["sequence"] for e in events] == list(range(1, 8))
        assert [e["kind"] for e in events] == [
            "scenario_start",
            "agent_input",
            "tool_requested",
            "policy_decision",
            "mock_tool_result",
            "agent_output",
            "scenario_end",
        ]
        assert events[4]["payload"]["document"] == events[5]["payload"]["answer"]
        assert c.get(path + "/results", headers=h).json()[0]["outcome"] == "pass"
        assert submit(c, h, version).json()["id"] == response.json()["id"]


def test_queue_admission_ownership_and_cancellation(harness, monkeypatch):
    c, workspace, engine, settings = harness
    a, va = workspace()
    b, vb = workspace()
    worker = uuid4()
    first = submit(c, a, va).json()
    path = "runs/" + first["id"]
    assert submit(c, a, va).json()["id"] == first["id"]
    assert submit(c, a, va, ["AS-010"]).status_code == 409
    assert submit(c, a, va, key="another").status_code == 503
    assert submit(c, b, va).status_code == 404
    for route in (path, path + "/traces", path + "/results"):
        assert c.get(route, headers=b).status_code == 404
    assert c.post(path + "/cancel", headers=b).status_code == 404
    monkeypatch.setattr(runs, "MAX_QUEUED", 1)
    assert submit(c, b, vb).status_code == 503
    assert c.get("runs", headers={"Host": "remote.example", **a}).status_code == 404
    with Session(engine) as s, s.begin():
        assert run_queue.claim(s, worker) == UUID(first["id"])
    run_queue.tick(engine, worker)
    assert c.post(path + "/cancel", headers=a).json()["cancel_requested"]
    run_queue.tick(engine, worker)
    assert c.get(path, headers=a).json()["status"] == "cancelled"
    evidence = c.get(path + "/traces", headers=a).json()
    assert evidence[-1]["kind"] == "mock_tool_result"
    run_queue.tick(engine, worker)
    assert c.get(path + "/traces", headers=a).json() == evidence
    second = submit(c, b, vb, key="second").json()
    assert c.post("runs/" + second["id"] + "/cancel", headers=b).json()["status"] == "cancelled"
    settings.max_database_bytes = 1
    assert submit(c, b, vb, key="third").status_code == 503


def test_crash_recovery_preserves_evidence_and_expires_queue(harness):
    c, workspace, engine, _ = harness
    a, va = workspace()
    b, vb = workspace()
    first = submit(c, a, va).json()
    old = uuid4()
    run_queue.tick(engine, old)
    queued = submit(c, b, vb).json()
    with Session(engine) as s, s.begin():
        s.get(Run, UUID(queued["id"])).queue_expires_at = run_queue.now() - timedelta(seconds=1)
    path = "runs/" + first["id"]
    events = c.get(path + "/traces", headers=a).json()
    with Session(engine) as s, s.begin():
        run_queue.recover(s)
    run_queue.tick(engine, uuid4())
    assert c.get(path, headers=a).json()["reason"] == "interrupted"
    assert c.get(path + "/results", headers=a).json()[0]["outcome"] == "inconclusive"
    assert c.get(path + "/traces", headers=a).json() == events and events
    assert c.get("runs/" + queued["id"], headers=b).json()["reason"] == "expired"


@pytest.mark.parametrize(
    ("bound", "reason"),
    [
        ("steps", "step_limit"),
        ("trace", "trace_limit"),
        ("input", "input_budget"),
        ("output", "output_budget"),
        ("total", "input_budget"),
        ("run", "run_timeout"),
        ("scenario", "scenario_timeout"),
    ],
)
def test_budget_stop_retains_inconclusive_result(harness, monkeypatch, bound, reason):
    c, workspace, engine, _ = harness
    h, v = workspace("vulnerable")
    obj = submit(c, h, v, ["AS-010"]).json()
    worker = uuid4()
    run_queue.tick(engine, worker)
    if bound == "steps":
        monkeypatch.setattr(run_queue, "MAX_STEPS", 2)
    if bound in ("trace", "input", "total", "output"):
        monkeypatch.setattr(
            run_queue,
            {
                "trace": "MAX_TRACE",
                "input": "MAX_INPUT",
                "total": "MAX_TOTAL",
                "output": "MAX_OUTPUT",
            }[bound],
            1,
        )
    if bound in ("run", "scenario"):
        with Session(engine) as s, s.begin():
            target = (
                s.get(Run, UUID(obj["id"]))
                if bound == "run"
                else s.query(Result).filter_by(run_id=UUID(obj["id"])).one()
            )
            target.started_at = run_queue.now() - timedelta(seconds=181)
    for _ in range(11):
        run_queue.tick(engine, worker)
    path = "runs/" + obj["id"]
    row = c.get(path, headers=h).json()
    assert (row["status"], row["reason"]) == ("failed", reason)
    assert c.get(path + "/results", headers=h).json()[0]["outcome"] == "inconclusive"


def test_new_app_recovers_orphan_and_resumes_unclaimed_work(harness, monkeypatch):
    client, workspace, engine, settings = harness
    auth, version = workspace()
    partial = submit(client, auth, version).json()["id"]
    run_queue.tick(engine, uuid4())
    pending = submit(client, auth, version, ["AS-011", "AS-010"], key="next").json()["id"]
    evidence = client.get("runs/" + partial + "/traces", headers=auth).json()
    monkeypatch.setattr(main, "consume", run_queue.consume)
    with TestClient(
        main.create_app(settings), base_url="http://localhost/api/v1/", client=("127.0.0.1", 52101)
    ) as restarted:
        deadline = monotonic() + 8
        while monotonic() < deadline:
            row = restarted.get("runs/" + pending, headers=auth).json()
            if row["status"] == "completed":
                break
            sleep(0.05)
        assert row["status"] == "completed"
        assert restarted.get("runs/" + partial, headers=auth).json()["reason"] == "interrupted"
        assert restarted.get("runs/" + partial + "/traces", headers=auth).json() == evidence
        rows = restarted.get("runs/" + pending + "/results", headers=auth).json()
        assert [r["scenario_id"] for r in rows] == ["AS-011", "AS-010"]
        assert all(r["status"] == "completed" for r in rows)


def test_agent_cannot_expand_gateway_permissions(harness, monkeypatch):
    client, workspace, engine, _ = harness
    auth, version = workspace()

    def request_record(profile, context, observation, step):
        context["available_tools"].append("get_customer_record")
        return {"tool": "get_customer_record", "arguments": {"record": "sample"}}

    monkeypatch.setattr(run_queue, "decide", request_record)
    run = submit(client, auth, version).json()
    run_queue.tick(engine, uuid4())
    events = client.get("runs/" + run["id"] + "/traces", headers=auth).json()
    assert events[-1]["payload"] == {"decision": "blocked", "reason": "tool_not_allowed"}
    assert "mock_tool_result" not in [event["kind"] for event in events]
    assert events[1]["payload"]["available_tools"] == ["search_docs"]


def test_active_caps_and_rate_limits(harness):
    c, workspace, engine, _ = harness
    a, va = workspace()
    b, vb = workspace()
    d, vd = workspace()
    worker = uuid4()
    first = submit(c, a, va).json()["id"]
    with Session(engine) as s, s.begin():
        assert run_queue.claim(s, worker) == UUID(first)
    assert submit(c, a, va, key="next").status_code == 202
    second = submit(c, b, vb).json()["id"]
    with Session(engine) as s, s.begin():
        assert run_queue.claim(s, worker) == UUID(second)
    assert submit(c, d, vd).status_code == 202
    with Session(engine) as s, s.begin():
        assert run_queue.claim(s, worker) is None
    assert submit(c, d, vd, key="retry1").status_code == 503
    limited = submit(c, d, vd, key="retry2")
    assert limited.status_code == 429 and limited.headers["Retry-After"] == "600"
    limiter = runs.RunLimiter()
    for i in range(5):
        limiter.admit("same", str(i))
    with pytest.raises(HTTPException):
        limiter.admit("same", "new-peer")
    for i in range(45):
        limiter.admit(str(i), "peer" + str(i))
    with pytest.raises(HTTPException):
        limiter.admit("new-owner", "new-peer")


@pytest.mark.parametrize(
    "case,reason", [("repeat", "tool_call_limit"), ("oversize", "arguments_too_large")]
)
def test_runtime_retains_denied_attempt(harness, monkeypatch, case, reason):
    client, workspace, engine, _ = harness
    auth, version = workspace("vulnerable")
    if case == "oversize":
        monkeypatch.setattr(
            run_queue,
            "decide",
            lambda *args: {"tool": "search_docs", "arguments": {"query": "x" * 17000}},
        )
    run = submit(client, auth, version, ["AS-010"]).json()
    worker = uuid4()
    for _ in range(8):
        run_queue.tick(engine, worker)
    path = "runs/" + run["id"]
    assert client.get(path, headers=auth).json()["status"] == (
        "completed" if case == "repeat" else "failed"
    )
    trace = client.get(path + "/traces", headers=auth).json()
    if case == "repeat":
        assert trace.pop()["kind"] == "scenario_end"
    assert trace[-2]["kind"] == "tool_requested"
    assert trace[-1]["kind"] == "policy_decision"
    assert trace[-1]["payload"]["reason"] == reason
    assert sum(event["kind"] == "mock_tool_result" for event in trace) == (
        6 if case == "repeat" else 0
    )
    assert client.get(path + "/results", headers=auth).json()[0]["outcome"] == (
        "pass" if case == "repeat" else "inconclusive"
    )


def test_secret_in_a_delivery_request_never_reaches_guest_trace(harness, monkeypatch):
    client, workspace, engine, _ = harness
    auth, version = workspace(allowed_tools=["send_message_simulated"])
    monkeypatch.setattr(
        run_queue,
        "decide",
        lambda *args: {
            "tool": "send_message_simulated",
            "arguments": {"content": PRIVATE_MARKER, "destination": "mock-inbox"},
        },
    )
    row = submit(client, auth, version, ["AS-006"]).json()
    run_queue.tick(engine, uuid4())
    trace = client.get("runs/" + row["id"] + "/traces", headers=auth)
    assert trace.json()[-1]["payload"] == {"decision": "blocked", "reason": "synthetic_secret"}
    assert PRIVATE_MARKER not in trace.text
    assert "mock_tool_result" not in [e["kind"] for e in trace.json()]


def test_full_suite_repeatability_and_owned_evidence(harness):
    client, workspace, engine, _ = harness
    auth, _ = workspace()
    other, _ = workspace()
    suite = client.get("scenario-suites").json()[1]
    assert suite["id"] == "core-v2" and len(suite["members"]) == 12
    for agent in client.get("agents").json():
        detail = client.get("agents/" + agent["id"]).json()
        version = detail["versions"][0]
        summaries = []
        for _ in range(2):
            run = client.post(
                "runs",
                headers={**auth, "Idempotency-Key": str(uuid4())},
                json={"agent_version_id": version["id"], "suite_id": "core-v2"},
            )
            assert run.status_code == 202, run.text
            path = "runs/" + run.json()["id"]
            worker = uuid4()
            for _ in range(45):
                if not run_queue.tick(engine, worker):
                    break
            results = client.get(path + "/results", headers=auth).json()
            assert [(r["scenario_id"], r["version"]) for r in results] == [
                (m["scenario_id"], m["version"]) for m in suite["members"]
            ]
            report = client.get(path + "/metrics", headers=auth).json()
            assert report["status"] == "completed" and report["coverage"]["numerator"] == 12
            assert report["pass_rate"]["numerator"] == (
                12 if version["demo_profile"] == "hardened" else 6
            )
            assert report["attack_success"]["denominator"] == 11
            assert report["unauthorized_execution"]["numerator"] == 0
            assert results[9]["outcome"] == "pass" and results[10]["outcome"] == "pass"
            findings = client.get(path + "/findings", headers=auth).json()
            events = []
            for offset in (0, 100):
                page = client.get(
                    path + "/traces", headers=auth, params={"limit": 100, "offset": offset}
                )
                assert PRIVATE_MARKER not in page.text
                events.extend(page.json())
            filtered = client.get(
                path + "/traces", headers=auth, params={"scenario_id": "AS-003"}
            ).json()
            assert filtered == [e for e in events if e["scenario_id"] == "AS-003"]
            assert client.get(path + "/traces?scenario_id=AS-003", headers=other).status_code == 404
            by_id = {e["id"]: e for e in events}
            assert all(by_id[f["evidence_id"]]["scenario_id"] == f["scenario_id"] for f in findings)
            assert all(
                "evaluator_rule" not in e["payload"] and "outcome" not in e["payload"]
                for e in events
                if e["kind"] == "agent_input"
            )
            assert all(
                client.get(path + suffix, headers=other).status_code == 404
                for suffix in ("/metrics", "/findings")
            )
            summaries.append(
                (
                    report,
                    [(e["scenario_id"], e["sequence"], e["kind"], e["payload"]) for e in events],
                )
            )
        assert summaries[0] == summaries[1]


def test_comparisons_owned_idempotent_and_retention(harness, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    from app.api import benchmarks
    from app.db.runs import Comparison

    client, workspace, engine, _ = harness
    owner, _ = workspace()
    other, _ = workspace()
    agents = client.get("agents").json()
    versions = {
        a["name"].split()[0].lower(): client.get("agents/" + a["id"]).json()["versions"][0]["id"]
        for a in agents
    }
    first = submit(client, owner, versions["vulnerable"], scenarios=["AS-001", "AS-011"]).json()[
        "id"
    ]
    worker = uuid4()
    for _ in range(5):
        run_queue.tick(engine, worker)
    second = submit(
        client, owner, versions["hardened"], scenarios=["AS-001", "AS-011"], key="two"
    ).json()["id"]
    foreign = submit(client, other, versions["hardened"]).json()["id"]

    def compare(auth, a, b):
        return client.post(
            "benchmarks/compare", headers=auth, json={"baseline_run_id": a, "candidate_run_id": b}
        )

    assert compare(owner, first, second).status_code == 409
    assert compare(owner, first, first).status_code == 422
    assert compare(owner, foreign, second).status_code == 404
    assert compare(owner, first, foreign).status_code == 404
    for _ in range(8):
        run_queue.tick(engine, worker)
    with ThreadPoolExecutor(max_workers=2) as pool:
        requests = [pool.submit(compare, owner, first, second) for _ in range(2)]
        responses = [request.result(timeout=10) for request in requests]
    assert sorted(response.status_code for response in responses) == [200, 201]
    report = responses[0].json()
    assert responses[1].json() == report
    assert report["counts"]["improved"] == 1 and report["counts"]["unchanged"] == 1
    assert report["metrics"]["pass_rate"]["delta_pp"] == 50
    path = "benchmarks/" + report["id"]
    assert client.get(path, headers=owner).json() == report
    assert client.get(path, headers=other).status_code == 404
    assert client.get(path).status_code == 401
    reverse = compare(owner, second, first).json()
    assert reverse["counts"]["regressed"] == 1
    monkeypatch.setattr(benchmarks, "MAX_COMPARISONS_PER_GUEST", 0)
    retry = compare(owner, first, second)
    assert retry.status_code == 200 and retry.json() == report
    third = submit(client, owner, versions["hardened"], key="three").json()["id"]
    client.post("runs/" + third + "/cancel", headers=owner)
    assert compare(owner, first, third).status_code == 503
    client.delete("guest-session", headers=owner)
    with Session(engine) as session:
        assert session.get(Comparison, UUID(report["id"])) is None
        assert session.get(Comparison, UUID(reverse["id"])) is None
