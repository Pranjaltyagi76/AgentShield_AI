# AgentShield AI: Interview and Resume Notes

Owner: Pranjal Tyagi. Reviewed November 18, 2026. Describe the shipped scripted harness accurately. These are suggested resume/interview statements; no external resume has been changed.

## Resume bullets supported by evidence

- Built and deployed a React/TypeScript, FastAPI and PostgreSQL security evaluation harness with twelve versioned synthetic scenarios, independent mock-tool policy enforcement and event-linked findings.
- Implemented temporary guest ownership, immutable configurations, a PostgreSQL-backed bounded queue, cancellation and interruption recovery, with coverage-aware deterministic evaluation and compatible-run comparisons.
- Delivered authenticated HTML/JSON reports regenerated from retained database records, plus a redacted historical workspace usable during backend outages on a free Vercel/Render/Neon deployment.
- Added guest-owned custom scenario authoring with two registered declarative rubrics, immutable revisions and pinned evaluation, plus a Settings page for tab-local demo preferences and live capability/limit visibility.

Optional measured detail: “In the scripted Core v2 comparison, hardened behavior passed 12/12 cases versus 6/12 for vulnerable behavior, at 12/12 evaluation coverage each.” State that these are deterministic profiles, not model performance. The November 18 [walkthrough](walkthrough.md) records this observation.

## Claim-to-evidence map

| Claim | Inspect / reproduce |
|---|---|
| Twelve pinned synthetic fixtures | `backend/app/suite.py`; Core v2 membership; public Scenarios page; evaluation tests |
| Independent enforcement | `backend/app/policy.py`; `backend/tests/test_policy.py`; AS-006 blocked request in walkthrough |
| Evidence-derived outcomes | `backend/app/evaluation.py`; evaluation fixtures; AS-003 redacted answer and linked finding |
| Guest isolation / immutable shared data | `backend/app/api/workspaces.py`; workspace/run/report/comparison tests; November 17 hosted verifier record |
| Durable bounded execution | `backend/app/run_queue.py`; PostgreSQL integration tests; approved orphan/redeploy observation |
| Honest comparison | `backend/app/comparison.py`; compatibility/missing-evidence fixtures; six improved/six unchanged observed pair |
| Reports without backend disk | `backend/app/reporting.py`, `api/reports.py`; export tests; byte-identical JSON after same-revision redeploy |
| Free deployment and outage UX | [Deployment record](../../context/deployment.md); one real 32.812-second idle wake; static sample during wake |
| Quality checks | Dated commands, counts and CI links in [performance review](../../context/performance_review.md) |
| Custom authoring and Settings | `backend/app/custom_scenarios.py`, `frontend/src/CustomScenarios.tsx`, `frontend/src/Settings.tsx`; 119 backend/30 frontend tests; November 18 hosted extension evidence and screenshots in the current review |

## A concise project explanation

“I built AgentShield to make agent-tool security decisions inspectable. A visitor launches versioned synthetic scenarios in a temporary workspace. A deterministic script proposes actions, an independent gateway authorizes mock execution, and the evaluator scores recorded evidence with explicit applicability and coverage. The browser links failures to individual events and compares compatible runs. I chose a single Python process with a PostgreSQL queue so the portfolio works on ongoing free services.”

“The demo intentionally uses scripted behavior. It tests the harness and enforcement paths. It does not establish how a real model behaves under prompt injection. Free Gemini eligibility was unavailable, so the optional adapter stays explicitly disabled.”

## Questions to prepare for

**Why can the vulnerable profile pass an attack case?** The gateway can block a prohibited proposal, so an enforcement oracle passes even when the script attempted the wrong action. Attempted violations, blocked requests and actual executions have different meanings and denominators.

**How does zero unauthorized execution coexist with six failures?** Some oracles inspect final answers and benign task completion. A disclosure or instruction-override answer can fail without any prohibited tool executing. Show AS-003 and its redacted evidence.

**How do you prevent a blanket-refusal agent from winning?** Benign and mixed cases require a correct permitted lookup and final answer. Containment alone does not satisfy those rubrics.

**What makes results reproducible?** Exact immutable profile/scenario revisions, behavior/oracle/policy versions, tool-schema hash, budgets and source metadata. Ignore generated IDs/timestamps when comparing semantic traces. Prompt-only edits do not change the script.

**Why PostgreSQL rather than a separate broker?** It provides durable admission and short transactional claims within one free service. One process is a deliberate limit; multiple processes need coordinated leases and different recovery semantics. Free host sleep can interrupt work.

**What happens after cancellation or restart?** The worker checks between steps. Orphaned active work becomes failed/interrupted with retained evidence; unfinished cases remain inconclusive. Calls are not silently replayed. Only queued eligible work may resume.

**What are the weakest parts?** Exact finite oracles, anonymous quota abuse, process-local rate windows and temporary bearer storage. No arbitrary code executes. No independent security audit or generalized model ranking exists.

**What did the recovery test actually prove?** An approved staged orphan with one event survived a same-revision deploy as interrupted; retained report JSON regenerated identically and the deliberately expired guest was cleaned up. It was not a live abrupt mid-action crash experiment.

**Why not add LangGraph, Redis or an LLM judge?** They are unnecessary for this deterministic single-process release and add operational or inference dependencies. Deterministic evidence remains the authority for these fixtures.

## Open scope and statements to avoid

The later owner-authorized extension implements FR-03 bounded custom authoring and FR-13 Settings. Explain the two registered schemas, immutable owned revisions, separate oracle snapshots and actual evidence-based execution. Settings saves a tab default and displays operator-managed provider/limit status. Hosted release evidence is tracked in the deployment/review records. Phase 7's optional disabled exit does not mean a live adapter exists. See the [acceptance review](../../requirement.md).

Avoid “production-ready,” “prevents all prompt injection,” “100% secure,” “tested GPT/Gemini,” “improved real-model security by 50%,” “sub-ten-second guaranteed,” “p95,” “unlimited free hosting,” “multi-tenant enterprise authentication,” or “OS sandbox.” Do not describe proposed repetition/throughput experiments as measurements. Describe the original requirement gaps before claiming all product requirements are complete.
