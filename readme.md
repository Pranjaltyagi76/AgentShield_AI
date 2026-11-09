# AgentShield AI

AI agent security testing, controlled attack simulation, and reliability benchmarking.

**Current status: Phase 0 foundation implemented and verified locally. The initial public deployment gate is still pending hosting-account connections.** Agent profiles, scenario execution, policy evaluation, and reports are planned for later phases.

The required product will work without an AI API key, using synthetic data and mock actions. Scripted demo results will demonstrate the actual harness; they will not establish real-model resistance to prompt injection.

## Available now

- Responsive React/Vite/TypeScript workspace with Overview, System status, roadmap, and not-found routes.
- FastAPI process health and real PostgreSQL readiness endpoints.
- Validated environment settings, restricted CORS, safe JSON errors, request IDs, and structured logs.
- Phase 0 execution/inference flags locked off; no feature mutation endpoints.
- Small SQLAlchemy/psycopg connection pool and bounded connection/query timeouts.
- Local PostgreSQL Compose configuration, backend Dockerfile, committed npm/uv dependency locks, and CI.
- Free Render/Vercel deployment configuration and an initial threat model.

Local verification: **17 backend tests and 11 frontend tests passed**, including real PostgreSQL connectivity. Lint, formatting, TypeScript, and the production frontend build passed. These are foundation tests, not security benchmark results. See [performance review](context/performance_review.md) for environment and limitations.

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
uv --directory backend run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

In a separate frontend terminal:

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open [the local workspace](http://127.0.0.1:5173). The frontend proxies `/api` to port 8000; `VITE_API_BASE_URL` includes `/api/v1` exactly once. Development API docs are at [localhost:8000/docs](http://127.0.0.1:8000/docs). Production disables the interactive docs.

`GET /api/v1/health` reports process health independently of PostgreSQL. `GET /api/v1/ready` reports `connected`, `unavailable`, or `not_configured`, with HTTP 503 when not ready. No feature tables or migrations are created in Phase 0; schema migrations begin in Phase 1.

Stop the database with `docker compose down`. This preserves the named data volume. Removing the volume deletes local database data, so do not do that as an ordinary shutdown step.

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

The database integration test intentionally skips unless `TEST_DATABASE_URL` is set. To include it against the local Compose database in PowerShell:

```powershell
$env:TEST_DATABASE_URL = "postgresql://agentshield:local-development-only@127.0.0.1:5432/agentshield"
uv --directory backend run pytest
```

This example matches the local Compose defaults. Update it if you changed your local database values. Copying a dotenv file does not populate PowerShell environment variables. CI provides a disposable PostgreSQL 17 service and runs the integration test.

The CI workflow also validates Compose configuration and builds the backend container. Docker/Compose were not available on the local implementation machine; their execution must be verified in CI or an equipped environment.

## Free deployment

Use Vercel Hobby for the frontend, Render Free for one backend process, and Neon Free for PostgreSQL, subject to current eligibility. Provider subdomains provide HTTPS. Free services may sleep, restart, hit quotas, or become unavailable; this is a low-traffic portfolio deployment without guaranteed uptime.

- Vercel root: `frontend`; tracked configuration: `frontend/vercel.json`.
- Render configuration: `render.yaml`; root: `backend`; locked build and `sh scripts/start.sh`.
- Set the real backend-only `DATABASE_URL`, explicit JSON `CORS_ORIGINS`, and frontend `VITE_API_BASE_URL`.
- Render's process health path is `/api/v1/health`; separately verify database readiness.
- Keep execution/inference disabled. No model keys, paid disk, worker, or Render database are provisioned.
- Complete owner sign-ins and confirm free-plan/billing settings before provisioning.

Follow [context/deployment.md](context/deployment.md). No live frontend/backend URL or Neon connection has been verified yet.

## Planned product

Later phases add isolated guest sessions, versioned agent configurations, 12 curated scenarios, vulnerable/hardened scripted profiles, independently enforced tool policies, redacted evidence traces, deterministic metrics, regression comparisons, and HTML/JSON reports. Optional eligible Gemini free-tier testing stays separate from scripted results.

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
