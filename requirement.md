# AgentShield AI: Requirements

Status: acceptance baseline; Phase 0 local foundation implemented, initial hosted gate pending. Last updated: November 10, 2026.

The full product specification is [AgentShield_PROJECT.md](AgentShield_PROJECT.md). This file is its concise acceptance checklist. Runtime decisions are in [context/system design.md](context/system%20design.md); implementation status is in [context/phasewise_roadmap.md](context/phasewise_roadmap.md). Changes to scope must update these references together.

## Product objective

Build a publicly deployed, low-traffic portfolio platform that runs synthetic agent-security scenarios, independently enforces tool permissions, records evidence, evaluates explicit unsafe objectives, compares compatible versions, and exports HTML/JSON reports. All required development and deployment services must operate on ongoing free plans.

## Functional requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| FR-01 | Issue temporary isolated guest sessions with hashed server-side credentials | Separate sessions cannot access each other's private records; expired/revoked credentials are rejected |
| FR-02 | Create agent profiles and immutable versions | Provider/model, prompt hash, tool/policy settings, and demo behavior version are recorded |
| FR-03 | Browse 12 curated versioned scenarios and validate bounded custom declarative scenarios | Catalog/filter/detail works; only registered tools/checkers are accepted; no executable input |
| FR-04 | Provide vulnerable/hardened scripted profiles without an API key | Both execute the actual runtime and produce evidence-derived results, not preset scores |
| FR-05 | Run individual/selected/full suites through a persisted bounded queue | Ownership, version snapshot, idempotency, concurrency, and capacity behavior are tested |
| FR-06 | Enforce validated tool permissions outside agent output | Unauthorized, invalid, or unconfirmed actions never execute |
| FR-07 | Capture ordered inputs, outputs, tool attempts, decisions, execution, and errors | Evidence distinguishes requested, blocked, and executed actions; no hidden chain-of-thought |
| FR-08 | Compute deterministic applicable scenario outcomes and metrics | Hand-calculated fixtures match; denominators/exclusions/coverage are visible |
| FR-09 | Produce evidence-linked findings | Every finding cites relevant trace events; suggestions do not assert unsupported causality |
| FR-10 | Compare compatible baseline/candidate runs | Regressions/improvements are correct; incompatible and inconclusive pairs are explicit |
| FR-11 | Generate escaped HTML and JSON downloads from retained records | Authorized export works after backend restart; no persistent local artifact dependency |
| FR-12 | Support cancellation, interruption recovery, expiry, and cleanup | Partial evidence is preserved; unfinished scenarios remain inconclusive; no silent replay |
| FR-13 | Show overview, agents, scenarios, launcher, runs/details, comparison, reports, settings | Responsive UI with useful loading/error/empty/expired/capacity states |
| FR-14 | Bundle a clearly labelled redacted saved sample report | Static sample remains inspectable when API is unavailable and is never presented as a live run |
| FR-15 | Optionally test one approved real model only when free access is available | Fixed adapter, bounded calls, explicit errors and mode labels; demo remains independent |

## Security and privacy requirements

| ID | Requirement |
|---|---|
| SEC-01 | Synthetic data and simulated actions only; no real messages, payments, exports to external systems, or account actions |
| SEC-02 | No arbitrary code, shell, plugins, URL fetching, tool implementations, or provider base URLs from users |
| SEC-03 | Agent-visible inputs exclude evaluator-only expected labels, oracle configuration, and ground truth |
| SEC-04 | Server-derived ownership applies to every resource and indirect reference; shared examples are immutable to guests |
| SEC-05 | Session credentials/provider keys never appear in URLs, logs, exports, committed files, or frontend environment variables |
| SEC-06 | Escape model/user text in reports and UI; redact protected synthetic data in presentation while preserving server-side evaluation |
| SEC-07 | Independent policy gateway is the only mock execution route; model output cannot grant permissions or confirmation |
| SEC-08 | CORS allows explicit frontend/development origins; authorization remains mandatory regardless of origin |
| SEC-09 | Default guest expiry is seven days from creation; access ends immediately and bounded cleanup removes dependencies |

## Reliability, capacity, and cost requirements

| ID | Requirement |
|---|---|
| NFR-01 | React/Vite/TypeScript frontend; Python/FastAPI backend; PostgreSQL; a modular monolith with one backend process |
| NFR-02 | No mandatory paid API/hosting/domain, trial-credit dependency, automatic upgrade, or paid fallback |
| NFR-03 | Free quotas cause visible unavailability, not unexpected paid usage; optional inference starts disabled |
| NFR-04 | Enforce finite server-side payload/step/token/time/trace/queue/concurrency/storage limits and session/IP/global rate controls |
| NFR-05 | Initial bounds include 12 scenarios, 10 steps/scenario, 1 active run/session, 2 globally, and 10 queued globally; Section 7 of the specification defines all defaults |
| NFR-06 | Failed/cancelled/incomplete execution cannot silently count as a pass; metrics include raw counts and coverage |
| NFR-07 | Backend sleep/restarts are expected; no guaranteed uptime or uninterrupted execution claims |
| NFR-08 | `/api/v1/health` and `/api/v1/ready` report process/database readiness without invoking inference |
| NFR-09 | Use a pooled TLS database connection, bounded pagination/polling, migrations, and short transactions |
| NFR-10 | Relevant tests, lint, type checks, and builds pass before declaring phase completion; unrun checks are stated explicitly |

The warm scripted-suite target is at most 10 seconds after readiness, to be measured before publication. It is not an achieved performance figure or an uptime promise.

## Evaluation requirements

Use the definitions in [context/benchmark.md](context/benchmark.md). Count secret disclosure only when a canary crosses the scenario's unauthorized boundary; intended placement in authorized internal context is not a leak. Separate attempted violations, blocked attempts, and executed violations. Exclude inconclusive results from pass/fail denominators while displaying their counts and coverage. Empty denominators are `N/A`.

Benign completion is scored independently so blanket refusal cannot look successful. Demo scores represent scripted harness behavior; prompt-only edits do not affect scripted behavior. Optional provider results remain distinct, including their failures and variability.

## Deployment and completion

Use Vercel Hobby, Render Free, and Neon Free subject to current eligibility and owner account setup. Verify the shell/API/database connection in Phase 0, then the entire public flow in Phase 9. Follow [context/deployment.md](context/deployment.md) and record real URLs/evidence only after observation.

Completion requires all mandatory feature/security gates, both scripted profiles and all 12 scenarios, correct evidence/metrics/comparison, HTML/JSON exports, verified guest isolation and bounds, tests/builds, documented public deployment, saved-sample outage UX, architecture/threat model, and portfolio walkthrough. Optional inference may remain disabled with a documented reason.

## Deferred work

Durable accounts and email flows, PDF reports, LangGraph, LLM judging, distributed workers, unrestricted external agent endpoints, commercial uptime, hosted local models, and paid infrastructure are outside the first release.

## Development and publication preferences

Implement only the requested phase. Maintain context and actual evidence as work progresses. Use the owner's author/committer identity for every new commit, without bot/co-author attribution. Prefer four to six meaningful commits per substantial push and never manufacture empty history. Follow [AGENTS.md](AGENTS.md) before committing or publishing.
