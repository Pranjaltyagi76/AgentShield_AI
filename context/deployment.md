# AgentShield AI: Free Deployment Runbook

Status: Render Free backend and Neon Free database verified over public HTTPS on November 16, 2026. Vercel scope authorization and public frontend smoke verification remain pending.

Reuse the existing resources in the observed deployment record below. Do not provision duplicate AgentShield services or projects when continuing this task.

## Budget and topology

Deploy a static React build on Vercel Hobby, one Python/FastAPI process on Render Free, and PostgreSQL on Neon Free. Optional inference uses a currently eligible Gemini free-tier model only. Local development uses existing hardware and Docker Compose. Use free provider subdomains and HTTPS.

Use ongoing free plans, not expiring trial credits. Do not enable automatic upgrades, paid fallbacks, paid workers, paid disks, hosted GPUs, paid schedulers, or paid monitoring. Budget notifications alone do not guarantee zero spending. If an optional service cannot operate without chargeable billing, disable it. Quota exhaustion should suspend the affected capability rather than incur charges.

The owner performs sign-ins and account verification. Never record credentials, session tokens, database passwords, or private dashboard links in this file. The committed `.env.example` contains placeholders/local development values only; real connection credentials remain in provider environment settings and out of Git.

## Provider references

These are the reviewed plan choices from November 10, 2026, not promises of unchanged future availability. Recheck the official pages during initial setup and final validation.

| Service | Relevant constraint | Reference |
|---|---|---|
| Vercel Hobby | Eligible personal/non-commercial projects; usage caps apply | [Hobby plan](https://vercel.com/docs/plans/hobby) |
| Render Free | Sleeps after 15 idle minutes; wake-up about one minute; restarts and ephemeral disk | [Free service documentation](https://render.com/docs/free) |
| Render billing | With a payment method, bandwidth/build overages may be charged; otherwise suspension/disabled builds | [Free limits and billing](https://render.com/docs/free) |
| Render PostgreSQL Free | Expires after 30 days; not our permanent database | [Free database limits](https://render.com/docs/free) |
| Neon Free | Currently 1 GB storage and 100 CU-hours per project monthly; scale-to-zero; no card required | [Pricing](https://neon.com/pricing) |
| Gemini | Free access is model-dependent; usage/data-use terms and quotas apply | [Pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| GitHub Actions | Standard runners free for public repos; artifact/cache storage has allowances | [Billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) |

Do not add artificial keep-alive requests to defeat host sleep. Use small database pools, backoff polling, bounded payloads, retention, and application storage thresholds to conserve capacity.

## Phase 0 smoke deployment

1. Use the implemented frontend/backend source, committed npm/uv locks, and CI. Local setup and check commands are in the root readme. The remaining hosted gate requires the owner to authorize the existing Vercel connection for the configured scope.
2. Create a Neon Free project, select a suitable available region, and obtain its TLS-enabled pooled database URL in the provider dashboard. Configure a small application connection pool. Do not publish the URL.
3. Reuse the Render Free Docker web service. Its repository root is unchanged; `dockerContext` is `backend` and `dockerfilePath` is `backend/Dockerfile`. The Dockerfile installs from the locked Python dependencies and starts `sh scripts/start.sh`. The matching `render.yaml` template selects Free/Singapore, has no Render database/disk/worker, and keeps automatic deployment off.
4. Configure only required settings; keep public runs and LLM inference disabled. Use one Uvicorn process bound to `0.0.0.0` and the host-assigned port.
5. Implement `/api/v1/health` for process health and `/api/v1/ready` for a bounded database check and, once migrations exist, schema readiness. Neither endpoint invokes a model.
6. Create a Vercel Hobby project with root `frontend`. Use `npm ci`, `npm run build`, and output `dist`. The tracked `frontend/vercel.json` rewrites the known `/system` and `/roadmap` routes without intercepting assets and sets production security headers. Add routing rules when future routes are implemented; verify direct visits after hosting. Its CSP now restricts connections to the provisioned API origin.
7. Set the frontend API base URL to the actual backend origin plus the API prefix expected by the client. Document that convention in the implemented client so `/api/v1` is not duplicated.
8. Restrict backend CORS to the deployed frontend and explicit development origins; do not wildcard preview origins. Add optional preview origins deliberately when needed.
9. Verify shell loading, HTTPS health/readiness, browser-to-API requests, and a real database connection. Record dated results below. No public feature mutation endpoints are exposed in Phase 0.

## Implemented Phase 0 startup

The live Render Docker build installs from `backend/uv.lock` using `uv sync --locked --no-dev --no-install-project` in `backend/Dockerfile`. `backend/scripts/start.sh` runs one Uvicorn worker, binds the host-provided port, and disables default access logs to avoid logging arbitrary query strings. It performs no feature-schema migration because Phase 0 has no feature tables. The same Dockerfile is checked by CI and deployed on Render; the backend remains Python/FastAPI.

Local smoke verification used actual PostgreSQL on loopback and the Vite proxy. Docker is missing on the implementation machine, so the local database connectivity check used an ignored temporary portable PostgreSQL binary; The initial hosted CI run verified the backend container build and frontend checks. The backend test/Compose job required a corrected setup-uv reference; follow the linked Actions history in the performance review for the latest result. Neither a temporary local database nor a green local readiness response proves Neon connectivity.

## Live configuration and continuation

The service was created directly with Render MCP in the workspace explicitly selected by the owner. It is not attached to a Blueprint. `render.yaml` is a schema-validated recreation/configuration template, not evidence of an applied Blueprint sync; do not adopt or replace the live service without reviewing that operation. The direct creation tool did not expose an HTTP health-check-path field, so the live platform probe is TCP. Both `/api/v1/health` and `/api/v1/ready` were independently verified over HTTPS. The template retains the intended HTTP health check for a future reviewed configuration application.

The live `CORS_ORIGINS` is currently `[]` while the frontend is not provisioned. After Vercel authorization, verify the target scope is eligible for Hobby, reuse/create the AgentShield frontend with root `frontend`, set public `VITE_API_BASE_URL=https://agentshield-api-hn0q.onrender.com/api/v1`, and deploy the reviewed source revision. Then merge the exact frontend origin into Render CORS without retrieving/replacing the database secret; trigger one manual deploy because auto-deploy is off. Verify browser-to-API-to-Neon behavior and deep links before completing Phase 0. Do not enable wildcard origins.

Vercel returned 403 for scope `pranjal-tyagi-ai` (`team_mRdCuSvoFHIrkEm4K3UAPs7P`). Use `authorize_team_access` to generate a fresh short-lived consent link when the owner is ready, then retry the original request after approval. Do not ask the owner to paste API tokens, do not switch scopes to evade the denial, and do not commit consent links.

## Full application startup after migrations exist

Run the checked-in Alembic migration command once before the API starts, then start the single process. The intended sequence is `alembic upgrade head` followed by `uvicorn app.main:app --host 0.0.0.0 --port <host PORT>` from the backend root. Convert this into an actual host-compatible checked-in startup script during implementation; `<host PORT>` is a placeholder, not a runnable command. Propagate any migration failure and do not report readiness after failure.

Do not rely on a paid pre-deploy hook, host shell, or separate migration job. Validate migration commands on a clean database. Never use an old database restore as the first rollback action without preserving current evidence.

## Configuration contract

| Setting | Intended value/handling |
|---|---|
| `DATABASE_URL` | Secret TLS-enabled pooled PostgreSQL URL |
| `APP_ENV` | Deployment environment identifier |
| `CORS_ORIGINS` | Explicit allowed frontend and local-development origins |
| `SECRET_KEY` | Deferred until session/auth features require it; Phase 0 creates no guest credentials |
| `LLM_PROVIDER` | `demo` by default |
| `GEMINI_API_KEY` | Optional backend-only key; absent for required demo |
| `PUBLIC_RUNS_ENABLED` | Off until guest isolation, bounds, and policy enforcement pass |
| `PUBLIC_LLM_ENABLED` | `false` by default; enable only after free eligibility/budgets are confirmed |
| `GUEST_RETENTION_DAYS` | `7` initially |
| `MAX_CONCURRENT_RUNS` / `MAX_QUEUED_RUNS` | `2` / `10` globally initially |
| `MAX_DATABASE_BYTES` | Initial application-data ceiling of 524288000 bytes (500 MiB) |
| `LOG_LEVEL` | Bounded structured operational logging without sensitive payloads |
| `VITE_API_BASE_URL` | Public backend API address; contains no secret |

The detailed server settings, token/byte/time limits, and their validation are defined in Section 7 of [the specification](../AgentShield_PROJECT.md). Do not store visitors' provider keys in the MVP. Validate missing required settings at startup and distinguish optional inference unavailability from API readiness.

## Final acceptance checks

- A clean browser session opens the real frontend; a direct nested route also works.
- HTTPS health/readiness and frontend API calls succeed with the configured database.
- Two independent guest sessions cannot read/mutate each other's agents, runs, evidence, comparisons, or reports; shared examples cannot be modified.
- Both demo profiles execute all 12 scenarios through the real pipeline without an API key; outcomes and traces are evidence-derived.
- Run creation is idempotent; full queue and rate limits return explicit errors; cancellation and restart interruption preserve evidence.
- Model errors stay errors/inconclusive; no automatic scripted substitution or paid fallback occurs.
- Compatibility checks, metric counts/coverage, HTML/JSON export, and safe HTML escaping work.
- Report downloads still work after backend restart while their database sources are retained.
- Guest expiry denies access immediately; bounded cleanup removes dependent records when the process is active.
- A cold start shows a waking/retry state; the bundled redacted saved sample is labelled historical and works without API access.
- Free plans, billing settings, usage limits, and disabled optional paid capabilities are rechecked.

## Recovery and data handling

If costs or limits become uncertain, disable inference first and stop accepting new runs using the operator switches. Preserve existing bounded reads/exports where services remain available. Quota suspension is an accepted free-tier limitation; do not upgrade to clear it without a new owner decision.

After restart, fail orphaned active runs as interrupted and preserve their partial evidence. Generate reports from database state, never local stored files. Keep a manual export procedure for synthetic data/configuration, with credentials excluded. Backups on existing local storage are optional and do not imply permanent guest retention. Roll back an application revision only if database migrations remain compatible; record any migration repair as a new change.

## Observed deployment record

Verified November 16, 2026. No credentials or connection strings are recorded here.

| Item | Current evidence |
|---|---|
| Repository | [Pranjaltyagi76/AgentShield_AI](https://github.com/Pranjaltyagi76/AgentShield_AI) |
| Frontend URL | Not provisioned; Vercel scope grant required |
| Backend health | [Live HTTPS health](https://agentshield-api-hn0q.onrender.com/api/v1/health): HTTP 200, status ok, phase 0 |
| Backend database readiness | [Live HTTPS readiness](https://agentshield-api-hn0q.onrender.com/api/v1/ready): HTTP 200, database connected |
| Render resource | agentshield-api; service ID srv-dbtefcmtlv9c73f4i2pg; Free plan; Singapore; one Docker instance; auto-deploy off |
| Successful Render deploy | dep-dbteiqgn74is73bmec5g; live at 2026-11-16 11:31:25 UTC |
| Deployed application revision | 5b48b865f45aef02044cc6e567302ff9c2779915 |
| Neon resource | agentshield-ai; project nameless-paper-98324516; organization Pranjal on Free; Singapore; PostgreSQL 17 |
| Neon compute | Fixed 0.25 CU minimum/maximum; Free idle policy left at its default |
| Database verification | Standalone SELECT 1 passed; deployed FastAPI readiness also reached the pooled Neon connection |
| Phase 0 execution/inference | Disabled; /api/v1/runs returned 404; /docs returned 404 in production |
| CORS | Unapproved-origin response had no allow-origin header; current allowed-origin list is empty pending frontend creation |
| Runtime error scan | No error-level app logs in the corrected deploy's scanned window |
| CI | [Deployment-fix CI](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/runs/43858216273): frontend, backend/PostgreSQL, and container build succeeded |
| Billing verification | Render service plan Free and Neon organization plan Free confirmed; no paid upgrade requested; account payment-method settings not inspected |
| Live benchmark | Not run; scenario execution is outside Phase 0 |
| Cold-start duration | Not measured; initial deploy duration is not a post-idle cold-start measurement |
| Local browser smoke | November 10: API/database connected and 1440px/390px navigation inspected locally |
| Remaining gate | Vercel scope approval, Hobby eligibility check, frontend deployment, exact CORS update, and public browser smoke |

The first Render deploy (dep-dbtefdetlv9c73f4i4r0) failed because Literal[False] settings rejected hosting environment strings. The corrected application normalizes explicit false spellings while rejecting true/unknown inputs, with 15 new regression cases. Preserve this failure and fix as historical evidence; never describe the first attempt as successful.
