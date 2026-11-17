"""Exercise the local HTTP API without printing or persisting a guest credential."""

import json
from http.client import HTTPConnection
from time import monotonic, sleep
from uuid import uuid4


def request(method, path, body=None, headers=None):
    connection = HTTPConnection("127.0.0.1", 8012, timeout=8)
    try:
        connection.request(
            method,
            "/api/v1/" + path,
            body=json.dumps(body) if body is not None else None,
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        response = connection.getresponse()
        data = response.read()
        if not 200 <= response.status < 300:
            raise RuntimeError(f"{method} {path} returned {response.status}")
        return json.loads(data) if data else None
    finally:
        connection.close()


def main():
    if request("GET", "health").get("phase") != 4:
        raise RuntimeError("Expected a Phase 4 API on port 8012")
    auth = {"Authorization": "Bearer " + request("POST", "guest-sessions")["credential"]}
    try:
        for profile in ("hardened", "vulnerable"):
            agent = request(
                "POST",
                "agents",
                {
                    "name": "Local smoke",
                    "configuration": {"demo_profile": profile, "allowed_tools": ["search_docs"]},
                },
                auth,
            )
            run = request(
                "POST",
                "runs",
                {"agent_version_id": agent["versions"][0]["id"], "scenarios": ["AS-011"]},
                {**auth, "Idempotency-Key": str(uuid4())},
            )
            path = "runs/" + run["id"]
            deadline = monotonic() + 20
            while run["status"] in ("queued", "running") and monotonic() < deadline:
                sleep(0.15)
                run = request("GET", path, headers=auth)
            trace = request("GET", path + "/traces", headers=auth)
            kinds = [event["kind"] for event in trace]
            if run["status"] != "completed" or kinds != [
                "scenario_start",
                "agent_input",
                "tool_requested",
                "policy_decision",
                "mock_tool_result",
                "agent_output",
                "scenario_end",
            ]:
                raise RuntimeError(f"{profile} smoke failed: {run['status']} {run['reason']}")
            print(f"{profile}: {run['status']}, {len(trace)} persisted events, mock document read")
    finally:
        request("DELETE", "guest-session", headers=auth)


if __name__ == "__main__":
    main()
