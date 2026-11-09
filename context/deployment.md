# AgentShield AI: Free Deployment Runbook

Status: planned; no frontend, API, database, or live demo deployment has been verified. Last updated: November 10, 2026.

## Budget and topology

Deploy a static React build on Vercel Hobby, one Python/FastAPI process on Render Free, and PostgreSQL on Neon Free. Optional inference uses a currently eligible Gemini free-tier model only. Local development uses existing hardware and Docker Compose. Use free provider subdomains and HTTPS.

Use ongoing free plans, not expiring trial credits. Do not enable automatic upgrades, paid fallbacks, paid workers, paid disks, hosted GPUs, paid schedulers, or paid monitoring. Budget notifications alone do not guarantee zero spending. If an optional service cannot operate without chargeable billing, disable it. Quota exhaustion should suspend the affected capability rather than incur charges.

The owner performs sign-ins and account verification. Never record credentials, session tokens, database passwords, or private dashboard links in this file. Commit placeholder-only `.env.example` later during Phase 0; local real `.env` files stay ignored.

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

1. Confirm that generated frontend/backend code and CI exist. This document alone does not provide runnable services.
2. Create a Neon Free project, select a suitable available region, and obtain its TLS-enabled pooled database URL in the provider dashboard. Configure a small application connection pool. Do not publish the URL.
3. Create the Render Free web service from the repository. Use the `backend` root, a supported Python runtime, and build commands derived from the actual dependency manifest produced in Phase 0. Do not guess a missing lockfile or install command.
4. Configure only required settings; keep public runs and LLM inference disabled. Use one Uvicorn process bound to `0.0.0.0` and the host-assigned port.
5. Implement `/api/v1/health` for process health and `/api/v1/ready` for a bounded database check and, once migrations exist, schema readiness. Neither endpoint invokes a model.
6. Create a Vercel Hobby project with root `frontend`. Once scripts exist, use the Vite build script and its `dist` output. Configure SPA route fallback without intercepting assets; verify a direct visit to a nested route.
7. Set the frontend API base URL to the actual backend origin plus the API prefix expected by the client. Document that convention in the implemented client so `/api/v1` is not duplicated.
8. Restrict backend CORS to the deployed frontend and explicit development origins; do not wildcard preview origins. Add optional preview origins deliberately when needed.
9. Verify shell loading, HTTPS health/readiness, browser-to-API requests, and a real database connection. Record dated results below. No public feature mutation endpoints are exposed in Phase 0.

## Full application startup after migrations exist

Run the checked-in Alembic migration command once before the API starts, then start the single process. The intended sequence is `alembic upgrade head` followed by `uvicorn app.main:app --host 0.0.0.0 --port <host PORT>` from the backend root. Convert this into an actual host-compatible checked-in startup script during implementation; `<host PORT>` is a placeholder, not a runnable command. Propagate any migration failure and do not report readiness after failure.

Do not rely on a paid pre-deploy hook, host shell, or separate migration job. Validate migration commands on a clean database. Never use an old database restore as the first rollback action without preserving current evidence.

## Configuration contract

| Setting | Intended value/handling |
|---|---|
| `DATABASE_URL` | Secret TLS-enabled pooled PostgreSQL URL |
| `APP_ENV` | Deployment environment identifier |
| `CORS_ORIGINS` | Explicit allowed frontend and local-development origins |
| `SECRET_KEY` | Owner-provisioned high-entropy backend secret; never frontend-visible |
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

| Item | Current evidence |
|---|---|
| Repository | [Pranjaltyagi76/AgentShield_AI](https://github.com/Pranjaltyagi76/AgentShield_AI); read connectivity previously checked |
| Frontend URL | Not provisioned or verified |
| Backend URL | Not provisioned or verified |
| Database connection | Not provisioned or verified |
| Free billing settings | Not inspected in owner accounts |
| Live benchmark | Not run |
| Cold-start duration | Not measured |
| Last successful deployment revision | None recorded |

Replace these entries with dated observations as work progresses. Never infer a successful deployment from a CI badge, build log, or a saved sample alone.
