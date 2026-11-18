# AgentShield AI: Performance and Quality Review

Last updated November 18, 2026. The owner-authorized audit fixes and public release verification are recorded first, followed by the historical audit, Phase 10 and earlier evidence.

## Owner-authorized custom authoring and settings — November 18, 2026

The owner requested completion of the three audit items. The punctuation correction is included, FR-03 now has bounded guest-owned authoring and FR-13 has a functional Settings page. The API accepts only registered label_match/guide_completion data, validates before persistence, caps definitions at 16 KiB and tasks at 1,000 UTF-8 bytes, and retains eight scenarios/four immutable revisions per guest. Execution pins the selected revision/hash and intersects mock-tool permissions. Private rubric snapshots stay in `test_runs.custom_oracles`, outside agent input and public API/report projections. Existing curated execution, gateway and scoring semantics remain covered by regression tests. Legacy curated idempotency signatures omit the new empty custom selection field.

Local final backend checks passed Ruff, format, Alembic model/migration consistency and **119 tests in 30.60 seconds**, with no skips, on Python 3.12.10/PostgreSQL 18.6. Frontend formatting, lint, TypeScript, **30 tests in nine files** and production build passed. The API capability status test was updated for the new limits/capability fields while preserving the no-probe/no-secret assertion. A direct-migration connection test verifies that only Neon pooled hostnames are converted for migrations, retaining TLS/credentials and leaving runtime pooling unchanged. No dependency was added.

The local browser created a label scenario and immutable revision 2, then created a guide scenario. It selected the earlier label revision 1 plus guide revision 1. Vulnerable run `ef8a08f6-968a-4a6a-9ac1-76851ec90bd7` completed with 0/2 passes; the hardened candidate (displayed prefix `6b66941d`) completed with 2/2 passes. The browser comparison showed 2/2 jointly evaluated cases, two improvements and +100 percentage points. Settings saved Vulnerable as the tab default and the launcher selected the shared vulnerable profile. Custom authoring, comparison and Settings had no document horizontal overflow at the 390×844 override; the override was reset. These are scripted checks, not model-security claims.

The existing Neon Free project (PostgreSQL 17, 0.25 CU defaults, one of ten branch slots in use before review) was re-read. Isolated branch `migration-review-0008` / `br-round-cherry-aziveynn` exercised the four actual DDL statements compiled from migration 0008. All succeeded in one transaction; seven retained source runs remained, with zero invalid/null private-oracle backfills and zero custom records. This is DDL validation, not an Alembic version-stamped runtime branch; its copied revision record remains 0007. Endpoint `ep-shy-feather-az0hxqpw` was then suspended and observed idle. The retained branch is a review artifact; it is not wired into the application. An initial explicit suspend-interval request was rejected by the Free account before branch creation; retrying with inherited Free settings succeeded. No plan/billing upgrade occurred and no connection credential was retrieved or printed.

Source `2d8b0a8ce18e7a70a35e6a9c47dd702ba8e5728e` passed [all three CI jobs](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/runs/44241232149): backend/PostgreSQL 17 at 05:01:33 UTC, container build at 05:01:44 UTC, and frontend checks/build at 05:02:18 UTC. The existing Render Free service deployed this source as `dep-dbuj37u7bikc73a3vcp0`, live at 05:04:09.204 UTC. Startup migration 0008, database readiness, new custom table writes and existing curated execution passed. Vercel received the same revision's 45 tracked frontend files, reaching READY as `dpl_EomvNY9gfUVQffmE5cmJHLddAkkD` at 05:08:59.205 UTC with the public canonical alias. No hosting environment or paid-plan change was needed.

The hosted API check used normal guest endpoints and synthetic records. Validation, registered-schema restrictions, shared immutability, foreign custom reads/appends and indirect foreign references, old-version retention, idempotency, redacted traces, report ownership and queued/running cancellation passed. Mixed vulnerable run `a26b1fe9-d565-46c5-8c9e-c02bc1296518` included AS-001–AS-010 plus two custom revision-1 cases and passed 5/12 at 12/12 coverage. Mixed hardened run `6daeb3eb-6cd5-4ef2-875c-6f2bec1163d8` included AS-003–AS-012 plus the same custom cases and passed 12/12 at 12/12 coverage. Comparison `d1c0d760-e7e1-4f99-838b-0d62a1213e14` had ten compatible jointly evaluated pairs: five improvements, five unchanged, four unmatched, zero other categories. Every curated ID was exercised across the two manifests; they are not a canonical same-manifest Core v2 benchmark pair. HTML/JSON exports omitted the private marker, private oracle column and credentials, with no HTML script. The verifier revoked its own two temporary guests in cleanup, so those source URLs are intentionally no longer retained. No special production SQL fixture, forced expiry or recovery deploy was used.

Public browser verification created `CS-cdf5f603ef1945ec8a9daa78c5350125` (label revision 1: teal/rust; appended revision 2: violet/gold) and `CS-e52669acca124de899159cc8670c261e` (guide revision 1, internal-note). It selected the older label revision 1 plus guide revision 1 and launched hardened run `b5c82aec-d36c-4d6e-8efd-2ce872be67b0`. The completed run showed 2/2 coverage, 2/2 passes, zero inconclusive cases and the original revision-1 `teal` answer. The JSON control reached “Report download prepared.” This GUI check verifies attachment preparation; the separate API check inspected both response formats and redaction. The tab default saved as Vulnerable, selected the shared vulnerable launcher profile, and survived a full Settings reload; the test then explicitly chose Hardened for the custom run. Live provider status, enforced limits and guest expiry rendered correctly.

At 390×844, Settings, authoring/version history and custom run detail each had document/client width 375/375; desktop run detail measured 1265/1265. Mobile navigation worked and the override was reset. Visually reviewed proof images are [authoring](../docs/screenshots/custom-authoring-live.jpg), [completed custom run and revision-1 evidence](../docs/screenshots/custom-run-live.jpg), and [Settings after reload](../docs/screenshots/settings-live.jpg). Final documentation checks passed 85 relative link targets across thirteen documents, protected-marker exclusion, JPEG signatures for the three new proofs and `git diff --check`. The final evidence update changes only documentation/images; runtime source remains the CI-tested deployed revision. The browser guest keeps only ordinary synthetic records under seven-day expiry; its credential was not read out or committed. The historical saved sample and walkthrough retain their original provenance.

All three audit items and authorized release gates are complete. Optional Gemini remains disabled with no adapter or provider-path evidence. No new cold cycle, latency distribution, throughput/saturation, abrupt-crash test or payment-dashboard inspection was performed. Resource reads confirmed the existing Free Render/Neon configuration; prior owner-confirmed billing restrictions remain in force. The retained isolated review branch remains suspended. No arbitrary checker/code/URL execution or paid dependency was introduced.

## Post-release application audit — November 18, 2026 (historical, before extension)

Requested scope: test the application, identify needed work and fix reproducible defects locally. Baseline repository revision was `1120998f5a8ebac1aeb70a7f6b8b9416b219695a`; at this audit the deployed frontend remained the Phase 10 source upload and the backend/schema were unchanged. No publication or infrastructure change was performed for that audit. Its pending findings below were subsequently closed by the separately authorized extension recorded above.

**Confirmed defect and local correction:** Agents/Scenarios rendered incorrectly decoded punctuation, including `Shared Â· read-only`, version separators and loading ellipses. The issue was observed in the hosted browser, not inferred from source alone. Seven strings in `frontend/src/Registry.tsx` now use proper UTF-8 middle dots and ellipses. A source scan found no remaining instances of the same corruption patterns in `frontend/src`. This presentation-only correction is saved locally and awaits publication. It introduces no dependency, schema, behavior, ownership or scope change.

**Local verification:** backend Ruff check and format passed. After migrating the existing dedicated loopback test database to head `0007`, all **98 backend tests passed in 21.72 seconds**, with no skips, on Python 3.12.10 and local PostgreSQL 18.6. The first connection attempts encountered sandbox TCP denial and a background server that ended with its shell; keeping the test server alive in a foreground session resolved the environment issue. These were environment failures before tests ran. The complete frontend checks passed both before and after the punctuation fix: Prettier, ESLint, TypeScript, **25 tests in seven files**, and production build. After editing, Prettier first requested normalization; formatting was applied and the full check sequence passed. No new test was added solely to mirror a punctuation replacement.

**Hosted verification:** a fresh guest copied the shared hardened profile into an owned profile and launched Core v2. Run `1881c725-3769-4925-ad64-05235b95ece6` completed with 12/12 coverage and 12/12 passes. Shared vulnerable run `9e17d5d8-772e-47e7-89b6-ace17f35be4f` completed with 12/12 coverage and 6/12 passes. Unauthorized execution counts were 0/6 and 0/11, with one and five blocked attempts respectively. The saved comparison showed six improvements, six unchanged and +50 percentage points. Filtering to improved cases produced six scenario rows. HTML and JSON downloads succeeded; local inspection confirmed completed source, full coverage, six improvements, protected-marker redaction and no HTML scripts. [Actual hosted comparison screenshot](../docs/screenshots/application-audit-comparison.jpg) records this check. These are scripted harness observations, not real-model security measurements.

The existing ordinary `python -m scripts.verify_hosted` check passed HTTPS readiness, trusted/untrusted CORS, guest isolation, shared immutability, idempotency, cancellation, inconclusive comparison, report ownership and HTTP 429 with `Retry-After`. It revoked only its own newly created verification guests. Recovery mode was not used; there was no production SQL fixture, forced expiry or redeploy.

At a 390×844 responsive test viewport, mobile navigation, scenario ID search/detail, a third hardened suite and the historical saved sample worked. The mobile suite `05ed7338-0a7c-4759-829d-8c2fe0888405` completed with 12/12 coverage and passes. Document width did not exceed client width on the checked comparison, catalog, run-detail or sample views. A planned browser quota-error observation instead admitted that third run; no GUI 429 claim is made. The independent HTTP verifier did observe 429. The temporary viewport was reset. The browser guest retains its synthetic copy and terminal runs under ordinary seven-day expiry; its credential was neither read out nor saved to artifacts.

**Result and remaining work:** no blocking defect was observed in the tested core scripted flows. The confirmed punctuation correction still needs publication. Original FR-03 custom declarative scenario authoring and FR-13's dedicated settings page remain partial requirements; the audit does not authorize their implementation. Optional Gemini remains disabled with no live adapter. No new latency distribution, cold cycle, throughput/saturation test, abrupt crash, live provider test, billing inspection or CI run was performed. Previously recorded evidence retains its original dates and limits. This audit is not an independent penetration test or proof of complete security.

## Phase 10 portfolio verification — November 18, 2026

Scope is presentation, canonical documentation and acceptance traceability for the current scripted release. Architecture now names actual files and data relationships, including JSONB findings, static sample ownership and absent provider modules. The threat model describes implemented controls, tested scope and residual risks. Methodology distinguishes partial-action aggregates from evaluable scenario/cohort rates and labels the ten-repeat performance protocol unrun. FR-03 custom authoring and FR-13's settings page remain partial, with no implied owner waiver. Optional Gemini remains disabled.

A fresh hosted browser guest launched both Core v2 suites on the unchanged Phase 9 runtime. Hardened run `8445a942-ebad-4b0f-85d9-3f15520805c0` and vulnerable run `d38526f1-c85d-41fa-bb18-a0c31ad927ec` each evaluated 12/12 cases, passing 12/12 and 6/12 respectively. Unauthorized executions were 0/6 and 0/11; blocked attempts were 1 and 5. The hardened run recorded one required confirmation; both had zero invalid requests and zero inconclusive cases. The saved comparison `5190c178-ae53-401a-a386-72921f1e38e4` showed six improvements, six unchanged and +50 percentage points, with twelve jointly evaluable pairs. These are one fresh run per deterministic profile, not real-model observations or a latency experiment.

Browser inspection followed AS-003 to its exact redacted answer, AS-006 to `destination_not_allowed` without execution and AS-011 to a recorded allowed guide result. HTML and JSON comparison downloads completed and report history listed both. Local inspection confirmed completed source, renderer v1, expected structured sections, no original protected marker, no credential fields and no HTML script. The initial API wake/unavailable state and later Connected/Ready were captured, with no new cold-start duration claimed. The temporary guest remains subject to ordinary seven-day expiry; its credential was not exported or committed. No production fixture, redeploy or expiry override was needed.

The portfolio contains fifteen sequential browser captures with UTC timestamps/public URLs, a 120-second captioned edited-capture video without audio, VTT, transcript, reproducible media builder and interview/resume notes. The video is explicitly labelled edited captures, not a continuous recording. Files are under `docs/portfolio/`; the original November 17 saved sample was neither regenerated nor relabelled. FFprobe reported H.264, limited-range yuv420p, 1024×960, 10 fps, 1,200 frames, 120.000 seconds and 918,889 bytes. `ffmpeg -v error -i docs/portfolio/walkthrough.mp4 -f null -` decoded the full file without errors. Representative extracted frames were visually inspected. Caption sizing was corrected to preserve the evidence view, and the final compatibility review converted the JPEG source's full-range color explicitly to limited-range yuv420p.

Local checks on Windows/Python 3.12/Node 24 passed: frontend `format:check`, `lint`, `typecheck`, 25 tests in seven files, and production `build`; final formatting/build passed again after the roadmap highlight edit. The media builder passed Ruff check/format. A read-only validation checked 74 relative link targets across twelve Markdown documents, report structure/redaction, unchanged historical sample date and all fifteen capture paths. `git diff --check` passed. The React skill checklist found no new hooks, effects, fetching, dependencies or accessibility controls in the static status edit.

The first media render failed because FFmpeg on Windows could not locate Fontconfig. The builder now references installed Arial with a generated ignored local font configuration; rendering and full decode passed. An initial Prettier invocation used repository-relative paths from the wrong directory and matched no files; the corrected frontend-directory command passed. Neither tooling issue changed benchmark outcomes.

No backend application code/schema changed. The 98-test local backend result remains the November 17 observation; it was not rerun locally for documentation/status edits. Hosted saturation, new crash/recovery fixtures, repeated latency/throughput measurements, live provider tests and fresh billing inspection were not run. Existing Phase 9 evidence retains its date and limits.

Source `fff55c404b79930823d21830113c8ac6439ff80a` passed [all three Phase 10 CI jobs](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/runs/44233718830), including backend/PostgreSQL checks, frontend checks/build and the backend container build. Vercel `dpl_C42Xhih6hnos7rC3AGF8B4uCDLRY` reached READY at 03:59:47.959 UTC. The canonical public alias served the updated overview and roadmap, the unchanged historical sample and Connected/Ready API/database status with public scripted execution enabled. Gemini remained disabled. The [published roadmap screenshot](../docs/screenshots/phase10-roadmap.jpg) records Phase 10 and the explicit open requirements. The final link check covered 75 relative targets after adding this proof. Phase 10's portfolio gates are complete; original product acceptance remains partial as documented in requirement.md.

## Phase 9 hosted verification — November 17, 2026

The existing Vercel project deployed 40 reviewed frontend source files from commit `6478fc228b60eeb729fab4a47945f043e7a3419e`. Render deployed the same source, and the container entrypoint migrated the existing Neon database to `0007`. Public scripted execution was separately approved. Existing public aliases and exact-origin CORS were retained. Gemini inference remains explicitly disabled.

A clean browser guest launched both complete Core v2 suites. The recorded server execution durations were 3.8 seconds for hardened and 5.1 seconds for vulnerable. Both evaluated 12/12 cases. Hardened passed 12/12 and vulnerable 6/12. The comparison recorded six improvements, six unchanged cases and +50 percentage points. These are two observed hosted runs, with one timing per profile. They provide a small warm-path check against the 10-second target.

The AS-003 finding opened its exact redacted answer. The browser downloaded HTML and JSON comparison reports, and the downloaded files were inspected for structure and redaction. Report history displayed both records. Mobile navigation was exercised at a 390-pixel viewport override, and document width remained within the available viewport. Screenshots are in `docs/screenshots/live-reports.jpg` and `live-sample-mobile.jpg`.

A separate HTTPS verifier confirmed foreign access denial for agent versions, runs, findings, metrics, traces, comparisons and report downloads. Shared metadata edits were denied. Reusing the same idempotency key returned the same run. Cancellation produced a terminal cancelled result with zero evaluable coverage. Comparing it with a completed case stayed inconclusive. Exact canonical-origin CORS was present and an untrusted origin was rejected for run creation.

The owner approved one production orphan/expiry fixture in verification-only data. After the same-revision Render recovery deployment, the staged job was `failed / interrupted`, retained its one `scenario_start` event and remained inconclusive. Downloaded JSON from a completed source was byte-identical after redeployment. Startup cleanup deleted the expired verification guest. The live limiter returned 429 with `Retry-After`, and the surviving verifier guest was revoked. SQL confirmed no remaining fixture, verification profile or queued/running job. Database size was 8,478,720 bytes. An error-level Render app-log query over 15:34–15:55 UTC returned no entries.

Account/resource records confirmed Vercel Hobby, Render Free and Neon Free. Vercel reported no active trial and excess data-cache billing disabled. The owner confirmed free dashboard plans and no chargeable overages. The billing-charges endpoint supplied no cost data. Initial approval-review rejections for public activation and the production data fixture were resolved through explicit owner approvals before retrying.

Final local checks passed all 98 backend tests in 23.64 seconds and all 25 frontend tests. Ruff, frontend formatting, lint, type checks and production build passed. Alembic reported no schema drift. The hosted verifier’s first attempt at an interactive checkpoint encountered stdin EOF and revoked its guest records. The interactive-terminal rerun passed.

Incoming request pairs interrupted initial waiting windows at 15:59:47, 16:11:42 and 16:14:00 UTC. After the verification tab was moved off the app, logs confirmed a quiet interval after 16:14:00. Render logged `application_stopped` at 16:29:00. The first wake request started at 16:30:32.949 UTC and returned valid public health JSON in **32.812 seconds**, with no failed probe attempt. Database readiness was connected by 16:31:06. The saved sample rendered while the API was waking, and manual retry restored the live browser to Connected/Ready. Render recorded startup on a new instance at 16:30:57. This is one measured cold cycle. The waking screenshot is `docs/screenshots/live-cold-sample.jpg`, and the recovered system view is `live-system.jpg`.

Live storage saturation, full shared-queue saturation and abrupt process termination during an active run were not forced. The hosted recovery case used an explicitly staged orphan. Existing PostgreSQL integration tests cover the bounded queue, storage and interruption logic. Custom declarative scenario authoring remains planned.

The final frontend publication, `dpl_5ML77ARTauV6ofQ1bMa1YoRGpuT4`, reached READY at 16:38:20 UTC with source `eb42f0990b406c851e519746bbefcc552eec650b`. Its canonical public alias loaded the Public demo state, Connected/Ready system view and completed Phase 9 roadmap. [All three source CI jobs passed](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/runs/44127697973). This final frontend change updates presentation and release labels. Backend application code remains at the already verified `6478fc2` release.

## Phase 8 report and outage verification — November 17, 2026

The final full PostgreSQL suite passed all 98 tests in 23.27 seconds. Alembic reported no schema drift at `0007`. Report tests verify concurrent duplicate creation (201/200 with one metadata record), foreign guest denial, unsupported formats, capacity, expiry, cascading deletion, missing-source behavior, HTML escaping and cancellation with inconclusive outcomes. A fresh API application regenerated byte-identical JSON from retained database records. No local report artifact was used.

All 25 frontend tests passed. The added export checks verify bearer headers, comparison references, attachment preparation, unavailable-source feedback and sample access without a session. Timer-based tests verify readiness stops after three not-ready responses or after a subsequent network failure. Frontend formatting, lint, TypeScript and the production build passed. Ruff lint and formatting passed.

Chrome launched both full scripted suites, created an owned comparison and downloaded HTML and JSON reports for the vulnerable candidate. The files contained redacted evidence and the comparison. Report history persisted through a complete page reload. After the guest was revoked, API requests were blocked in Chrome and the bundled sample still rendered with no guest credential. The sample’s evidence anchor resolved. A 390-pixel viewport had no document overflow. Final screenshots were visually inspected and are stored in `docs/screenshots/`.

The saved workspace was captured through local HTTP and PostgreSQL at 10:20 UTC on November 17. Its vulnerable run passed 6/12 cases with 12/12 coverage, and the captured vulnerable → hardened comparison recorded six improvements and six unchanged cases. Renderer v1 output replaces UUIDs consistently and redacts the synthetic private marker. The temporary capture guest was revoked.

Earlier browser capture attempts exposed premature screenshot timing and an assertion requiring findings from a run with none. The verification harness was corrected to wait for a new document and use the vulnerable candidate for evidence-link checks. The final focused browser workflow passed. Screenshots show the final rendered pages.

These checks cover the local application and an intentionally blocked API. Hosted exports, real free-host cold starts, public execution and final deployment validation remain Phase 9 work. Optional Gemini inference stays disabled. Custom scenario authoring remains planned.

## Phase 7 disabled-inference verification — November 17, 2026

Phase 7 uses its explicit disabled exit branch. Only the presence of environment and local-file key settings was inspected. No configured Gemini key was found and the owner’s account tier and quotas were not verified. Public Google documentation was checked, with links and the eligibility decision recorded in deployment.md.

All 95 backend tests passed with local PostgreSQL in 22.61 seconds. Tests verify the availability response, secret omission, database-independent status, startup rejection of Gemini/enabled inference despite key presence, and HTTP 422 for a provider override with no run created. The existing full-suite tests still verify both scripted profiles. Ruff lint and formatting passed. Alembic reported no schema drift at `0006`.

All 20 frontend tests passed, including the visible disabled Phase 7 state. Frontend formatting, lint, TypeScript and production build passed. No browser smoke was run for these text/status changes.

The live adapter, provider timeouts, quota handling, structured output and token accounting are unimplemented and untested. No live Gemini smoke, provider usage or model score is claimed. The API capability phase remains 6. This optional decision adds no database migration.

## Phase 6 verification — November 17, 2026

A Chrome guest launched both scripted Core v2 profiles against local FastAPI and PostgreSQL without an inference key. In the vulnerable-baseline and hardened-candidate comparison, 12/12 cases were evaluable in both runs. Six improved and six were unchanged. The pass rate rose from 6/12 to 12/12 (+50 percentage points). Reversing the pair produced six regressions. Chrome reopened the saved comparison after reload, navigated to the AS-001 source evidence and back, and showed no document overflow at 390 CSS pixels.

The backend suite passed all 92 tests with local PostgreSQL. Two simultaneous requests for the same ordered pair returned HTTP 201 and 200 with identical snapshots. Tests also covered both input ownership checks, guest revocation and cascading deletion, quota handling, incompatible settings and fixture revisions, unmatched cases, missing evidence, and undefined rate changes. Alembic reported no schema drift at `0006`. Ruff lint and formatting passed.

The frontend suite passed all 20 tests. Frontend formatting, lint, TypeScript and the production build passed. Hosted comparison, load and latency measurements remain outstanding.

## Phase 5 verification — November 17, 2026

- Real Chrome, Vite, FastAPI and PostgreSQL completed the full vulnerable scripted suite from the launcher. Following AS-003’s finding opened the matching redacted answer and retained the selection after reloading the URL. AS-007 showed a blocked request and AS-011 showed an executed mock read.
- The same guest saw the run in history and cancelled a second run from its detail page. At 390 CSS pixels, document width stayed within the viewport. The test revoked its temporary guest.
- 78 backend tests passed with PostgreSQL. The filtered trace matched the unfiltered scenario events, and a second guest received HTTP 404. The schema stayed at revision `0005` with no Alembic drift.
- 18 frontend tests passed. The new regressions cover disabled execution, selected scenarios, exact approval, retry-key reuse, capacity guidance, event links, hidden-field omission, empty denominators, polling limits, expiry and interruption. Frontend format, lint, type checks and the production build passed. Ruff checks passed.
- These observations cover the local browser workflow. The public deployment is still Phase 0.

## Phase 4 verification — November 17, 2026

Observed through a loopback Uvicorn server and PostgreSQL with `scripts/smoke_suite.py`, the two shared behavior-version-2 profiles, and no inference key.

| Observed metric | Hardened | Vulnerable |
|---|---:|---:|
| Evaluation coverage | 12/12 | 12/12 |
| Scenario pass rate | 12/12 | 6/12 |
| Adversarial objectives achieved | 0/11 | 6/11 |
| Disclosure cases with exposure | 0/2 | 1/2 |
| Required benign objectives completed | 3/3 | 1/3 |
| Unauthorized mock actions executed | 0/6 | 0/11 |
| Evidence-linked findings | 0 | 6 |
| Trace bytes | 7,005 | 9,118 |

All 78 backend tests passed with local PostgreSQL. Database tests repeated both profiles and compared semantic traces and counts. Unit fixtures checked missing evidence, internal and external marker placement, claimed versus observed execution, partial findings, benign completion, and hand-calculated exclusions and empty denominators. Alembic upgraded to `0005` with no detected model drift. Frontend formatting, lint, type checking, 13 tests and the production build passed. These are deterministic fixture results. Real-model resistance and hosted performance were outside this measurement.

## Phase 3 verification — November 17, 2026

- All 66 backend tests passed against local PostgreSQL after upgrading from `0003` to `0004`. Alembic detected no model drift. Ruff checks passed.
- The production-mode API test used a non-loopback client address, an explicit HTTPS origin and two guest credentials. A foreign guest could neither submit with the owner's version nor read or cancel the run. The unconfirmed and disallowed-destination cases produced no mock receipt. A matching owner confirmation produced exactly one receipt.
- Tests covered protected and foreign records, canary text in outgoing mock messages and exports, malformed and oversized arguments, attempts to supply confirmation from the agent, and guest trace redaction. After six allowed reads the next proposal was traced and blocked. Its result remained inconclusive.
- Both no-key profiles completed AS-011 through local Uvicorn and PostgreSQL with seven persisted events each. The smoke client revoked its guest. Frontend formatting, lint, type checking, all 13 tests and the production build passed. [Implementation CI including the container build](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/runs/44005420354).
- Public-mode tests ran locally. The hosted service still runs Phase 0. Scenario scoring and hosted performance measurements belong to later verification.

## Phase 2 verification — November 16, 2026

All 50 backend tests passed against PostgreSQL, including the gateway permission-isolation regression. Ruff lint and formatting passed. Local PostgreSQL upgraded from `0002` to `0003`, and Alembic reported no model drift. Both scripted profiles completed AS-011 through Uvicorn on 127.0.0.1:8012. Each returned seven persisted events covering scenario start, public input, tool request, gateway decision, mock response, answer, and scenario end. The smoke client revoked its own guest afterward. No benchmark score or timing target was measured.

The initial polling test exposed a PostgreSQL deadlock between a status request and a worker update. The fix acquires the guest before the run and uses a parent lock compatible with foreign-key checks. Local tests cover live polling, idempotency conflicts, cross-guest denial, active and queued cancellation, partial evidence across app restart, queued expiry, rate/capacity rejection, timeouts and byte/step budgets. Port 8000 was occupied during the first HTTP check. The successful smoke used the dedicated port above. Frontend formatting, lint, types, 13 tests and the production build passed. Production deployment was outside this local phase.

## Phase 1 verification — November 16, 2026

On a dedicated local PostgreSQL database, Alembic upgraded from empty to `0002`; `alembic check` found no model/schema drift. Ruff lint and formatting passed. `pytest -q -p no:cacheprovider` with TEST_DATABASE_URL passed **35/35**. Checks cover anonymous and foreign reads, cross-parent version lookup, shared immutability, revocation, expiry before cleanup, cascading deletion, byte and row quotas, issuance limits and the catalog allowlist. Frontend formatting, lint, types, build and **13/13** Vitest cases passed. A local browser created a guest and private profile, observed version 1, filtered AS-011 and opened its detail against FastAPI/PostgreSQL. No model calls, benchmark scores, hosted Phase 1 checks or cold-start measurements.

## Phase 0 evidence (historical)

| Area | Observed status |
|---|---|
| Backend | FastAPI foundation implemented; no agent/run/guest mutation endpoints |
| Frontend | Overview, system inspector, roadmap, and not-found routes implemented |
| Local checks | November 16: 31 backend tests passed, 1 database integration case skipped locally; November 10 browser evidence retained |
| PostgreSQL | Live Render-to-Neon readiness returned connected; standalone Neon SELECT 1 also passed |
| Lint/format/types | Ruff, Prettier, ESLint, TypeScript passed |
| Frontend production build | Passed; no security benchmark has been executed |
| Dependency audit | npm audit reported zero vulnerabilities after targeted development-tool override |
| Docker/Compose local execution | Not run; Docker is not installed on this machine |
| GitHub Actions | Deployment-fix CI passed frontend, backend/PostgreSQL, and container jobs; workflow includes the real database integration case |
| Vercel/Render/Neon deployment | Vercel Hobby, Render Free, and Neon Free verified together through the public frontend |
| Security benchmark scores | Not measured; runtime and evaluators begin in later phases |
| Uptime/load/latency benchmark | Not measured; foundation build time is not application latency |

## Phase 0 completion review: November 16, 2026 (Asia/Calcutta)

- Public URL: https://agentshield-ai-tau.vercel.app. An unsigned HTTPS request returned HTTP 200 with the AgentShield application title. No model key, developer credential, or Vercel sign-in was required for the public production alias.
- The owner completed Vercel scope approval. The selected scope's Hobby badge was observed; Render service plan and Neon organization plan were already confirmed Free. No upgrade was requested. Payment-method settings were not inspected.
- Final frontend release: b5abaad3dde25d627aae0efb804e03e9f6c38df4; Vercel deployment dpl_3wys5nTJ9Gywt3fAFXn4kK8fVfck reached READY. Uploaded source contained 23 files, excluding real environment files, dependency folders, and generated build output. Node 24, npm ci, npm run build, and dist output were used.
- Final frontend checks: Prettier, ESLint, TypeScript, all 11 Vitest cases, and production build passed. The local build reported HTML 0.72 kB, CSS 19.25 kB, and JavaScript 427.05 kB; these are artifact sizes, not application latency.
- Render deploy dep-dbtf20jo00dc73d0nqe0 reached live at 12:04:19 UTC on d6561281701f86c160851b7d6c8661f4624a5866. Backend source is unchanged from CI-tested 5b48b86. Error-level app logs from 12:04:19 through 12:06:05 UTC were empty.
- Browser evidence: Overview showed Connected and Ready; /system rendered actual health and database-connected JSON; direct /system and /roadmap visits worked; the final roadmap showed Phase 0 complete and ten later phases Planned. Connection refresh worked. No console errors or warnings were returned in the inspected window.
- Mobile check at a requested 390×844 viewport: navigation opened, selecting System status closed it and showed the actual database response. Document client/scroll widths both measured 375 px. Desktop check at 1440×1000 measured both widths 1425 px; no horizontal overflow. Temporary viewport overrides were reset.
- Final HTTPS health/readiness both returned 200; production /docs and /api/v1/runs returned 404. The canonical frontend origin received the exact allow-origin header; untrusted.example received none. CSP allows the actual API origin; DENY framing and nosniff headers were observed.
- Local proof screenshot: .cache/phase0-live-preview.png (ignored workspace evidence, not a generated private trace). Deployment IDs, configuration, and manual release procedure are recorded in deployment.md.
- Vercel Git linking initially returned 400 because the account's GitHub integration was not installed. The project was created without Git linking and successfully deployed using source uploads. Automatic frontend Git deployment is not configured.
- Final-release attempt dpl_9Hc63GtqSVrUuAveuExpyJHYBk1V failed with NOW_SANDBOX_WORKER_ROOTDIR_NOT_EXIST because an empty source bundle was submitted from a stale REPL binding. The existing public deployment stayed available. A fresh function-local bundle was counted and inspected before the successful retry; this was an upload packaging failure, not a code/build assertion failure.
- Automatic approval review rejected removing project-wide Vercel protection. It was not applied; the canonical production alias works while default protection remains enabled. No bypass was added.
- All Phase 0 exit gates are complete. Feature execution, no-key scenario profiles, isolation, benchmarks, and reports remain for later requested phases. Post-idle cold-start duration, warm API latency, uptime, load capacity, and security scores were not measured.

## Initial hosted backend review: November 16, 2026 (Asia/Calcutta)

Historical state before Vercel authorization and frontend completion; the completion record above supersedes its pending frontend gate.

- Source revision verified by CI and deployed on Render: 5b48b865f45aef02044cc6e567302ff9c2779915.
- [CI run 43858216273](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/runs/43858216273) completed successfully for frontend checks/build, backend tests with PostgreSQL 17, Compose validation, and the backend container build.
- The final frontend-CSP revision a7f5a720b0a898486bede64bd39ffca8042c2b07 also passed [CI run 43859035364](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/runs/43859035364). The live backend remains on 5b48b86; the subsequent revision changes only frontend security-header configuration.
- Local backend command: backend/.venv/Scripts/python.exe -m pytest backend/tests -p no:cacheprovider -o faulthandler_timeout=20. Result: 31 passed and 1 database integration case skipped, in 1.12 seconds. TEST_DATABASE_URL was not configured for this local rerun; do not claim it tested hosted connectivity.
- Ruff lint/format checks passed. Render Docker manifest passed current JSON schema validation using check-jsonschema. Frontend formatting also passed after restricting the CSP to the actual API origin.
- The backend suite now has 32 collected cases, including 15 environment-string regressions. The first deployment's false-string parsing failure is preserved in the deployment record. Explicit false values are accepted; true and unknown values remain rejected.
- A sandboxed pytest run stalled and was interrupted. The same suite passed outside the restricted sandbox; no assertions were removed or skipped to work around the stall.
- Live HTTPS health and readiness both returned 200. Readiness reported database connected. Production /docs and the unimplemented run route returned 404; an unapproved origin received no CORS allow-origin header.
- Corrected Render deploy dep-dbteiqgn74is73bmec5g reached live on the Free plan in Singapore. Its error-level runtime-log query returned no logs in the scanned window.
- Neon project agentshield-ai was created in the confirmed Free organization, in Singapore on PostgreSQL 17 with fixed 0.25 CU limits. An explicit idle-timeout override was rejected, so the successful project retained the Free plan default. No app feature schema or data was created.
- Frontend deployment remains incomplete: Vercel returned 403 for its configured scope and requires the owner's team-access approval. No paid plan or alternative scope was selected.
- Warm API latency, post-idle cold starts, uptime, security benchmark scores, and load capacity were not measured.

## Phase 0 review: November 10, 2026 (Asia/Calcutta)

Scope: application shell, typed settings/API client, process health/database readiness, logging/errors/CORS, dependency locks, local database/container configuration, CI, threat model, and deployment templates. No agent execution, attack logic, data tables, guest credentials, or inference has been implemented.

Environment: Windows x64, Python 3.12.10, Node 24.18.0, npm 11.16.0, uv 0.12.23. Runtime dependencies are recorded in the committed locks. Starlette's current TestClient uses httpx2; installing that client removed the deprecated-httpx warning.

### Actual checks

| Check | Command/procedure | Result |
|---|---|---|
| Python lint | `backend/.venv/Scripts/ruff.exe check --no-cache backend/app backend/tests` | Passed |
| Python formatting | Same Ruff executable with `format --check --no-cache` | 11 files formatted correctly |
| Backend tests | `backend/.venv/Scripts/python.exe -m pytest backend/tests -p no:cacheprovider`, with local `TEST_DATABASE_URL` | 17 passed, no skipped tests, 1.40 seconds in the recorded run |
| Frontend format | `npm --prefix frontend run format:check` | Passed |
| Frontend lint | `npm --prefix frontend run lint` | Passed |
| Frontend types | `npm --prefix frontend run typecheck` | Passed |
| Frontend tests | `npm --prefix frontend test` | 11 passed in 2 files; includes stale-connection regression |
| Frontend build | `npm --prefix frontend run build` | Passed |
| Browser | Real local API through Vite proxy; Overview/System/Roadmap navigation; 1440px and 390px breakpoints | API connected and PostgreSQL ready; no observed horizontal overflow; mobile menu/navigation worked |
| Foundation mode | Backend tests request future feature routes and try enabling execution/inference | Routes absent; unsafe Phase 0 flag configuration rejected |
| Readiness boundaries | Test unavailable/configuration/recovery, real PostgreSQL, generic errors, CORS, and process-only health | Passed |

The optional integration test first skipped when no database was available, then passed after starting a temporary PostgreSQL 18.6 test instance from the published `embedded-postgres@18.6.0-beta.19` package inside the ignored workspace cache. It bound only loopback port 55432 and created no Windows service/user. This was a verification workaround for missing Docker, not a new application dependency or a replacement deployment plan. CI is configured for PostgreSQL 17; its result must be recorded separately.

Vite's native subprocesses require execution outside the restricted sandbox; the tests/build passed there. The ordinary commands remain valid on the developer's normal terminal. A local pytest cache creation issue was avoided with `-p no:cacheprovider`; this does not disable tests. Ruff validation used `--no-cache` for the same reason.

### Dependency finding and resolution

npm initially reported ten moderate findings through one development-tool transitive `minimatch` advisory. A declared override to the patched `^11.0.1` release resolved the audit findings without a forced bulk upgrade. ESLint, type checking, tests, and build were then rerun successfully. Keep the override documented and review it during future dependency updates. An empty audit is not proof of complete dependency security.

### Build artifact observation

The recorded production build emitted a 0.72 kB HTML entry, 21.12 kB CSS (5.81 kB gzip), and 427.06 kB JavaScript (131.78 kB gzip). These are build-reported transfer sizes, not memory, runtime performance, or security measurements. Do not publish a p95 latency/throughput claim from these numbers.

### Gates remaining at the November 10 review

Vercel approval, free-plan checks, public frontend deployment, exact CORS, and the initial browser/API/database smoke were outstanding at that review. They were completed on November 16 as recorded above. The [November 16 CI run](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/runs/43858216273) passed PostgreSQL, Compose, frontend, and container checks. Actual post-idle cold-start timing remains unmeasured; no measured duration is claimed.

## Hosted CI verification record

The [initial CI run](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/runs/42687280344) verified the frontend checks/build and backend container build. The backend job failed before executing tests because `astral-sh/setup-uv@v10` could not be resolved. Direct Git tag inspection found v7 at `94527f2e458b27549849d47d273a16bec83a01e9`; the workflow now pins that verified revision. The correction also removes unused starter assets and ignores interrupted pytest cache folders.

See the [Actions history](https://github.com/Pranjaltyagi76/AgentShield_AI/actions/workflows/ci.yml) for the correction run and its current result. Local backend tests including actual PostgreSQL had already passed independently. A workflow setup failure is not a failed security benchmark and must not be represented as one.

## Initial Phase 0 targets (historical; superseded by phase evidence above)

| Criterion | Target | Actual result |
|---|---|---|
| Prohibited mock execution | Zero executed prohibited actions in enforcement fixtures | Not measured |
| Scripted repeatability | Same canonical configuration yields the same semantic outcome/trace | Not measured |
| Warm scripted suite | At most 10 seconds after readiness, per profile; measure before claiming | Not measured |
| Guest isolation | Explicit cross-session tests pass | Not implemented |
| Inconclusive handling | Missing evidence never becomes a pass | Not implemented |
| Resource limits | Server enforces finite queue/concurrency/step/token/storage bounds | Not implemented |
| Reports | Escaped HTML/JSON regenerate from retained data after restart | Not implemented |

## Ongoing review procedure

For every phase, record exact scope/revision, environment, actual commands/results, evidence, findings/fixes, checks not run, and remaining gates. Keep superseded failures with their context instead of presenting them as historical successes. Measure warm execution and cold start separately using [benchmark.md](benchmark.md). Do not invent coverage, benchmark scores, uptime, or deployment success.

## Future review template

```text
Review date/timezone and phase:
Revision and environment:
Implemented scope:
Exact checks/commands, counts, and results:
Not-run checks and reasons:
Benchmark settings, versions, sample size, warm/cold procedure:
Measured values and evidence (no secrets):
Findings, fixes, and retest:
Remaining gates and next authorized action:
```

Account persistence, distributed workers, vector databases, PDF generation, LangGraph, and LLM judges remain deferred scope decisions.
