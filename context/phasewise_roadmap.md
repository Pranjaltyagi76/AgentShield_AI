# AgentShield AI: Phasewise Roadmap

Last updated: November 10, 2026. Source: Section 16 of [AgentShield_PROJECT.md](../AgentShield_PROJECT.md).

## Current position

Documentation preparation is complete for the initial plan. Application implementation has not started. No phase is complete, no application tests have run, and no deployment has been verified. Repository setup or documentation publication alone does not complete Phase 0.

Implement only the phase explicitly requested by the owner. Later-phase content in this document is a plan, not permission to build every feature now. The optional Phase 7 may be explicitly skipped with a recorded reason while preserving core completion criteria.

| Phase | Scope | Status |
|---|---|---|
| 0 | Foundation and initial free deployment smoke test | Not started |
| 1 | Guest ownership, data model, agent/scenario catalog | Not started |
| 2 | Scripted agents, bounded queue, simulation runtime | Not started |
| 3 | Deterministic policy enforcement | Not started |
| 4 | Full scenario pack, oracles, metrics | Not started |
| 5 | Run UI, traces, evidence | Not started |
| 6 | Compatible benchmark comparisons | Not started |
| 7 | Optional free real-model adapter | Not started; optional |
| 8 | HTML/JSON reports, saved sample, UX polish | Not started |
| 9 | Complete public deployment validation | Not started |
| 10 | Portfolio evidence and walkthrough | Not started |

## Phase 0: Foundation

Create React/Vite/TypeScript frontend and Python/FastAPI backend, typed settings, health/readiness, a frontend API client, local PostgreSQL via Docker Compose, placeholder-only environment examples, Ruff/pytest/frontend quality checks, and standard Linux GitHub Actions CI. Create supporting threat-model documentation. Preserve the chosen modular layout.

Deploy only the frontend shell and health/readiness API on free plans; verify a Neon connection without creating feature tables. Keep mutation and run endpoints unavailable. Record commands, free billing settings, origins, and cold-start behavior. Owner sign-ins/account setup may be needed.

Exit evidence: local frontend/backend start, checks pass, and deployed shell/API/database connectivity is observed. If accounts prevent deployment, mark that gate incomplete and record the blocker; do not silently waive it.

## Phase 1: Core data and guest ownership

Add SQLAlchemy models, Alembic migrations, guest credential issuance/expiry/revocation, ownership resolution, bounded cleanup, and immutable shared-record rules. Seed the 12 versioned scenario definitions. Add agent/version and scenario/catalog APIs and their pages.

Exit evidence: two guest sessions cannot read or change each other's profiles or referenced resources; shared examples remain read-only; expiry denies access; a guest can create an isolated temporary agent profile. Ground truth is excluded from runtime-facing data.

## Phase 2: Sandbox and scripted demo

Implement vulnerable/hardened behavior versions, synthetic context, mock tools, schema validation, persisted traces, queue creation/claiming, idempotency, deadlines, cancellation, heartbeat/interruption recovery, and server-enforced byte/step/token/concurrency/storage/rate limits.

Exit evidence: one scenario executes locally with persisted ordered evidence; queue/limit/restart/cancellation tests pass. Keep public execution disabled until Phase 3 enforcement is verified.

## Phase 3: Policy engine

Implement allowlists, protected-record access rules, destination restrictions, secret-export checks, confirmation gating for simulated actions, maximum calls, and invalid-argument handling. The gateway alone may execute registered mock tools.

Exit evidence: prohibited and unconfirmed actions never execute, even when the agent claims authorization; decisions and attempted actions appear in traces. Enable bounded public demo execution only after ownership/enforcement tests pass.

## Phase 4: Scenario runner and evaluation

Execute the full 12-scenario suite in both scripted profiles. Implement scenario-specific checkers, evidence-linked findings, applicability, coverage, and correctly denominated metrics. Keep execution failures separate from security outcomes. Test authorized internal canary placement, external disclosure, benign completion, and expected budget-stop containment.

Exit evidence: observed execution produces repeatable scores without preset outcome labels. Hand-calculated fixtures match calculations; infrastructure failures and missing evidence are inconclusive. Do not force every vulnerable result to fail or treat all blocked attempts as successful attacks.

## Phase 5: Run and trace UI

Build launch/configuration, bounded status polling, run history/details, trace timeline/tool detail, policy decisions, findings, and evidence links. Handle cancellation, interruption, expired sessions, and capacity errors visibly.

Exit evidence: a guest can launch and understand a benchmark from the UI, distinguishing attempted, blocked, and executed actions without exposing hidden chain-of-thought or protected canaries.

## Phase 6: Benchmark comparison

Add baseline/candidate matching by scenario version and compatible settings, improved/regressed/unchanged outcomes, explicit incompatible/inconclusive cases, metric deltas with counts, and a comparison page.

Exit evidence: known fixtures identify regressions correctly; scripted behavior changes are distinguished from real-model prompt changes; access to both source runs is enforced.

## Phase 7: Optional free LLM adapter

Use the provider interface for a fixed approved Gemini endpoint and a currently free eligible model. Keep inference off by default. Add structured action parsing, strict budgets, timeouts, bounded retries, usage recording, quota/error handling, and an operator kill switch. No paid billing, custom provider endpoints, or paid fallback.

Exit evidence: a free synthetic smoke test succeeds with the same enforced gateway, or mark the phase explicitly skipped/disabled with the reason. A failed provider run retains its own error and never becomes a scripted result. LangGraph and LLM judging remain deferred.

## Phase 8: Reports and polish

Render escaped HTML and JSON on demand from retained records; add report metadata, ownership checks, and retention-dependent regeneration. Add a redacted saved sample bundled with the frontend, backend-waking/retry states, accessibility/responsive polish, and accurate setup/screenshots.

Exit evidence: the complete workflow works without developer intervention while services are available; the static sample is clearly historical and remains inspectable without API access; reports survive backend restart without relying on local files.

## Phase 9: Final deployment validation

Update the Phase 0 free deployment, run migrations, verify HTTPS/CORS/readiness, and test live guest isolation, all demo scenarios, comparisons, reports, cancellation, restart recovery, quota behavior, cleanup, and cold starts. Recheck free-plan eligibility and billing settings. Record actual URLs and dated evidence.

Exit evidence: frontend, backend, database, and no-key workflow are observed working from a clean browser session. Unavailable services and account blockers remain explicitly incomplete. No paid trials, paid fallback, or guaranteed-uptime claims.

## Phase 10: Portfolio readiness

Finalize architecture/threat model/methodology, measured sample report, actual screenshots, walkthrough video, decision records, limitations, and interview notes. Update resume claims only to match implemented, measured behavior.

Exit evidence: a reviewer can understand the repository, reproduce setup, inspect evidence, and try the deployed app without needing private credentials.

## Completion record for every phase

Record start/completion date, changed scope, relevant commit IDs, actual checks/commands and results, evidence/artifact locations, known limitations, and remaining gates. Update [performance_review.md](performance_review.md) and [deployment.md](deployment.md) where applicable. Do not mark all tasks complete because only the local implementation passed.

## Commit and push policy

Use only the owner's Git author and committer identity described in [AGENTS.md](../AGENTS.md). Group related, reviewable work into roughly four to six meaningful commits per substantial push. Do not create empty/artificial commits, backdate work, or rewrite published history to reach a count. A small change may need fewer commits; a phase may need more. Verify the outgoing history and relevant checks before pushing to the owner's repository.
