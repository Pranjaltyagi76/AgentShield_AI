# AgentShield AI

AI agent security testing, controlled attack simulation, and reliability benchmarking.

**Status: planning and documentation. The application has not been implemented or deployed yet.** No test coverage, benchmark score, latency, or live demo is claimed at this stage.

AgentShield will let developers run synthetic adversarial scenarios, inspect attempted and executed tool actions, enforce deterministic permissions, compare compatible agent versions, and export evidence-backed reports. The required demo will work without an AI API key.

## Planned capabilities

- Twelve versioned security/benign scenarios with deterministic checkers.
- Vulnerable and hardened scripted demo profiles using the real execution/evaluation pipeline.
- Independent tool-policy enforcement and redacted evidence traces.
- Temporary isolated guest workspaces and read-only shared examples.
- Benchmark comparisons, regression detection, and HTML/JSON exports.
- Optional free-tier real-model testing, separate from scripted demo results.

All data and tool actions are synthetic. This is an application-controlled simulation harness; it does not execute untrusted code or test arbitrary external systems. Scripted demo scores demonstrate the harness, not measured real-LLM security. Passing a finite test suite does not prove complete security.

## Planned stack and free deployment

| Layer | Choice |
|---|---|
| Frontend | React, Vite, TypeScript, Tailwind, shadcn/ui |
| Backend | Python 3.12+, FastAPI, Pydantic |
| Persistence | PostgreSQL, SQLAlchemy 2, Alembic |
| Execution | One backend process, bounded database-backed queue, registered mock tools |
| Public hosting | Vercel Hobby frontend, Render Free backend, Neon Free database |
| Optional inference | Eligible Gemini free-tier model; disabled by default |
| Checks | pytest, Ruff, TypeScript, ESLint, build checks, GitHub Actions |

The budget requirement is no mandatory paid APIs or hosting through deployment, no trial-credit dependency, and no paid fallback. Free services have quotas, cold starts, and possible suspension. See the [deployment runbook](context/deployment.md) for dated provider references and validation requirements. Use provider subdomains; no purchased domain is needed.

## Documentation map

| Document | Purpose |
|---|---|
| [AgentShield_PROJECT.md](AgentShield_PROJECT.md) | Full specification and product constraints |
| [requirement.md](requirement.md) | Acceptance requirements and release scope |
| [context/system design.md](context/system%20design.md) | Runtime flows, trust boundaries, ownership, limits, and failure handling |
| [context/architecture.md](context/architecture.md) | Technology decisions, modules, data relationships, and planned layout |
| [context/phasewise_roadmap.md](context/phasewise_roadmap.md) | Phase tasks, completion gates, and actual progress |
| [context/deployment.md](context/deployment.md) | Free hosting setup, configuration, validation, and observed deployment record |
| [context/performance_review.md](context/performance_review.md) | Actual quality/performance evidence and unresolved review points |
| [context/benchmark.md](context/benchmark.md) | Scenario oracles, metric denominators, comparisons, and measurement method |
| [AGENTS.md](AGENTS.md) | Persistent development instructions and commit identity/publication preferences |

## Development status and setup

The current files describe the intended system. Frontend/backend source, dependency manifests, Docker Compose, environment examples, and CI will be created in Phase 0. Runnable installation/start commands will be added after those files exist and have been tested. There is no live application URL yet.

Next implementation milestone: Phase 0 foundation and an initial shell/API/database deployment smoke test. Implement one explicitly requested phase at a time. Later milestones add guest ownership, runtime, policies, scenario evaluation, UI, comparisons, reports, final deployment validation, and portfolio evidence.

## Repository and ownership

Owner: **Pranjal Tyagi**. Repository: [Pranjaltyagi76/AgentShield_AI](https://github.com/Pranjaltyagi76/AgentShield_AI).

Commits must use the owner's verified configured author and committer identity and contain no bot co-author attribution. Prefer four to six coherent commits per substantial push; preserve truthful history and do not split trivial edits merely to inflate the count. Keep secrets and local environments out of version control. See [AGENTS.md](AGENTS.md) for the working rules.
