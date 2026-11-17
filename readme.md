# AgentShield AI

AI agent security testing, controlled attack simulation, and reliability benchmarking.

**Phase 6 benchmark comparisons are implemented and verified locally. The public site still runs Phase 0.** Open `/agents` locally to start a seven-day workspace, create profiles, edit metadata, and save immutable versions. Open `/scenarios` to search twelve curated definitions without a session.

The required product will work without an AI API key, using synthetic data and mock actions. Scripted demo results will demonstrate the actual harness; they will not establish real-model resistance to prompt injection.

## Available now

- Responsive React/Vite/TypeScript workspace with Overview, System status, roadmap, and not-found routes.
- FastAPI process health and real PostgreSQL readiness endpoints.
- Validated environment settings, restricted CORS, safe JSON errors, request IDs, and structured logs.
- Guest-only profile mutations; shared examples are read-only. Scripted runs require explicit opt-in. No inference key is needed.
- Small SQLAlchemy/psycopg connection pool and bounded connection/query timeouts.
- Local PostgreSQL Compose configuration, backend Dockerfile, committed npm/uv dependency locks, and CI.
- Free Render/Vercel deployment configuration and an initial threat model.

Phase 1 local verification (November 16): 35 backend tests passed with PostgreSQL and 13 frontend tests passed. The catalog and private profile creation were also checked in the browser.

Historical Phase 0 verification (November 16): the backend suite contains **32 cases**; **31 passed locally and one database integration case skipped** without TEST_DATABASE_URL. [CI with PostgreSQL](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/runs/43859035364) passed all jobs, including the database integration check, frontend checks/build, and container build. The frontend suite contains **11 tests**. Live Render readiness also reached Neon successfully. These are foundation tests, not security benchmark results. See [performance review](context/performance_review.md) for environment and limitations.

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

`GET /api/v1/health` reports process health independently of PostgreSQL. `GET /api/v1/ready` reports `connected`, `unavailable`, or `not_configured`, with HTTP 503 when not ready. Phase 6 readiness requires Alembic revision `0006`.

Stop the database with `docker compose down`. This preserves the named data volume. Removing the volume deletes local database data, so do not do that as an ordinary shutdown step.

## Launch a benchmark in the browser

Start loopback PostgreSQL as described above. In a backend terminal, migrate the database, enable local runs and start the API on the port used by the Vite proxy.

```powershell
uv --directory backend run alembic upgrade head
$env:LOCAL_RUNS_ENABLED = "true"
uv --directory backend run uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers --no-access-log
```

Run `npm --prefix frontend run dev` in another terminal and open [Benchmark runs](http://127.0.0.1:5173/runs). Start a guest workspace, select an agent version and launch Core v2 or selected scenarios. Open a finding’s evidence link to inspect its highlighted event. Expand a tool request to see its arguments, policy decision and recorded mock result. The same tab can reopen a run from history. Guest access expires after seven days or revocation.

## Optional Gemini status

Phase 7 uses the specification’s disabled-inference exit branch. This workspace has no configured Gemini credential and account-specific free access has not been verified. The API supports scripted execution through Phase 6. `GET /api/v1/demo/status` reports whether scripted execution is enabled by configuration and why Gemini is disabled. Database readiness remains available at `/ready`.

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

## Free deployment

Use Vercel Hobby for the frontend, Render Free for one backend process, and Neon Free for PostgreSQL, subject to current eligibility. Provider subdomains provide HTTPS. Free services may sleep, restart, hit quotas, or become unavailable; this is a low-traffic portfolio deployment without guaranteed uptime.

- Vercel root: `frontend`; tracked configuration: `frontend/vercel.json`.
- Render configuration: `render.yaml`; Docker context `backend`, Dockerfile `backend/Dockerfile`, locked Python build, and `sh scripts/start.sh`.
- Set the real backend-only `DATABASE_URL`, explicit JSON `CORS_ORIGINS`, and frontend `VITE_API_BASE_URL`.
- Render's process health path is `/api/v1/health`; separately verify database readiness.
- Keep execution/inference disabled. No model keys, paid disk, worker, or Render database are provisioned.
- Complete owner sign-ins and confirm free-plan/billing settings before provisioning.

Open the [live AgentShield foundation](https://agentshield-ai-tau.vercel.app) or its [system status](https://agentshield-ai-tau.vercel.app/system). The browser reaches the [backend health](https://agentshield-api-hn0q.onrender.com/api/v1/health) and [database readiness](https://agentshield-api-hn0q.onrender.com/api/v1/ready) endpoints; both returned HTTP 200 on November 16. No sign-in or model key is required for this foundation smoke test. Public execution on the hosted foundation is disabled. See the deployment record for the pending Phase 3 release.

Follow [context/deployment.md](context/deployment.md) for the exact configuration and release procedure. Vercel GitHub integration is not installed, so frontend releases currently upload reviewed source through the API. Render automatic deploy is off. Free services may sleep or suspend at quota limits; no uptime or measured cold-start claim is made.

## Planned product

Later phases add HTML/JSON reports, a saved example, and hosted validation of the scripted workflow. Optional eligible Gemini free-tier testing stays separate from scripted results.

This is an application-controlled simulation harness. It does not execute untrusted code or test arbitrary external systems. A passing finite benchmark does not prove complete security.

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
| [context/benchmark.md](context/benchmark.md) | Future benchmark methodology |
| [docs/threat-model.md](docs/threat-model.md) | Initial threats, controls, and remaining risks |
| [AGENTS.md](AGENTS.md) | Development and publication instructions |

Owner: **Pranjal Tyagi**. Repository: [Pranjaltyagi76/AgentShield_AI](https://github.com/Pranjaltyagi76/AgentShield_AI). New commits use the owner's author/committer identity without bot co-author attribution. Prefer four to six meaningful commits per substantial push; never manufacture history.
