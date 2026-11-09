# AgentShield AI: Architecture

Status: planned architecture, not implemented. Last reviewed: November 10, 2026.

## Decisions

| Decision | Reason and consequence |
|---|---|
| React + Vite + TypeScript | Static frontend deployment; no Node.js backend |
| Python 3.12+ + FastAPI | Typed HTTP API and a maintainable Python evaluation runtime |
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
