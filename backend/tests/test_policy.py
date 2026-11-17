import os
from time import monotonic, sleep
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app
from app.policy import MAX_CALLS, PRIVATE_MARKER, SCHEMAS, gateway, request_evidence

MESSAGE = {
    "tool": "send_message_simulated",
    "arguments": {"destination": "mock-inbox", "content": "Workspace hours reviewed."},
}


@pytest.mark.parametrize(
    "tool,args,reason",
    [
        ("get_customer_record", {"record": "protected"}, "protected_record"),
        ("get_customer_record", {"record": "other-customer"}, "record_owner_mismatch"),
        ("get_customer_record", {"record": "missing"}, "invalid_arguments"),
        ("send_message_simulated", {"destination": "mock-outbox"}, "destination_not_allowed"),
        (
            "export_file_simulated",
            {"destination": "mock-inbox", "record": "protected"},
            "protected_record",
        ),
        (
            "export_file_simulated",
            {"destination": "mock-inbox", "record": "other-customer"},
            "record_owner_mismatch",
        ),
        (
            "export_file_simulated",
            {"destination": "mock-inbox", "content": "x" + PRIVATE_MARKER},
            "synthetic_secret",
        ),
        (
            "send_message_simulated",
            {"destination": "mock-inbox", "content": PRIVATE_MARKER},
            "synthetic_secret",
        ),
        (
            "send_message_simulated",
            {"destination": "mock-inbox", "confirmed": True},
            "invalid_arguments",
        ),
        ("search_docs", {"query": ["guide"]}, "invalid_arguments"),
        (
            "export_file_simulated",
            {"destination": "mock-inbox", "content": "é" * 8200},
            "arguments_too_large",
        ),
    ],
)
def test_denials_override_even_an_exact_approval(tool, args, reason):
    proposal = {"tool": tool, "arguments": args}
    verdict = gateway(proposal, SCHEMAS, 0, proposal)
    assert verdict.reason == reason
    assert verdict.result is None
    assert PRIVATE_MARKER not in str(request_evidence(proposal))


def test_approval_and_attempt_boundaries():
    assert gateway(MESSAGE, SCHEMAS, 0).decision == "requires_confirmation"
    assert gateway(MESSAGE, [], 0, MESSAGE).reason == "tool_not_allowed"
    assert gateway(MESSAGE, SCHEMAS, MAX_CALLS, MESSAGE).reason == "tool_call_limit"
    assert gateway(MESSAGE, SCHEMAS, MAX_CALLS - 1, MESSAGE).result["receipt"] == "simulated"
    different = {"tool": "export_file_simulated", "arguments": MESSAGE["arguments"]}
    assert gateway(different, SCHEMAS, 0, MESSAGE).decision == "requires_confirmation"
    assert gateway({**MESSAGE, "confirmed": True}, SCHEMAS, 0).reason == "invalid_proposal"
    assert gateway({"tool": [], "arguments": {}}, SCHEMAS, 0).reason == "unknown_tool"
    assert (
        gateway(
            {"tool": "get_customer_record", "arguments": {"record": "sample"}}, SCHEMAS, 0
        ).result["record"]
        == "sample"
    )


def test_public_scripted_mode_with_isolated_guests():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("requires migrated PostgreSQL")
    origin = "https://frontend.example"
    settings = Settings(
        _env_file=None,
        app_env="production",
        public_runs_enabled=True,
        database_url=url,
        cors_origins=[origin],
    )
    with TestClient(
        create_app(settings), base_url="https://api.example/api/v1/", client=("192.0.2.2", 1234)
    ) as client:

        def issue():
            response = client.post("guest-sessions")
            assert response.status_code == 201
            return {"Authorization": "Bearer " + response.json()["credential"]}

        owner, stranger = issue(), issue()
        try:
            assert client.get("runs").status_code == 401
            assert (
                client.get(
                    "runs", headers={**owner, "Origin": "https://unknown.example"}
                ).status_code
                == 403
            )
            for profile, confirm, reason in [
                ("hardened", False, "confirmation_missing"),
                ("vulnerable", True, "destination_not_allowed"),
                ("hardened", True, "owner_confirmed"),
            ]:
                version = client.post(
                    "agents",
                    headers=owner,
                    json={
                        "name": profile,
                        "configuration": {
                            "demo_profile": profile,
                            "allowed_tools": ["send_message_simulated"],
                        },
                    },
                ).json()["versions"][0]["id"]
                data = {"agent_version_id": version, "scenarios": ["AS-006"]}
                if confirm:
                    data["confirmation"] = {"scenario": "AS-006", "step": 1, **MESSAGE}
                headers = {"Idempotency-Key": str(uuid4()), "Origin": origin}
                assert (
                    client.post("runs", headers={**headers, **stranger}, json=data).status_code
                    == 404
                )
                response = client.post("runs", headers={**headers, **owner}, json=data)
                assert response.status_code == 202
                path = "runs/" + response.json()["id"]
                until = monotonic() + 10
                while monotonic() < until:
                    row = client.get(path, headers=owner).json()
                    if row["status"] == "completed":
                        break
                    sleep(0.05)
                assert row["status"] == "completed"
                trace = client.get(path + "/traces", headers=owner).json()
                assert trace[0]["payload"]["version"] == 2
                assert "confirmation" not in trace[1]["payload"]
                assert trace[2]["kind"] == "tool_requested"
                assert trace[3]["payload"]["reason"] == reason
                receipts = [e["payload"] for e in trace if e["kind"] == "mock_tool_result"]
                assert receipts == (
                    [{"receipt": "simulated", "destination": "mock-inbox"}]
                    if reason == "owner_confirmed"
                    else []
                )
                assert client.get(path + "/traces", headers=stranger).status_code == 404
                assert client.post(path + "/cancel", headers=stranger).status_code == 404
                assert (
                    client.post("runs", headers={**headers, **owner}, json=data).json()["id"]
                    == row["id"]
                )
        finally:
            for auth in (owner, stranger):
                client.delete("guest-session", headers=auth)
