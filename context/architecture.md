# AgentShield AI: Architecture

Status: Phase 0 foundation and public deployment smoke complete; Phase 1 registry and catalog implemented locally; the scripted evaluator, run UI and Phase 6 comparisons are verified locally. Last reviewed November 17, 2026.

## Decisions

| Decision | Reason and consequence |
|---|---|
| React + Vite + TypeScript | Static frontend deployment; no Node.js backend |
| Python 3.12+ + FastAPI | Typed HTTP API and a maintainable Python evaluation runtime |
| CI-tested Python Docker container on Render Free | Live backend uses backend/Dockerfile with one process; no change to the Python/FastAPI backend |
| PostgreSQL + SQLAlchemy 2 + Alembic | Durable relational state, version references, and explicit migrations |
| Modular monolith, one API process | Fits a single free web service and simple bounded execution |
| PostgreSQL queue + in-process consumer | Persists state without a mandatory broker or paid worker |
| Guest sessions first | Isolated temporary workspaces without account/email infrastructure |
| Scripted demo + optional Gemini | Required workflow stays independent of API availability |
| HTML/JSON generated on demand | No persistent disk or object-storage dependency |

LangGraph, LLM judging, PDF generation, durable accounts, multiple workers, and public model hosting are deferred. Adding any of them requires explicit scope and zero-spend review.

## Planned repository layout

Paths below are planned unless present in the current working tree. The context folder is the maintained development reference; do not create competing copies of its architecture or deployment documents under another folder.

```text
AgentShield_AI/
  AGENTS.md
  AgentShield_PROJECT.md
  requirement.md
  readme.md
  context/
    system design.md
    architecture.md
    phasewise_roadmap.md
    deployment.md
    performance_review.md
    benchmark.md
  frontend/
    src/
      app/          # routing, providers, application shell
      components/   # shared presentation components
      features/     # agents, scenarios, runs, traces, comparisons, reports
      pages/
      lib/          # API client, session handling, shared utilities
      types/
    public/         # redacted saved sample report, later in Phase 8
    package.json
  backend/
    app/
      api/
      core/
      sessions/
      agents/
      scenarios/
      sandbox/
      policies/
      tracing/
      evaluation/
      benchmark/
      reports/
      db/
    tests/
    alembic/
    pyproject.toml
  scenario-pack/
  docs/             # supporting threat model and decision records as needed
  scripts/
  .github/workflows/
  docker-compose.yml
  .env.example
  .gitignore
```

## Hosted foundation status

The Vercel Hobby static frontend, Render Free Docker API, and Neon Free PostgreSQL connection are live and verified together in the browser. The frontend uses the public backend API base and its CSP permits only that API origin. Render CORS explicitly lists the two production aliases, without wildcard previews. Vercel releases upload reviewed frontend source through its API because the GitHub integration is not installed; automatic GitHub frontend deployment is not configured. Vercel's default deployment protection is retained; the canonical production domain is public. The Render service was created directly with MCP, with no Blueprint attached and automatic deploy off. See deployment.md for exact evidence and resource IDs.

## Run and trace frontend

The React routes `/runs` and `/runs/:runId` share the registry’s tab-scoped guest session. The launcher records a pending idempotency key and its request configuration for ambiguous retries. The status query polls active runs every 2.5 seconds in the foreground, stopping on a terminal response, error or 100 updates. Evidence reloads on status transitions, selection or manual refresh. Each query is scoped to the mounted guest workspace. A finding links to the run, scenario and event ID. The owned trace API filters by scenario and redacts values before the browser receives them.

## Retained reports and saved workspace

Migration `0007` stores report metadata with run ID, optional comparison ID, format, renderer version and creation time. A unique ordered source/format/version tuple uses PostgreSQL NULLS NOT DISTINCT to deduplicate reports without a comparison. Guest-row locking serializes report admission. The 64-report guest ceiling and configured database limit bound storage. Both foreign keys cascade when a source is deleted.

The report API checks the source run and both comparison inputs on creation, metadata reads and downloads. Only terminal runs can create reports. Renderer v1 builds HTML or JSON from retained results, configuration and ordered trace evidence. HTML text is escaped, includes no scripts, uses local evidence anchors and is sent as an attachment with a sandbox CSP. Protected synthetic values are redacted before rendering. No report path or generated file is stored on the backend.

`/reports` provides paginated guest history. Export controls appear on finished runs and comparisons. The frontend fetches download bodies with an Authorization header and creates a temporary Blob URL. A guest change during a download prevents the old workspace response from being offered.

`/sample` and the bundled HTML/JSON require no API or session. The saved workspace is captured through the real local runtime using newly issued guest data and shared profiles. Its UUIDs are replaced consistently, preserving finding/evidence references. It is explicitly labelled historical. Readiness polling permits at most three not-ready responses and stops on errors. A manual retry and sample link remain available.

## Optional inference decision

Phase 7 uses the specification’s explicit disabled branch. The release has no network provider adapter or provider SDK. Startup validation accepts only `LLM_PROVIDER=demo` and false `PUBLIC_LLM_ENABLED`. Guest configuration accepts no provider, endpoint or API key overrides. `GET /api/v1/demo/status` returns an explicit disabled Gemini state with reason `free_account_access_unverified`. The scripted execution flag reports configuration, and `/ready` separately probes the database. Phase 7 introduced no schema migration or inference capability. Phase 8 later advances the schema and report capability.

## Benchmark comparisons

Migration `0006` stores an immutable JSONB summary with a unique ordered baseline/candidate pair. Both foreign keys cascade on source deletion. An authenticated POST to `/api/v1/benchmarks/compare` checks both terminal runs belong to the guest. A per-guest transaction lock serializes admissions and retries. A guest can retain 64 comparisons within the configured database limit. Retrying an existing pair returns its saved summary even at capacity. GET `/api/v1/benchmarks/{id}` checks access through both runs.

The pure comparator consumes pinned run configurations and persisted scenario assessments. The React page displays full-run coverage alongside paired metrics, signed changes and per-scenario links back to each source trace.

## Local evaluation

Migration `0005` preserves the frozen Core v1 catalog and adds the Core v2 executable manifest, a second version of each shared profile, and a nullable JSONB assessment on each scenario result. A new run pins fixture revisions, behavior, oracle, policy, tool schema hash and budgets. Previously completed runs retain their original data. A terminal scenario and its assessment commit together. Owner-scoped endpoints aggregate stored assessments and resolve findings by event ID. Evaluation reads bounded evidence server-side before response redaction. Guest trace responses redact the synthetic marker.

## Local simulation runtime

Alembic revision `0003` adds runs, scenario results and ordered trace events with guest-dependent cleanup. The local API locks queue admission in PostgreSQL, snapshots the profile version and public fixture fields, and enforces idempotency per guest. The worker uses a transaction-scoped queue lock and checks the run owner, worker identity and status under row lock on each step. A running job with a heartbeat older than five seconds is marked interrupted and retains partial evidence. Short transactions support transaction-pooled PostgreSQL. Committed submissions wake the consumer. It also checks for pending work at startup and on an idle timer.

The script sees a copy of synthetic task data and its previous observation. The gateway checks the original allowed tools and validated arguments before producing a mock response. Only the gateway produces synthetic tool results. It checks each proposal against the scenario and version allowlists, strict argument schemas, synthetic ownership and protected records, the permitted destination, an exact synthetic private marker, and a six-call budget per scenario. A high-impact action needs the authenticated guest’s approval for that run, scenario, step, tool and arguments. AS-006 revision 2 provides one confirmable message. The script never receives the approval. Migration `0004` retains revision 1 in the frozen Core v1 catalog.

## Implemented Phase 1 registry

SQLAlchemy models and Alembic revisions `0001`/`0002` define guest sessions, agents, immutable agent versions, scenarios and scenario versions. The seed migration creates two shared profiles and AS-001 through AS-012. Catalog serialization selects public columns explicitly. Runtime descriptors and evaluator rules are distinct; no checker executes in this phase. A bounded query provides the Core v1 suite membership. The Docker entrypoint migrates once before startup; readiness rejects missing/outdated schema. `app/api/workspaces.py` owns the API transactions; React routes `/agents` and `/scenarios` use the versioned API.

## Implemented Phase 0 foundation (historical)

Implemented modules are api/system.py, core/settings.py, core/logging.py, db/connection.py, and the application factory in main.py. The database probe uses synchronous SQLAlchemy/psycopg in FastAPI threadpool routes with a two-connection pool, connect/pool/statement timeouts, and no feature tables. Health is independent of the database; readiness returns 503 when unavailable. Production hides interactive docs, and Phase 0 configuration rejects enabling execution or inference.

The frontend uses React Router, TanStack Query, Zod response contracts, Tailwind, lucide icons, and a local shadcn-style Radix-composed Button. There are three foundation routes and a not-found view. Source/lockfiles, tests, CI, Compose, Dockerfile, Render blueprint, and Vercel routing/headers are present. No guest session, agent, or evaluation implementation is included.

## Backend responsibilities

| Module | Owns | Boundary |
|---|---|---|
| `api` | Routes, typed requests/responses, pagination, error mapping | No business rules implemented only in route handlers |
| `core` | Validated settings, limits, lifecycle, structured logging | Never log secrets or session credentials |
| `sessions` | Session issuance/expiry, ownership resolution | No caller-selected owner identity |
| `agents` | Immutable agent versions, demo profiles, provider adapters | Agent cannot invoke tools directly |
| `scenarios` | Declarative versioned definitions, visible/evaluator projections | Oracle context never enters model input |
| `sandbox` | Run loop, synthetic state, registered tools, gateway | No arbitrary code, URL fetches, shell, or real actions |
| `policies` | Deterministic permission and argument rules | Sole execution authority outside model output |
| `tracing` | Ordered evidence and redacted presentation | Record attempted and executed actions separately |
| `evaluation` | Scenario checkers, applicability, aggregate metrics | Missing evidence cannot become a pass |
| `benchmark` | Compatible-pair matching and regression detection | Compare scenario/version/settings compatibility explicitly |
| `reports` | Escaped HTML/JSON rendering from retained records | No persistent local artifact dependency |
| `db` | ORM models, repositories, transactions, migrations | Small connection pool; no long transaction across provider waits |

Dependency direction: routes call application services; the runner calls adapters and the gateway; the gateway calls validation, policies, and registered mock tools; evaluators consume evidence. Mock tools do not call providers. Provider adapters return bounded text/actions and cannot import an execution shortcut.

## Data relationships

- `guest_sessions` owns private `agents` and `test_runs`; the credential hash and expiry are server-side only.
- `agents` has immutable `agent_versions`, recording provider/model, prompt hash, demo profile/behavior version, tools, and policy configuration.
- `scenarios` has immutable `scenario_versions`, separating runtime inputs from oracle configuration and expected behavior.
- `test_runs` references an exact agent version and a snapshot of suite membership/configuration. Suite membership records exact scenario versions, not just a mutable suite name.
- `scenario_results` belongs to a run and scenario version; execution status and nullable pass/evaluation outcome are distinct.
- `trace_events` belongs to a result/run, with a unique ordered sequence per scenario result. Events across concurrent scenarios use timestamps and explicit result IDs rather than assuming a global total order.
- `findings` links evidence event IDs; verify those IDs belong to the referenced result.
- `benchmark_comparisons` references two accessible retained runs.
- `reports` references a retained run and renderer version; source ownership applies at every download.

Shared seeded agents/runs have a null owner and an explicit shared flag set only by server-side seeding. Reject records that are neither owned nor explicitly shared. Session cleanup removes dependent private records while retaining shared reference data.

Use UUIDs, foreign keys, indexes on ownership/status/time, and uniqueness for session/idempotency key and trace sequence. Enforce cross-record ownership at service boundaries as well as direct object reads.

## Contracts and runtime

- Version routes under `/api/v1`; session routes and read-only shared catalog/sample routes are explicitly distinguished from private operations.
- Keep agent response/action schemas separate from database and evaluator schemas. Whitelist serialized fields; do not serialize ORM objects wholesale.
- Maintain immutable snapshots/hashes for scenario suite, tool schemas, policies, agent behavior, prompt, and run settings. Record source revision where available.
- Start one Uvicorn process. Application lifespan starts the consumer and cleanup loop and shuts them down cooperatively. Multi-process deployment requires a new concurrency/recovery design before enabling it.
- Atomically claim jobs; recover orphaned jobs after restart. Keep database transactions short and out of network waits.
- Use polling initially with backoff and pagination. WebSockets and distributed orchestration are unnecessary for the first release.
- Run migrations once before API startup. Failed migrations prevent the process from reporting readiness.

## Frontend behavior

React Router manages pages; TanStack Query manages remote state; forms use React Hook Form and Zod. Tailwind/shadcn components provide accessible UI; use Recharts only for meaningful comparisons.

Separate loading, backend waking, unauthenticated/expired session, queue capacity, empty history, and failed run states. Render model content as text. Apply a restrictive content security policy and avoid arbitrary HTML rendering. Do not expose hidden chain-of-thought. Demo profile controls explain which settings affect scripted behavior.

## Documentation maintenance

Update this file for architecture decisions, [system design](system%20design.md) for runtime flows/boundaries, [requirements](../requirement.md) for acceptance changes, and [roadmap](phasewise_roadmap.md) for phase status. Record actual measurements only in [performance review](performance_review.md), using the method in [benchmark](benchmark.md). Provider configuration and live verification belong in [deployment](deployment.md).
