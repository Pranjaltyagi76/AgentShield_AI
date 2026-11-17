"""Release checks for the fixed public deployment. Credentials stay in memory."""

import argparse
import json
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

API = "https://agentshield-api-hn0q.onrender.com/api/v1"
ORIGIN = "https://agentshield-ai-tau.vercel.app"


class UnexpectedStatus(RuntimeError):
    def __init__(self, method, path, status, retry_after):
        super().__init__(f"{method} {path} returned {status}")
        self.status = status
        self.retry_after = retry_after


def request(method, path, auth=None, data=None, expected=200, extra=None, raw=False):
    headers = {"Accept": "application/json", **(auth or {}), **(extra or {})}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = Request(
        API + path,
        method=method,
        headers=headers,
        data=json.dumps(data).encode() if data is not None else None,
    )
    try:
        response = urlopen(req, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        body = response.read()
        if response.status != expected:
            raise UnexpectedStatus(
                method, path, response.status, response.headers.get("Retry-After")
            )
        value = body if raw else (json.loads(body) if body else None)
        return value, response.headers


def wait_run(run_id, auth):
    deadline = monotonic() + 60
    while monotonic() < deadline:
        run, _ = request("GET", "/runs/" + run_id, auth)
        if run["status"] not in ("queued", "running"):
            return run
        sleep(0.3)
    raise RuntimeError("Hosted run did not finish within the verification deadline")


def submit(version, auth, key):
    return request(
        "POST",
        "/runs",
        auth,
        {
            "agent_version_id": version,
            "scenarios": ["AS-011"],
        },
        expected=202,
        extra={"Idempotency-Key": key},
    )[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recovery-check",
        action="store_true",
        help="Pause for the documented owned orphan fixture and service redeploy",
    )
    args = parser.parse_args()
    health, _ = request("GET", "/health")
    if health.get("run_mode") != "public":
        raise RuntimeError("Public execution has not been activated")
    assert health["service"] == "agentshield-api" and health["phase"] >= 8
    assert request("GET", "/ready")[0]["status"] == "ready"
    availability, _ = request("GET", "/demo/status")
    assert availability["requires_api_key"] is False
    assert availability["inference"]["enabled"] is False
    _, allowed = request("GET", "/health", extra={"Origin": ORIGIN})
    _, denied = request("GET", "/health", extra={"Origin": "https://untrusted.example"})
    assert allowed.get("Access-Control-Allow-Origin") == ORIGIN
    assert denied.get("Access-Control-Allow-Origin") is None
    owners = []
    try:
        agents = []
        for name in ("Phase 9 release verification", "Phase 9 expiry verification"):
            session, _ = request("POST", "/guest-sessions", expected=201)
            auth = {"Authorization": "Bearer " + session["credential"]}
            owners.append(auth)
            agent, _ = request(
                "POST",
                "/agents",
                auth,
                {
                    "name": name,
                    "configuration": {"allowed_tools": ["search_docs"], "demo_profile": "hardened"},
                },
                expected=201,
            )
            agents.append(agent)
        first, second = owners
        version = agents[0]["versions"][0]["id"]
        request("GET", "/agents/" + agents[0]["id"], second, expected=404)
        shared, _ = request("GET", "/agents")
        request("PATCH", "/agents/" + shared[0]["id"], first, {"name": "blocked"}, expected=403)
        request(
            "POST",
            "/runs",
            first,
            {"agent_version_id": version, "scenarios": ["AS-011"]},
            expected=403,
            extra={"Origin": "https://untrusted.example", "Idempotency-Key": str(uuid4())},
        )
        key = str(uuid4())
        baseline = submit(version, first, key)
        assert submit(version, first, key)["id"] == baseline["id"]
        run_id = baseline["id"]
        assert wait_run(run_id, first)["status"] == "completed"
        for suffix in ("", "/metrics", "/findings", "/traces"):
            request("GET", "/runs/" + run_id + suffix, second, expected=404)
        request(
            "POST",
            "/runs",
            second,
            {
                "agent_version_id": version,
                "scenarios": ["AS-011"],
            },
            expected=404,
            extra={"Idempotency-Key": str(uuid4())},
        )
        report, _ = request(
            "POST", "/runs/" + run_id + "/reports", first, {"format": "json"}, expected=201
        )
        path = "/reports/" + report["id"] + "/download"
        original, _ = request("GET", path, first, raw=True)
        assert b"AS-SYNTHETIC-PRIVATE-001" not in original
        assert first["Authorization"].split()[1].encode() not in original
        request("GET", path, second, expected=404)
        cancelled = submit(version, first, str(uuid4()))
        request("POST", "/runs/" + cancelled["id"] + "/cancel", first)
        assert wait_run(cancelled["id"], first)["status"] == "cancelled"
        values, _ = request("GET", "/runs/" + cancelled["id"] + "/metrics", first)
        assert values["coverage"]["numerator"] == 0
        comparison, _ = request(
            "POST",
            "/benchmarks/compare",
            first,
            {
                "baseline_run_id": run_id,
                "candidate_run_id": cancelled["id"],
            },
            expected=201,
        )
        assert comparison["counts"]["inconclusive"] == 1
        request("GET", "/benchmarks/" + comparison["id"], second, expected=404)
        request(
            "POST",
            "/benchmarks/compare",
            second,
            {
                "baseline_run_id": run_id,
                "candidate_run_id": cancelled["id"],
            },
            expected=404,
        )
        print(
            json.dumps(
                {
                    "verified": [
                        "HTTPS readiness",
                        "CORS",
                        "guest isolation",
                        "shared immutability",
                        "idempotency",
                        "cancellation",
                        "inconclusive comparison",
                        "report ownership",
                    ],
                    "baseline_run": run_id,
                    "expiry_agent": agents[1]["id"],
                }
            ),
            flush=True,
        )
        if args.recovery_check:
            recovery = str(uuid4())
            print(json.dumps({"stage_recovery_run": recovery}), flush=True)
            input(
                "Stage the documented owned orphan/expiry fixture and redeploy, then press Enter. "
            )
            assert request("GET", path, first, raw=True)[0] == original
            recovered = wait_run(recovery, first)
            assert recovered["status"] == "failed" and recovered["reason"] == "interrupted"
            events, _ = request("GET", "/runs/" + recovery + "/traces", first)
            assert len(events) == 1 and events[0]["kind"] == "scenario_start"
            assert (
                request("GET", "/runs/" + recovery + "/metrics", first)[0]["coverage"]["numerator"]
                == 0
            )
            request("GET", "/guest-session", second, expected=401)
            print(
                "Verified restart regeneration, hosted orphan recovery and expired-session denial.",
                flush=True,
            )
        rejected = False
        for _ in range(6):
            try:
                run = submit(version, first, str(uuid4()))
            except UnexpectedStatus as error:
                if error.status != 429:
                    raise
                assert error.retry_after and int(error.retry_after) > 0
                rejected = True
                break
            request("POST", "/runs/" + run["id"] + "/cancel", first)
            wait_run(run["id"], first)
        assert rejected, "Quota rejection was not observed"
        print(
            "Verified HTTP 429 with Retry-After. Guest verification records will be revoked.",
            flush=True,
        )
    finally:
        for owner in owners:
            try:
                request("DELETE", "/guest-session", owner, expected=204)
            except UnexpectedStatus as error:
                if error.status != 401:
                    raise


if __name__ == "__main__":
    main()
