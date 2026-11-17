"""Capture a redacted historical workspace from new loopback-only scripted runs."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4

from app.reporting import render_html, render_json
from app.suite import PRIVATE_MARKER
from scripts.smoke_local_runs import request

ROOT = Path(__file__).resolve().parents[2]


def main():
    if request("GET", "health").get("run_mode") != "local":
        raise RuntimeError("Capture requires an explicitly enabled loopback API on port 8012")
    if request("GET", "ready")["status"] != "ready":
        raise RuntimeError("Local database is not ready")
    auth = {"Authorization": "Bearer " + request("POST", "guest-sessions")["credential"]}
    try:
        runs = {}
        for agent in request("GET", "agents"):
            if not agent["is_shared"]:
                continue
            version = request("GET", "agents/" + agent["id"])["versions"][0]
            profile = version["demo_profile"]
            run = request(
                "POST",
                "runs",
                {"agent_version_id": version["id"], "suite_id": "core-v2"},
                {**auth, "Idempotency-Key": str(uuid4())},
            )
            deadline = monotonic() + 60
            while run["status"] in ("queued", "running") and monotonic() < deadline:
                sleep(0.2)
                run = request("GET", "runs/" + run["id"], headers=auth)
            if run["status"] != "completed":
                raise RuntimeError("Sample capture did not complete")
            runs[profile] = run
        comparison = request(
            "POST",
            "benchmarks/compare",
            {
                "baseline_run_id": runs["vulnerable"]["id"],
                "candidate_run_id": runs["hardened"]["id"],
            },
            auth,
        )
        metadata = request(
            "POST",
            "runs/" + runs["vulnerable"]["id"] + "/reports",
            {
                "format": "json",
                "comparison_id": comparison["id"],
            },
            auth,
        )
        report = request("GET", "reports/" + metadata["id"] + "/download", headers=auth)
        # Publish only this newly generated synthetic workspace, with all UUIDs replaced.
        ids = {}

        def public_id(match):
            value = match.group()
            return ids.setdefault(value, f"sample-{len(ids) + 1:04d}")

        report = json.loads(
            re.sub(
                r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}",
                public_id,
                render_json(report),
            )
        )
        report["sample"] = {
            "label": "Saved sample - not a live run",
            "captured_at": datetime.now(UTC).isoformat(),
            "method": (
                "Captured from two completed Core v2 scripted runs "
                "through local HTTP and PostgreSQL. "
                "IDs are replaced and synthetic private values are redacted."
            ),
        }
        body = render_json(report)
        if PRIVATE_MARKER in body or auth["Authorization"].split()[1] in body:
            raise RuntimeError("Sample failed redaction verification")
        public = ROOT / "frontend" / "public"
        public.mkdir(exist_ok=True)
        (public / "saved-sample.json").write_text(body + "\n", encoding="utf-8")
        (public / "saved-sample.html").write_text(render_html(report), encoding="utf-8")
        print(
            "Captured sample:",
            report["metrics"]["pass_rate"],
            "comparison:",
            report["comparison"]["counts"],
        )
    finally:
        request("DELETE", "guest-session", headers=auth)


if __name__ == "__main__":
    main()
