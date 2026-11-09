# AgentShield AI: Initial Threat Model

Status: Phase 0 foundation. November 10, 2026. The later agent runtime is a planned application simulation, not an OS sandbox.

## Assets and entry points

Assets include environment secrets/database credentials, service availability/free quotas, future guest credentials/private records, versioned test definitions, evaluator-only ground truth, and evidence integrity.

Phase 0 entry points are the static frontend, the process-only health endpoint, database readiness, development-only OpenAPI/docs, dependency installation, CI, and deployment configuration. No guest, agent, scenario, run, tool, or inference endpoints exist yet.

## Threats and controls

| Threat | Phase 0 control and verification | Later required work |
|---|---|---|
| Exposed database credentials | SecretStr settings, hidden validation inputs, generic readiness failures, no exception text in operational logs; tests inspect responses | Review provider adapters, traces, reports, and history before publishing |
| Untrusted origin requests | Explicit CORS origins; GET-only cross-origin methods; no wildcard; CORS tests | Real guest authorization before private features; CORS alone is not access control |
| Misleading operational status | Process health separate from actual PostgreSQL readiness; unavailable state is 503 | Evidence completeness, honest coverage, no fake benchmark outcomes |
| Public feature activation before enforcement | Phase 0 settings reject true execution/inference flags; feature routes absent | Ownership, policy gateway, budgets, and runtime tests before activation |
| Dependency/supply-chain issues | Committed npm/uv locks, locked installs, tracked dependency override, CI read-only permissions | Review updates; do not treat an audit with no findings as proof of security |
| Browser content injection | React text rendering; no arbitrary HTML; production CSP/security headers | Redact/escape future model/tool/report content and protect guest bearer credentials |
| Database resource exhaustion | Small pool, connection and statement timeouts; readiness only executes a constant probe | Public endpoint rate limits, bounded queue, guest/IP/global limits, retention |
| Sleep/restart/data loss | No local persistence assumptions; health/readiness tolerate absent DB | Durable queue state, interruption handling, on-demand retained-data reports |
| Cost escalation | Free-only manifests, inference disabled, no paid disk/worker/database provisioned | Owner verifies actual account billing and quotas during deployment |

The SQL probe uses the minimum query needed to establish connectivity. Feature schema readiness and migrations begin in Phase 1. Readiness requests are not a production load-test interface; provider quotas and public-endpoint abuse remain operational risks until additional controls are implemented.

## Trust boundaries for later phases

The browser cannot choose ownership. Agent output cannot authorize tools. Retrieved documents and tool results are untrusted data. Oracle labels remain outside agent context. Custom scenarios may select approved declarative schemas, never executable code or arbitrary URLs. Optional provider calls use a fixed endpoint with synthetic context; mock tools have no network actions.

## Remaining verification

Real provider account eligibility, billing configuration, live TLS/CORS, deployed database connectivity, container execution, and cold-start timing require actual environments. Do not infer these from source configuration. Record observed outcomes in the context deployment/performance documents.
