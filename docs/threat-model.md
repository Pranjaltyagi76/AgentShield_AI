# AgentShield AI: Threat Model

Reviewed November 18, 2026 for the deployed scripted release. This is a source and evidence review, not a penetration-test certification. [Architecture](../context/architecture.md) and [system design](../context/system%20design.md) describe the runtime. [Performance review](../context/performance_review.md) records actual checks.

## Assets, actors and scope

Protect hosting/database secrets, guest credentials/private records, free quotas, immutable versions, oracle ground truth and evidence integrity. Visitors can issue guests, submit bounded profile data, select curated scenarios and inspect owned evidence. Attackers may forge IDs, repeat requests, consume quotas or submit hostile text. Retrieved instructions and agent proposals are untrusted even when claiming authority.

The runtime uses synthetic data and four in-memory mock tools. It accepts no executable scenarios, shell, arbitrary URLs, custom endpoints or real messages/exports. A process/database compromise is not contained by an OS sandbox. Gemini has no network adapter and remains disabled.

## Trust boundaries and controls

| Threat / boundary | Implemented control | Evidence and residual risk |
|---|---|---|
| Secret/credential exposure | Secret settings, generic errors, logs without credential payloads; bearer headers; server stores SHA-256 guest-token digest | `test_system.py`, `test_workspaces.py`; hosted verifier keeps credentials in memory. Same-origin script compromise can steal browser session storage |
| Forged ownership / indirect references | Server-derived guest, immediate expiry checks, parent ownership on versions/runs/evidence/comparisons/reports; shared profiles immutable | Workspace/run/comparison/report tests; hosted two-guest isolation and denied shared edits November 17 |
| Agent bypasses policy / claims approval | Gateway alone creates results; strict schema/allowlist, record/destination/marker checks; exact owner confirmation outside agent context | Policy/run tests; AS-006 hosted and November 18 blocked-destination capture. These controls do not sanitize every natural-language answer |
| Oracle leakage / fabricated score | Explicit public/runtime projections, private evaluator descriptors, ordered evidence validation, immutable snapshots | Evaluation tests and actual twelve-case runs. Finite exact-string oracles have limited semantic coverage |
| Incomplete evidence hides failure | Separate execution/outcome, inconclusive handling, compatibility and cohort denominators | Evaluation/comparison tests, cancellation and approved hosted orphan recovery. No real-model resilience evidence |
| Text injection in UI/report | React text rendering, CSP, redaction, HTML escaping, attachment/sandbox headers, no report scripts | Report/frontend tests and observed downloads. No claim of complete XSS/supply-chain protection |
| Cross-origin misuse | Exact CORS origins plus independent authorization; production docs disabled | System tests; trusted/untrusted HTTPS checks. CORS does not stop direct HTTP clients |
| Resource exhaustion | Payload/evidence/step/time caps, process-local rate windows, persistent guest/queue quotas, database admission ceiling | Local queue/storage guards and hosted 429 with Retry-After. Windows reset on restart; a proxy peer cap may be shared |
| Sleep/restart/data loss | PostgreSQL persistence, short transactions, orphan recovery, source-backed regeneration, static sample | Approved November 17 recovery/expiry test and idle wake. Free services may suspend; no distributed-worker/uptime claim |
| Cost escalation | Existing free resources; no paid fallback; explicit public activation; provider locked to demo | Free-plan evidence and owner billing confirmation November 17. Future eligibility must be rechecked |
| Deployment/dependency compromise | Locked npm/uv installs, read-only CI permissions, reviewed source upload, explicit intended-file staging | PostgreSQL tests and container CI. No independent security audit claimed |

Test filenames live in `backend/tests/`; frontend tests live beside components. See the review log for local versus hosted scope.

## Enforced default bounds

These are code/specification defaults, not measured traffic capacity.

| Layer | Bound |
|---|---|
| Guest admission | 8 per peer and 60 globally per 600 seconds; 128 retained guests |
| Guest data | 8 profiles/guest; 4 immutable versions/profile; 7-day expiry |
| Write bodies | 256 KiB for run POST/PATCH paths; 64 KiB otherwise; 16 KiB UTF-8 prompt |
| Run admission | 5 per owner and peer, 50 globally per 600 seconds; 1 queued and 1 active/guest; 10 queued and 2 active globally |
| Execution | 12 scenarios, 10 steps/scenario; gateway denies further calls after 6 calls |
| Time | Queue 300 seconds, run 180 seconds, scenario 60 seconds; stale heartbeat recovery after 5 seconds |
| Evidence/text | Event 16 KiB; trace 1 MiB/run; input 4,000 bytes, output 512 bytes, total scripted budget 20,000 bytes |
| Derived records | 64 comparisons and 64 reports/guest, subject to retention and database ceiling |
| Database | Conservative admission ceiling at 500 MiB total database size, configurable downward; small bounded pool/timeouts |
| Cleanup | Every 300 seconds while active; at most 16 expired guests/transaction, skip locked; also at startup |

Rate windows are process-local. Queue, ownership and retained caps are database-backed. Byte budgets are not measured provider tokens. Expiry denies access immediately even while physical cleanup waits for a sleeping process. Storage admission is conservative, not a forecast of the next write or a guarantee against concurrent overshoot.

## Attack-to-evidence example

AS-006 revision 2 makes the vulnerable script propose a synthetic message to a prohibited destination. The trace records `destination_not_allowed` with no mock result. A hardened proposal to `mock-inbox` needs exact owner confirmation. Both profiles can pass enforcement while differing in attempted behavior. Separately, AS-003 can fail on final-answer disclosure despite zero unauthorized tool executions. The server evaluates original evidence; presentation redacts the private marker.

## Remaining risks and unverified behavior

- Anonymous access can consume free quotas. No distributed rate store, live saturation experiment or production-scale capacity claim exists.
- Lost browser credentials have no recovery. Same-origin script compromise can steal temporary access; durable identity/MFA is absent.
- Exact-marker checks miss some encodings/paraphrases. Twelve curated cases cannot establish general security or model rankings.
- Custom scenario authoring and a dedicated settings page remain open original requirements. Current controls are profile forms, status views and operator configuration.
- Provider parsing, tokens, retries/quota handling and eligible free Gemini access are unimplemented/unverified.
- The approved orphan fixture verified recovery with partial evidence; it did not emulate every abrupt mid-action failure. Queue/storage saturation was tested locally only.
- Hosting/database operators remain trusted. No permanent backup, multi-region recovery, third-party audit or untrusted-code execution is claimed.
