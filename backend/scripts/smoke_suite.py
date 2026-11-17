"""Run the two shared Core v2 profiles through the loopback API and revoke the guest."""

from time import monotonic, sleep
from uuid import uuid4

from smoke_local_runs import request


def main():
    if request("GET", "health")["phase"] != 4:
        raise RuntimeError("Expected a Phase 4 API on loopback port 8012")
    auth = {"Authorization": "Bearer " + request("POST", "guest-sessions")["credential"]}
    try:
        profiles = request("GET", "agents")
        for agent in profiles:
            version = request("GET", "agents/" + agent["id"])["versions"][0]
            run = request(
                "POST",
                "runs",
                {"agent_version_id": version["id"], "suite_id": "core-v2"},
                {**auth, "Idempotency-Key": str(uuid4())},
            )
            path = "runs/" + run["id"]
            until = monotonic() + 60
            while run["status"] in ("queued", "running") and monotonic() < until:
                sleep(0.2)
                run = request("GET", path, headers=auth)
            metrics = request("GET", path + "/metrics", headers=auth)
            if run["status"] != "completed" or metrics["coverage"]["numerator"] != 12:
                raise RuntimeError("Expected twelve evaluable results")
            findings = request("GET", path + "/findings", headers=auth)
            print(
                version["demo_profile"],
                "findings",
                len(findings),
                "trace bytes",
                run["trace_bytes"],
            )
            for key in (
                "coverage",
                "pass_rate",
                "attack_success",
                "secret_exposure",
                "benign_completion",
                "unauthorized_execution",
            ):
                metric = metrics[key]
                print(f"  {key} {metric['numerator']}/{metric['denominator']}")
    finally:
        request("DELETE", "guest-session", headers=auth)


if __name__ == "__main__":
    main()
