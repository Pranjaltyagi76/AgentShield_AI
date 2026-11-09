# AgentShield AI: Working Instructions

## Read before development

Read `AgentShield_PROJECT.md`, `requirement.md`, and the relevant files in `context/`. Start with `context/phasewise_roadmap.md` for actual progress. The specification is the product baseline; context documents explain decisions and record evidence. If these disagree, resolve the mismatch against the owner's latest instructions and update the affected documents together.

Implement only the phase explicitly requested by the owner. A roadmap is not authorization to build every phase. Documentation preparation and Git setup do not imply Phase 0 is complete. Never invent measured results, successful checks, deployment URLs, or completed gates.

## Required constraints

- React + Vite + TypeScript frontend; Python/FastAPI backend; PostgreSQL. No Streamlit or Node.js backend.
- Ongoing free services only through deployment; no paid fallback, automatic upgrade, trial-credit dependency, or purchased-domain requirement.
- Keep both scripted demo profiles usable without an API key. Actual trace evidence and deterministic oracles produce scores; never hardcode outcomes or relabel a failed provider run as a demo success.
- Synthetic data and mock actions only. No arbitrary code, shell, URL fetching, custom provider/tool endpoints, or real external actions from scenarios.
- Policy enforcement is outside the agent and is the only route to mock execution. Keep evaluator-only ground truth out of agent context.
- Enforce guest ownership, expiry, shared-record immutability, rate/concurrency/storage limits, cancellation, and interruption handling before public execution.
- Keep secrets/session credentials out of Git, logs, URLs, reports, and frontend environment variables. Do not expose hidden chain-of-thought.
- Run relevant meaningful checks for implemented behavior and report exactly what passed, failed, or was not run.

## Maintain context

- Update `context/phasewise_roadmap.md` when phase status changes; include remaining gates honestly.
- Update `context/architecture.md` and `context/system design.md` for design changes.
- Record actual test/performance evidence in `context/performance_review.md`; keep methodology in `context/benchmark.md`.
- Record deployment configuration and observed results in `context/deployment.md`. Do not claim deployment complete without observing frontend, API, database, and no-key workflow.
- Keep `readme.md`, `requirement.md`, and the full specification consistent with final scope. Do not create duplicate canonical architecture/deployment documents under `docs/`.

## Git identity and publication

The owner explicitly requires new commits to be attributed only to **Pranjal Tyagi**, not Codex or any bot. Existing user Git configuration at initial setup identifies `Pranjal Tyagi` with `pranjaltyagi200275@gmail.com`.

- Set repository-local `user.name` and `user.email` to that owner identity; do not change global settings.
- Verify both author and committer identity before committing, including environment overrides and commit hooks/templates. Do not add bot `Co-authored-by`, `Signed-off-by`, or generated-author trailers.
- Verify outgoing commit author/committer fields and messages before every push. Do not claim control over unrelated existing contributors or the owner's GitHub email-association settings.
- Prefer four to six meaningful, reviewable commits for each substantial work batch before pushing. Group by purpose; no empty commits, fake changes, backdating, or artificial history inflation. Small changes may need fewer commits.
- Target repository: `https://github.com/Pranjaltyagi76/AgentShield_AI.git`. Inspect remote state before publishing. Preserve remote work; no force push or history rewriting unless explicitly requested.
- Stage explicit intended files, review staged changes, and run applicable checks. Do not publish secrets, machine-specific credential configuration, dependency folders, local databases, or generated private traces.
- Push work when requested or already authorized by the owner. Do not infer ongoing permission to publish unrelated future work from a prior push.

## Current scope

At initial documentation creation, application implementation has not started. Use the roadmap and actual working tree for later status rather than treating this statement as permanent.
