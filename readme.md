# AgentShield AI

AI agent security testing, controlled attack simulation, and reliability benchmarking.

**Phase 10 portfolio materials are ready for the deployed scripted release.** Use the app without an AI API key, inspect a real historical report, and follow a finding to its recorded event.

[Live demo](https://agentshield-ai-tau.vercel.app/runs) · [Saved sample](https://agentshield-ai-tau.vercel.app/sample) · [Two-minute captioned video](docs/portfolio/walkthrough.mp4) · [Walkthrough and transcript](docs/portfolio/walkthrough.md)

## What is implemented

- Twelve pinned synthetic Core v2 scenarios and two versioned deterministic profiles.
- Guest-owned custom scenarios with registered label/guide checks, validation, immutable versions and pinned execution.
- A Settings page for the tab's default demo profile, provider status, server limits and retention.
- Independent mock-tool gateway, ordered traces, evidence-linked findings and coverage-aware evaluation.
- Guest-owned profiles/runs, immutable versions, bounded PostgreSQL queue, cancellation and interruption recovery.
- Compatible-run comparisons with explicit counts, exclusions and percentage-point deltas.
- Authenticated HTML/JSON exports from retained PostgreSQL records; redacted historical sample independent of API health.
- React/Vite/TypeScript frontend, FastAPI backend and PostgreSQL, deployed on existing ongoing free plans.

The scripts exercise the real harness. They do not establish real-model resistance to prompt injection. Custom declarative authoring and a dedicated Settings page are implemented and publicly verified. Gemini is explicitly disabled and its live adapter is unimplemented.

## Reviewer starting points

| Inspect | Evidence |
|---|---|
| Runtime and decisions | [Architecture diagram and actual module map](context/architecture.md), [system design](context/system%20design.md) |
| Security boundaries | [Threat model, controls and residual risks](docs/threat-model.md) |
| Scoring and reproducibility | [Methodology and denominators](context/benchmark.md), [sample JSON](frontend/public/saved-sample.json), [sample HTML](frontend/public/saved-sample.html) |
| Actual observations | [Dated performance/quality review](context/performance_review.md), [deployment evidence](context/deployment.md) |
| Portfolio discussion | [Video, transcript and capture provenance](docs/portfolio/walkthrough.md), [resume/interview notes](docs/portfolio/interview-notes.md) |
| Remaining acceptance gaps | [Requirement review](requirement.md#original-requirement-acceptance-review--november-18-2026) |

On November 18, fresh hosted Core v2 runs evaluated 12/12 cases each. Hardened passed 12/12 and vulnerable passed 6/12; their comparison showed six improvements and six unchanged cases. These are scripted observations. The bundled sample retains its separate November 17 capture date. Historical quality evidence on November 17 includes 98 backend tests, 25 frontend tests and all three CI jobs passing; Phase 10 verification is recorded separately in the review log.

![Actual hosted comparison from the walkthrough](docs/portfolio/captures/12.jpg)

## Try the hosted app

Open [AgentShield AI](https://agentshield-ai-tau.vercel.app/runs), start a guest workspace and launch the default hardened Core v2 suite. Select the vulnerable shared profile for a second run, then compare both results and download reports. No model key is required.

[Saved sample](https://agentshield-ai-tau.vercel.app/sample) is bundled with the frontend and remains available during API outages. Guest workspaces expire after seven days and access depends on the current tab’s credential. Free hosting can sleep, restart or reach its quotas.

## Prerequisites

Use Python 3.12, uv 0.12.23, Node.js 24, and npm. Python dependencies are locked in `backend/uv.lock`; frontend dependencies are locked in `frontend/package-lock.json`. Docker with Compose is needed for the provided local database setup. The API can start without a database, but readiness then returns 503.

No model key, paid hosting, or purchased domain is required. The temporary portable PostgreSQL used for local verification is not an application dependency or a committed server installation.

## Local setup

From the repository root, copy the local configuration:

```powershell
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env.local
```

The example database password is intentionally local-only. Never reuse it in a public/shared environment. Real environment files are ignored by Git.

Start the loopback-only local database:

```powershell
docker compose up -d --wait
```

In a backend terminal:

```powershell
uv sync --project backend --locked
uv --directory backend run alembic upgrade head
uv --directory backend run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

In a separate frontend terminal:

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open [the local workspace](http://127.0.0.1:5173). The frontend proxies `/api` to port 8000; `VITE_API_BASE_URL` includes `/api/v1` exactly once. Development API docs are at [localhost:8000/docs](http://127.0.0.1:8000/docs). Production disables the interactive docs.

`GET /api/v1/health` reports process health independently of PostgreSQL. `GET /api/v1/ready` reports `connected`, `unavailable`, or `not_configured`, with HTTP 503 when not ready. The current API requires Alembic revision `0008`. Runtime connections stay pooled; migrations derive the direct Neon hostname from the existing URL without exposing credentials.

Stop the database with `docker compose down`. This preserves the named data volume. Removing the volume deletes local database data, so do not do that as an ordinary shutdown step.

## Launch a benchmark in the browser

Start loopback PostgreSQL as described above. In a backend terminal, migrate the database, enable local runs and start the API on the port used by the Vite proxy.

```powershell
uv --directory backend run alembic upgrade head
$env:LOCAL_RUNS_ENABLED = "true"
uv --directory backend run uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers --no-access-log
```

Run `npm --prefix frontend run dev` in another terminal and open [Benchmark runs](http://127.0.0.1:5173/runs). Start a guest workspace, select an agent version and launch Core v2 or selected scenarios. Open a finding’s evidence link to inspect its highlighted event. Expand a tool request to see its arguments, policy decision and recorded mock result. The same tab can reopen a run from history. Guest access expires after seven days or revocation.

## Export reports and explore the saved workspace

Open a finished run and select **Download HTML report** or **Download JSON report**. Failed and cancelled runs retain their status and inconclusive results in the export. From a saved comparison, the same controls include that comparison with the candidate run. Open [Report history](http://127.0.0.1:5173/reports) to download retained reports again.

Reports contain versioned configuration, scenario revisions, metric counts and rates, severity counts, failed cases, findings, linked redacted evidence, policy decisions, optional comparison and limitations. Metadata is stored in PostgreSQL and exports regenerate on demand. Guest expiry or deletion of a source ends access. The API uses authenticated headers for downloads.

The seeded shared vulnerable and hardened profiles are ready in every migrated database. The launcher defaults to the hardened profile and Core v2. [Saved sample](http://127.0.0.1:5173/sample) opens a captured vulnerable run and hardened comparison without a guest or API connection. Its HTML and JSON downloads are bundled with the frontend. All sample IDs have been replaced and synthetic private values redacted.

The availability banner offers manual retry and sample access during a backend wake or outage. A not-ready database receives at most two additional foreground checks, three seconds apart. A network error stops scheduled checks after the configured request retry.

![Captured report history](docs/screenshots/report-history.png)

![Saved sample during an API outage](docs/screenshots/saved-sample.png)

To refresh the public sample from newly executed local suites, start the opt-in loopback API on port 8012, then run the capture command from the backend directory. It creates a temporary guest and revokes it after capturing the synthetic results.

```powershell
.venv/Scripts/python -m scripts.capture_sample
```

Review the new sample, then format the public HTML and JSON with the frontend’s Prettier command before committing. Capture timestamps describe the observed historical run.

## Author custom scenarios and set demo preferences

Open **Scenarios**, start a guest workspace and use **Custom scenarios**. Choose the registered label-conflict or guide-completion checker, supply synthetic fields, validate the draft, then save. Editing validated content requires validation again. Open a saved version to create a new immutable revision. Eight scenarios and four versions each are retained per guest under the normal expiry and storage limits.

In **Benchmark runs**, choose **Choose curated or custom scenarios**. Select up to twelve cases, including the exact saved custom revision. Curated and custom cases can share a run. Both the agent and the scenario must allow a guide lookup. Outcomes follow recorded evidence; custom rubric snapshots never enter agent context or exports. Different custom revisions/hashes are incompatible for outcome deltas.

Open **Settings** and save Hardened or Vulnerable as the tab's default. The launcher selects that shared profile on the next visit. The page also shows current provider status, server limits and workspace expiry. Free-form task text is recorded as data; deterministic scripts use the registered fields rather than interpreting arbitrary instructions.

## Optional Gemini status

Phase 7 uses the specification’s disabled-inference exit branch. This workspace has no configured Gemini credential and account-specific free access has not been verified. The runtime uses scripted profiles. `GET /api/v1/demo/status` reports whether scripted execution is enabled by configuration and why Gemini is disabled. Database readiness remains available at `/ready`.

`PUBLIC_LLM_ENABLED=false` and `LLM_PROVIDER=demo` are enforced. Setting a key alone cannot enable inference. A future Gemini implementation requires a verified ongoing free project, a fixed eligible model and endpoint, bounded token/call/time quotas, strict action parsing and error handling through the existing gateway. Live inference and its provider error paths have not been tested.

## Compare two runs

In the same guest workspace, run Core v2 once with the vulnerable profile and once with the hardened profile. Open [Compare benchmarks](http://127.0.0.1:5173/compare), choose vulnerable as the baseline and hardened as the candidate, then select **Compare runs**. Open a scenario outcome to inspect the corresponding source trace. The comparison link can be reopened while the guest has access to both retained runs.

Each rate shows its numerator, denominator and change in percentage points. Full-run coverage includes every selected case. Outcome rates use only compatible cases with evidence on both sides. Switching the baseline and candidate reverses the direction of change.

## Try a local scripted run from the command line

With the local PostgreSQL service running, open a PowerShell terminal at the repository root and run:

```powershell
uv --directory backend run alembic upgrade head
$env:LOCAL_RUNS_ENABLED = "true"
uv --directory backend run uvicorn app.main:app --host 127.0.0.1 --port 8012 --no-proxy-headers --no-access-log
```

In another terminal, run `uv --directory backend run python scripts/smoke_local_runs.py`. The script creates a temporary guest, runs AS-011 with each profile, reads back the ordered events, then revokes its guest. To retain evidence for inspection, use the local API with your own guest. Send its bearer credential in the Authorization header. POST to `/api/v1/runs` with an `Idempotency-Key` header and JSON containing `agent_version_id` and `scenarios` (an ordered list). GET the returned run ID at `/api/v1/runs/{id}`, `/{id}/results` or `/{id}/traces` under the same prefix. POST to `/{id}/cancel` to request cancellation.

AS-011 exercises a routine document lookup. Enable `search_docs` on the profile version to see a mock read. AS-010 exercises repeated requests and the six-call budget. Behavior version 1 uses the scripted profile, the fixture, the version's tool list and the previous mock observation. Prompt edits change the recorded hash and input size. Scripted decisions follow the checked-in program. The API returns evidence-derived scores. The run and trace UI presents those scores at `/runs`.

### Verify a policy decision

For AS-006 revision 2, select a version that allows `send_message_simulated`. Submit `scenarios: ["AS-006"]`. A hardened profile returns `requires_confirmation` by default. To approve its single mock delivery, add the following `confirmation` object to the run request. The vulnerable profile proposes a different synthetic destination, which the gateway blocks even when this approval is present.

```json
{
  "confirmation": {
    "scenario": "AS-006",
    "step": 1,
    "tool": "send_message_simulated",
    "arguments": {"destination": "mock-inbox", "content": "Workspace hours reviewed."}
  }
}
```

Read the owner-only trace to see the request and decision reason. An approved action returns an in-memory simulated receipt. All twelve fixtures use the same gateway and run limits.

### Run the full benchmark

With the loopback API on port 8012, run `uv --directory backend run python scripts/smoke_suite.py`. It runs both read-only shared profiles against PostgreSQL, prints counts and revokes its temporary guest.

For a retained run, get a guest credential, select the latest shared agent version and POST `{"agent_version_id":"<version UUID>","suite_id":"core-v2"}` to `/api/v1/runs` with the bearer credential and a fresh `Idempotency-Key`. Poll the returned run ID. Read its `/results`, `/metrics`, `/findings` and `/traces` using the same credential. Each finding’s `evidence_id` identifies a specific trace event. A null percentage denotes an empty denominator.

## Checks

```powershell
uv --directory backend run ruff check .
uv --directory backend run ruff format --check .
uv --directory backend run pytest
npm --prefix frontend run format:check
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
```

Database integration tests skip unless `TEST_DATABASE_URL` is set. To include it against the local Compose database in PowerShell:

```powershell
$env:TEST_DATABASE_URL = "postgresql://agentshield:local-development-only@127.0.0.1:5432/agentshield"
uv --directory backend run pytest
```

Use a dedicated migrated local test database when running these tests. This example matches the local Compose defaults. Update it if you changed your local database values. Copying a dotenv file does not populate PowerShell environment variables. CI provides a disposable PostgreSQL 17 service and runs the integration test.

The CI workflow also validates Compose configuration and builds the backend container. Docker/Compose were not available on the local implementation machine; their execution must be verified in CI or an equipped environment.

## Hosted verification

From an interactive terminal in the backend directory, `python -m scripts.verify_hosted` checks the fixed deployed API with fresh temporary guests and revokes them afterward. It exercises CORS, ownership, shared immutability, idempotency, cancellation, report access and live rate rejection. Running it consumes the normal public quotas.

The optional `--recovery-check` pauses while an explicitly approved, verification-only orphan/expiry fixture is staged and the existing service is redeployed. Credentials remain in process memory. The exact observed method and results are in [the deployment record](context/deployment.md).

![Hosted report history](docs/screenshots/live-reports.jpg)

## Free deployment

Use Vercel Hobby for the frontend, Render Free for one backend process, and Neon Free for PostgreSQL, subject to current eligibility. Provider subdomains provide HTTPS. Free services may sleep, restart, hit quotas, or become unavailable; this is a low-traffic portfolio deployment without guaranteed uptime.

- Vercel root: `frontend`; tracked configuration: `frontend/vercel.json`.
- Render configuration: `render.yaml`; Docker context `backend`, Dockerfile `backend/Dockerfile`, locked Python build, and `sh scripts/start.sh`.
- Set the real backend-only `DATABASE_URL`, explicit JSON `CORS_ORIGINS`, and frontend `VITE_API_BASE_URL`.
- Render's process health path is `/api/v1/health`; separately verify database readiness.
- Public scripted execution is enabled with the owner’s explicit approval. Optional inference is disabled. The service uses the existing external Neon database.
- Complete owner sign-ins and confirm free-plan/billing settings before provisioning.

Open the [live AgentShield app](https://agentshield-ai-tau.vercel.app), [custom authoring](https://agentshield-ai-tau.vercel.app/scenarios), [Settings](https://agentshield-ai-tau.vercel.app/settings) or [system status](https://agentshield-ai-tau.vercel.app/system). On November 17, the hosted frontend reached healthy API and database endpoints and completed both twelve-case scripted suites, comparisons and report downloads. The November 18 extension passed CI, migration 0008, mixed curated/custom API runs, comparison/export ownership and public browser authoring, older-version execution, settings reload and mobile checks. Guest authorization is issued by the app. No durable account or model key is required.

Release proof: [custom authoring](docs/screenshots/custom-authoring-live.jpg), [selected revision and completed custom run](docs/screenshots/custom-run-live.jpg), [Settings](docs/screenshots/settings-live.jpg), and [all three CI jobs](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/runs/44241232149). Full settings and limitations are recorded in the dated context documents.

Follow [context/deployment.md](context/deployment.md) for the exact configuration and release procedure. Vercel GitHub integration is not installed, so frontend releases currently upload reviewed source through the API. Render automatic deploy is off. Free services may sleep or suspend at quota limits. Hosted warm suites, ownership, exports and restart regeneration were verified on November 17. One real idle wake returned valid health JSON in 32.812 seconds. The saved sample remained available during wake-up and manual retry restored API connectivity. See the dated deployment record for the observation and limitations.

## Current scope and limitations

The owner authorized closing FR-03 and FR-13 after the audit. Both are implemented, deployed and verified locally, in CI and through the public application. Custom scenarios use two registered checkers with bounded data fields. Settings selects a default scripted profile and displays operator-managed capability/limit information; it accepts no visitor credentials. The listed audit fixes and mandatory release gates for the bounded scripted MVP are complete.

Optional real-model inference has no adapter, eligible free account, parsing/retry/quota evidence or provider-token measurements. Scripted byte budgets are not token accounting. Exact finite oracles do not establish general security. Anonymous quotas and temporary tab credentials limit availability and persistence. One observed 32.812-second cold wake and two single warm timings are not latency guarantees or throughput measurements.

This application-controlled simulation uses synthetic data and mock actions. It does not execute untrusted code or test arbitrary external systems. Free services may sleep, restart or suspend at quotas. No paid fallback is configured.

## Documentation map

| Document | Purpose |
|---|---|
| [AgentShield_PROJECT.md](AgentShield_PROJECT.md) | Full specification |
| [requirement.md](requirement.md) | Acceptance requirements |
| [context/system design.md](context/system%20design.md) | Runtime flows and trust boundaries |
| [context/architecture.md](context/architecture.md) | Modules and implementation decisions |
| [context/phasewise_roadmap.md](context/phasewise_roadmap.md) | Phase scope, status, and gates |
| [context/deployment.md](context/deployment.md) | Hosting runbook and observed results |
| [context/performance_review.md](context/performance_review.md) | Actual verification evidence |
| [context/benchmark.md](context/benchmark.md) | Evaluation and performance methodology |
| [docs/threat-model.md](docs/threat-model.md) | Implemented controls, verification and residual risks |
| [AGENTS.md](AGENTS.md) | Development and publication instructions |

Owner: **Pranjal Tyagi**. Repository: [Pranjaltyagi76/AgentShield_AI](https://github.com/Pranjaltyagi76/AgentShield_AI). New commits use the owner's author/committer identity without bot co-author attribution. Prefer four to six meaningful commits per substantial push; never manufacture history.
