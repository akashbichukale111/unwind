# Evidence index

Every claim in the README, `docs/JUDGE.md` and `submission/` traces to a row
below. Each row names the CLAIM, the FILE that backs it, and the EXACT
command that reproduces it. If a row's command does not reproduce the
number, the number is wrong — file an issue against this index, not the
claim site.

A screenshot in this repository proves what its own caption says and
nothing more. There are no decorative screenshots.

**Generated / last refreshed:** 2026-08-17. Timestamps in filenames are the
actual run time, not an edit time.

---

## 1. Card 1 — UNWIND CORE (the cascade, the cull, the interface)

| Claim | File | Reproduction command |
| --- | --- | --- |
| Hub retraction: 2,594 dependents → 78 material survivors | `corpus/data/stats.json`; recomputed live by `spine/cascade.py` on every request | `make cascade` |
| Zero model calls in the T0/T1 path | `tests/test_zero_model.py` (AST import-graph walk + a full cascade run with Vertex disabled) | `python -m pytest tests/test_zero_model.py -v` |
| Forged retraction refused at radius 0 | same test file, `test_full_cascade_completes_with_vertex_disabled`; also `make cascade-forged` | `make cascade-forged` |
| Extraction recall: parser 81.8% → parser+Gemini 100.0%, +18.2 pp, denominator 8 | `docs/LIVE-VERIFICATION.md`, `docs/evidence/README.md` §1 | `make verify-live` (needs credentials; not re-run in this pass — see §7 below) |
| Worst extraction class 66.7% (`temporal:absolute-duration`) | `docs/COVERAGE.md` | `make coverage` |
| **78 = 78** on-screen counter, real headless browser, 4,206 nodes rendered | `docs/shots/05-split.png` (screenshot); assertion in `scripts/measure_ui.py` | `make ui-check` |
| 60 fps median at 4,206 nodes (idle field) | `scripts/measure_ui.py`'s own fps assertion (median ≥ 55 required) | `make ui-check` |
| 60 fps median at 4,206 nodes, under a **scripted pan** (interaction, not idle) | `evidence/fps/latest.json`, `evidence/fps/fps-probe-2026-08-17T01-46-55-199Z.json` | `cd scripts && npm install && node fps_probe.js` |
| Deployed URL live, serving Card 1 | `evidence/health/health-20260817T020614Z.md` | `bash scripts/health_check.sh` |
| Deployment computes, not a fixture: `make deploy-verify` 5/5 PASS | `docs/DEPLOY.md`; last full run 2026-08-13 | `make deploy-verify URL=https://unwind-hgeodtazqq-uc.a.run.app` |
| 261 tests, Card 1 frozen (subset of the 316 that pass excluding Cards 0/3's own test files, which also includes Card 2's 44) | `pytest` node IDs under `tests/test_spine.py`, `tests/test_court.py`, `tests/test_corpus.py`, `tests/test_judgment*.py`, `tests/test_settle*.py`, etc. — verified: 316 passed with Cards 0/3 test files excluded | `python -m pytest tests/ -q --ignore=tests/test_warrant_ledger.py --ignore=tests/test_warrant_zero_model.py --ignore=tests/test_warrant_separation.py --ignore=tests/test_countersign_verify.py --ignore=tests/test_countersign_boundary.py` |

## 2. Card 0 — WARRANT

| Claim | File | Reproduction command |
| --- | --- | --- |
| Balances are a pure integer fold; rederive bit-equal | `evidence/warrant/rederive-20260817T021008Z.log` — 4/4 PASS | `FIRESTORE_EMULATOR_HOST=localhost:8080 python scripts/rederive_warrant.py` |
| Zero model calls in `warrant/` (stricter than `tower/`'s own boundary — no `google.adk` at all) | `tests/test_warrant_zero_model.py` | `python -m pytest tests/test_warrant_zero_model.py -v` |
| Warrant ledger shares no storage, no code path with `settle/loadrating.py` | `tests/test_warrant_separation.py` | `python -m pytest tests/test_warrant_separation.py -v` |
| MINT impossible without human concurrence + independent countersign | `tests/test_warrant_ledger.py::test_mint_without_records_raises_forger` et al. | `python -m pytest tests/test_warrant_ledger.py -k mint -v` |
| Cold-start agent (zero warrant) refuses `WARRANT_INSUFFICIENT` by construction | `evidence/warrant/moat-tests-20260817T021026Z.log`; `tests/test_tower_gateway.py::test_warrant_check_refuses_cold_start_agent` | `python -m pytest tests/test_warrant_ledger.py::test_spend_or_refuse_cold_start_refuses -v` |
| BURN visible to the VERY NEXT routing decision (no cache, live fold) | `evidence/warrant/moat-tests-20260817T021026Z.log` — `test_burn_causes_immediate_revocation_visible_to_next_routing_decision` | `python -m pytest tests/test_warrant_ledger.py::test_burn_causes_immediate_revocation_visible_to_next_routing_decision -v` |
| Earn-up across N validated cases crosses the delegation threshold | `evidence/warrant/moat-tests-20260817T021026Z.log` | `python -m pytest tests/test_warrant_ledger.py::test_earn_up_across_n_cases_crosses_threshold -v` |
| SYNTHETIC and EARNED events fold through IDENTICAL arithmetic (500 mixed events) | `evidence/warrant/moat-tests-20260817T021026Z.log` | `python -m pytest tests/test_warrant_ledger.py::test_rederive_bit_equality_over_500_mixed_events -v` |
| Live BURN-and-reroute + cold-start earn-up, end to end, terminal | `evidence/warrant/demo-20260817T021008Z.log` | `FIRESTORE_EMULATOR_HOST=localhost:8080 bash scripts/demo_warrant.sh` |
| Live BURN-and-reroute + cold-start earn-up, in the four-card instrument UI | `docs/shots` — *(browser screenshots taken during this build, not re-saved to a tracked path this pass; reproduce live per the command)* | `make emulator` (term 1) · `make dev` (term 2) · open `http://127.0.0.1:8000`, press `T`, click both buttons |
| 37 tests, all passing | `pytest` output | `python -m pytest tests/test_warrant_ledger.py tests/test_warrant_zero_model.py tests/test_warrant_separation.py -v` |

## 3. Card 2 — CONTROL TOWER

| Claim | File | Reproduction command |
| --- | --- | --- |
| Registry drives ADK 2 dynamic composition — flipping one field changes the graph object | `tests/test_tower_registry.py::test_flipping_a_registry_field_changes_the_composed_graph` | `python -m pytest tests/test_tower_registry.py -v` |
| Gateway is a real ADK `Workflow` of `FunctionNode`s, four reason codes in fixed order | `tests/test_tower_gateway.py::test_gateway_workflow_is_a_real_adk_workflow` | `python -m pytest tests/test_tower_gateway.py -v` |
| Decision Memory Bank is append-only, causal (not a vector store) | `tests/test_tower_memory.py::test_what_happened_because_of_walks_a_branching_chain` | `python -m pytest tests/test_tower_memory.py -v` |
| Durable runtime survives a genuine process restart across a simulated one-week gap | `tests/test_tower_runtime.py::test_case_resumes_after_a_simulated_one_week_gap_and_a_process_restart` | `python -m pytest tests/test_tower_runtime.py -v` |
| Cloud Trace export verified live, one root span carrying the whole reasoning chain | `evidence/observability/README.md`, `trace-run-2026-08-15.log`, `trace_view.png`, `captured-spans-2026-08-15.json` | *(needs live GCP credentials; not re-run this pass — see §7)* |
| Firestore rules + indexes deployed and verified live | `evidence/firestore/deploy-2026-08-15.md` | *(needs Firebase CLI + credentials; not re-run this pass)* |
| Model Armor probe: injection payload MATCH_FOUND, benign payload NO_MATCH_FOUND | `evidence/armor/probe-20260815T132536Z.md` | *(needs a live Model Armor template; not re-run this pass)* |
| 44 tests, all passing (32 in `test_tower_*.py` + 12 in `test_principals.py`, the shared principal-separation module Card 2 added) | `pytest` output — verified 32+12=44 | `python -m pytest tests/test_tower_*.py tests/test_principals.py -v` |

## 4. Card 3 — COUNTERSIGN

| Claim | File | Reproduction command |
| --- | --- | --- |
| Countersign is a real single-turn ADK 2 `AgentTool` (not plain code) | `countersign/agent.py:96,110`; `tests/test_countersign_verify.py::test_countersign_agent_is_a_real_single_turn_agent_tool` | `python -m pytest tests/test_countersign_verify.py::test_countersign_agent_is_a_real_single_turn_agent_tool -v` |
| Collusion guard rejects same-family and same-principal countersigns | `tests/test_countersign_verify.py::test_same_family_countersign_rejected`, `::test_same_principal_countersign_rejected` | `python -m pytest tests/test_countersign_verify.py -k rejected -v` |
| DISAGREE freezes minting via CHALLENGE, permanently, for that case | `evidence/warrant/moat-tests-20260817T021026Z.log` — `test_disagree_freezes_minting_with_challenge` | `python -m pytest tests/test_countersign_verify.py::test_disagree_freezes_minting_with_challenge -v` |
| `countersign/` unreachable from `spine/` (both directions) | `tests/test_countersign_boundary.py` | `python -m pytest tests/test_countersign_boundary.py -v` |
| Live Gemma wiring attempted against real Vertex AI — real auth, real API round-trip, real `404` | `countersign/DESIGN.md` §"Live verification, attempted and reported honestly" | *(needs GCP credentials with Model Garden access this project does not have; the exact escalation and error text is recorded in DESIGN.md rather than re-run)* |
| Measured agreement rate over all 41 eval scenarios: 75.6% (31/41), SIMULATED | `evidence/countersign/results.json` | `python scripts/run_countersign_eval.py` |
| 16 tests, all passing | `pytest` output | `python -m pytest tests/test_countersign_verify.py tests/test_countersign_boundary.py -v` |

## 5. Cross-cutting / submission-level

| Claim | File | Reproduction command |
| --- | --- | --- |
| Full suite: 369 passed with the emulator, 325 passed / 44 skipped without | `evidence/tests/full-suite-20260817T021026Z.log` | `python -m pytest -q` (add `FIRESTORE_EMULATOR_HOST=localhost:8080` for the 369 number) |
| Every ADK 2 construct the README claims is present at its cited `file:line` | `evidence/adk/verify-adk-mapping-20260817T021008Z.log` — 10/10 PASS | `bash scripts/verify_adk_mapping.sh` |
| Clean-clone quickstart, verified 2026-08-17 | this pass's own transcript (see `submission/CHECKLIST.md`) | `git clone <repo> /tmp/x && cd /tmp/x && make install && make test` |
| No Gemini/Gemma model string exists outside `lib/config.py` (prose exempt) | `tests/test_config_singleton.py`, `tests/test_countersign_boundary.py` | `python -m pytest tests/test_config_singleton.py tests/test_countersign_boundary.py -v` |
| Frozen dirs (`spine/`, `court/`, `judgment/`, `settle/`) untouched across the whole build | `git diff --stat -- spine/ court/ judgment/ settle/` against `stage-one-floor` | `git diff --stat stage-one-floor -- spine/ court/ judgment/ settle/` |
| Colour system: exactly 7 tokens, no gradients, no radius > 4px, contrast floor respected | `scripts/check_contrast.py`'s own output | `python scripts/check_contrast.py` |
| ruff clean | this pass's own transcript | `ruff check . && ruff format --check .` |

## 6. What is [DESIGNED] / [PROJECTED] — never claimed as run

These do not have a reproduction command in this pass because reproducing
them needs live GCP credentials with more access than this build environment
had (no billing project with Model Garden access to `gemma-3-27b-it`; the
Vertex/Firestore/Trace/Armor evidence above was captured on the
maintainer's own credentialed machine on 2026-08-13/15, not regenerated
here):

- Live Gemini T2 judgement quality — **unmeasured**, `docs/T2-MEASUREMENT.md` explains why a fixture was deliberately not built.
- Live Gemma countersign verdicts — **attempted, blocked by a real 404** (Model Garden access), `countersign/DESIGN.md`.
- Firestore rules/composite indexes deployment, Model Armor probe, Cloud Trace capture — all real, all evidenced above, all from an EARLIER credentialed run, not this pass.
- ~~Redeployment of Cards 0–3~~ — **done 2026-08-17**, see §8 below. (Struck through rather than deleted: this row was accurate when written minutes earlier in the same day, and the honest move is to show the state changed, not to erase that an earlier statement existed.)

## 8. Redeployment of Cards 0–3 to the live Cloud Run URL — 2026-08-17

| Claim | File | Reproduction command |
| --- | --- | --- |
| Cards 0–3 + instrument deployed to `unwind-hgeodtazqq-uc.a.run.app`, revision `unwind-00005-2bl` | `evidence/deploy/deploy-20260817T022816Z.log` | `UNWIND_PROJECT_ID=project-895d4ca8-d301-447d-916 UNWIND_RUN_REGION=us-central1 UNWIND_VERTEX_LOCATION=global bash infra/deploy.sh` |
| Fresh health check post-deploy | `evidence/health/health-20260817T023133Z.md` | `bash scripts/health_check.sh` |
| `make deploy-verify` 5/5 PASS post-deploy, incl. real headless-browser 78=78 | `evidence/deploy/deploy-verify-*.md` (second run, with `UNWIND_CHROME` set) | `UNWIND_CHROME=/opt/pw-browsers/chromium-1234/chrome-linux64/chrome python scripts/deploy_verify.py https://unwind-hgeodtazqq-uc.a.run.app` |
| `/api/instrument` returns `available: true` with real Card 0–3 data, live | raw JSON captured during this pass (not separately saved to a tracked path) | `curl -s https://unwind-hgeodtazqq-uc.a.run.app/api/instrument` |
| `POST /api/instrument/burn` and `/earn` both work live, real Firestore | `evidence/deploy/shots/03-deployed-burn.png` | `curl -s -X POST https://unwind-hgeodtazqq-uc.a.run.app/api/instrument/burn` (and `/earn`) |
| Root cause + fix: missing Firestore composite index (`decision_memory`, `case_id`+`seq`) | `evidence/firestore/deploy-2026-08-17.md`, `infra/indexes.json` | `gcloud firestore indexes composite list --project project-895d4ca8-d301-447d-916 --format=json \| python3 -c "import json,sys; [print(i) for i in json.load(sys.stdin) if any(f['fieldPath']=='case_id' for f in i['fields'])]"` |
| Root cause + fix: `_firestore_available` only checked for a local emulator, never real prod Firestore | `services/api/main.py` (function docstring explains the bug); no test caught it since the local suite always runs against an emulator | code review — `git show <this-pass's-commit> -- services/api/main.py` |
| Frozen dirs still untouched after this fix pass | this pass's own transcript | `git diff --stat stage-one-floor -- spine/ court/ judgment/ settle/` |
| Full suite still 369 passed after the fix | this pass's own transcript | `FIRESTORE_EMULATOR_HOST=localhost:8080 python -m pytest -q` |

## 9. Premium UI repair — instrument as the default landing view — 2026-08-17

| Claim | File | Reproduction command |
| --- | --- | --- |
| Root cause of raw/default-looking controls: `<button>` does not inherit `color` from its ancestors, and `.home-card` never set it explicitly | `evidence/deploy/ui-premium-fix-2026-08-17.md` | computed-style check in a headless browser: `getComputedStyle(document.querySelector('.home-card')).color` against the pre-fix deployed URL |
| Fix: retired the tile-menu `#home` screen; the existing premium `#instrument` overlay (real warrant bars, registry data, agreement rate) is now the default landing view, no key required | `web/static/index.html`, `web/static/style.css`, `web/static/app.js` | `git show ae027ac` |
| Redeployed to the live URL, revision `unwind-00007-2cn` | `evidence/deploy/deploy-20260817T034428Z.log` | `UNWIND_PROJECT_ID=project-895d4ca8-d301-447d-916 UNWIND_RUN_REGION=us-central1 UNWIND_VERTEX_LOCATION=global bash infra/deploy.sh` |
| Fresh health check post-deploy | `evidence/health/health-20260817T034428Z.md` | `bash scripts/health_check.sh` |
| Fresh load shows all four cards, no `T` required; all four click targets, `Esc`/`T`/the-four-cards-link all return to the instrument; BURN/EARN visibly move real balances; zero console errors — verified against the live URL | `evidence/deploy/shots/04-deployed-instrument-premium.png`, `05-deployed-core-from-card1.png`, `06-instrument-mobile.png` | headless Chromium against `https://unwind-hgeodtazqq-uc.a.run.app` (script not separately committed; see `evidence/deploy/ui-premium-fix-2026-08-17.md` for the full check list) |
| Contrast/palette/gradient/radius check still clean | this pass's own transcript | `python scripts/check_contrast.py` |
| Frozen dirs still untouched | this pass's own transcript | `git diff --stat stage-one-floor -- spine/ court/ judgment/ settle/` |
| Full suite still 369 passed, 10/10 ADK mapping checks | this pass's own transcript | `FIRESTORE_EMULATOR_HOST=localhost:8080 python -m pytest -q && bash scripts/verify_adk_mapping.sh` |

## 10. Card click-through fixed — real detail screens for Warrant / Control Tower / Countersign, "CARD N" labels retired — 2026-08-17

| Claim | File | Reproduction command |
| --- | --- | --- |
| Root cause: `.instr-clickable` only routed Card 1 (Unwind Core) to a real screen; Cards 0/2/3 just pulsed a border and went nowhere, and the visible labels still read "CARD 0 — WARRANT" etc. | `git diff` on `web/static/app.js` (former `activate()`) and `web/static/index.html` in this commit | `git show <this-commit> -- web/static/app.js web/static/index.html` |
| Fix: `WARRANT`, `CONTROL TOWER`, `COUNTERSIGN` labels now read as plain product names; each opens its own `.overlay` detail screen (`#warrant-detail`, `#tower-detail`, `#countersign-detail`) reusing the exact same `/api/instrument` payload the home tiles already used — no new backend logic, `card2.agents` was extended to serialize registry fields (`authority_scope`, `data_scope`, `max_budget`, `risk_class_thresholds`) that `tower/schema.py`'s `AgentRegistryEntry` already computed but the API never exposed | `web/static/index.html`, `web/static/app.js`, `web/static/style.css`, `services/api/main.py` | `git show <this-commit>` |
| BURN/EARN stay wired to the real endpoints from both the home hero and the Warrant detail screen; `updateBar`/`applyInstrumentAction` update every matching DOM node (`querySelectorAll`, not `querySelector`) so both surfaces agree | `web/static/app.js` | `git show <this-commit> -- web/static/app.js` |
| 27/27 headless-browser checks pass against the live deployed URL: 4-card labelling, all 4 click-throughs, Esc/T/refresh, live BURN + EARN, Countersign honesty disclosure, zero page errors | `scripts/verify_card_navigation.py`, `evidence/deploy/card-navigation-20260817T102942Z.log` | `UNWIND_CHROME=/opt/pw-browsers/chromium-1234/chrome-linux64/chrome python scripts/verify_card_navigation.py https://unwind-hgeodtazqq-uc.a.run.app` |
| Redeployed to the live URL, revision `unwind-00008-6b8`, 100% traffic | `evidence/deploy/deploy-20260817T102606Z.log` (this pass's `infra/deploy.sh` run) | `UNWIND_PROJECT_ID=project-895d4ca8-d301-447d-916 bash infra/deploy.sh` |
| Fresh health check post-deploy | `evidence/health/health-20260817T102851Z.md` | `bash scripts/health_check.sh https://unwind-hgeodtazqq-uc.a.run.app` |
| `pytest`, ruff, ADK mapping, contrast all still clean after this pass | this pass's own transcript | `python -m pytest -q && ruff check . && bash scripts/verify_adk_mapping.sh && python scripts/check_contrast.py` |
| Known pre-existing gap, not touched by this pass: `scripts/deploy_verify.py` step 5 still assumes the OLD bare-field-with-bar landing screen (from before `ae027ac` made the instrument the default landing view) and times out on `#bar` being hidden; steps 1–4 (the 78=78 computation, zero model calls, refusal path) still pass | `scripts/deploy_verify.py` | `python scripts/deploy_verify.py https://unwind-hgeodtazqq-uc.a.run.app` |
| Frozen dirs untouched | this pass's own transcript | `git diff --stat stage-one-floor -- spine/ court/ judgment/ settle/ tests/` |

## 7. Screenshot inventory (each proves exactly its caption)

| File | What it proves | What it does NOT prove |
| --- | --- | --- |
| `docs/shots/01-field.png` | The field renders with the full node count | Nothing about warrant, tower or countersign — Card 1 only |
| `docs/shots/05-split.png` | The on-screen counter after a cascade | The specific number equals the cascade's own count — that assertion lives in `scripts/measure_ui.py`, not the pixel content |
| `docs/shots/09-honesty.png` | The honesty panel is reachable and renders | The numbers on it are current — cross-check against `docs/COVERAGE.md` |
| `docs/evidence/deploy-preflight-passed.png` | `make deploy-check` passed at capture time | The deploy itself — preflight checks inputs, not a running service |
| `evidence/observability/trace_view.png` | A captured Cloud Trace waterfall existed on 2026-08-15 | That a trace exists FOR THIS SESSION's Card 0/3 work — it is Card 2 evidence only |
| `evidence/deploy/shots/01-deployed-field.png` | The field renders on the DEPLOYED URL (not localhost) — 4,206 nodes, `T` key hint visible in the legend | The cull itself — that's shot 05-split.png / `make ui-check` |
| `evidence/deploy/shots/02-deployed-instrument.png` | All four cards render on the DEPLOYED URL with real data — SYNTHETIC/EARNED labels, real agreement rate, real CHALLENGE mark | Nothing about the BURN animation itself — that's shot 03 |
| `evidence/deploy/shots/03-deployed-burn.png` | A live BURN action against the deployed service, `WARRANT_INSUFFICIENT` refusal rendered with the oxide border | The exact before/after balance at first-ever click — this capture ran after prior test clicks in this same pass already zeroed that bar; see `evidence/firestore/deploy-2026-08-17.md` for the fresh 0→500bp mint that WAS captured on a first call |

---

## 8. Agentic Command OS — the plan-driven rewrite (2026-08-20)

Every row below was produced by a command in this table, on this commit, in
this environment. Where a capability could not be exercised here, the row says
so instead of pointing at something weaker and calling it proof.

| Claim | Code | Test / evidence | Reproduction command |
| --- | --- | --- | --- |
| Different objectives produce different plans (5/5 unique fingerprints) | `fleet/planner.py` | `tests/test_fleet.py::test_different_objectives_create_different_plans` | `pytest tests/test_fleet.py -k different_objectives -v` |
| **Detection is causal**: removing the escalation from the evidence changes the trace | `command_os/mission.py:_phase_contain` | `tests/test_mission_causality.py`; `evidence/mission/causality-*.log` | `make causality` |
| Drift is scored from the evidence's own numbers (147 tool calls, `finance`) | `_phase_contain` | `test_mission_causality.py::test_critical_drift_isolates_the_agent_the_evidence_named` | same |
| A read-only role cannot write, enforced by the **unmodified** Gateway | `fleet/roles.py` + `tower/gateway.py` | `tests/test_fleet.py::test_recon_cannot_write_even_if_asked_to` | `pytest tests/test_fleet.py -k cannot_write -v` |
| A model-authored plan cannot widen scope, invent a tool, or invent an action kind | `fleet/planner.py:validate_plan` | `tests/test_adversarial.py` attacks 1–4 | `make redteam` |
| Uncertainty strictly raises the price of acting | `warrant/economics.py` | `tests/test_warrant_economics.py` (15 tests) | `pytest tests/test_warrant_economics.py -v` |
| Pricing is model-free by import-graph proof | `warrant/economics.py` lives under `warrant/` | `tests/test_warrant_zero_model.py` | `pytest tests/test_warrant_zero_model.py -v` |
| The economy sustains: verified work MINTs, mismatch BURNs | `_phase_verify` | `evidence/mission/economy-*.log` — 4 consecutive missions, 80bp → 520bp | `make mission` ×4 |
| **Anonymous approval is refused (401)**; a service token is refused (403) | `lib/auth.py`, `services/api/security.py` | `tests/test_api_auth.py`, `tests/test_auth.py` (19 tests) | `pytest tests/test_auth.py tests/test_api_auth.py -v` |
| Every mutating route has an auth dependency — checked by walking the route table | `services/api/security.py` | `test_api_auth.py::test_every_mutating_route_requires_a_principal` | same |
| The concurrence record names the **authenticated** caller, never a constant | `_phase_gate` | `test_api_auth.py::test_authenticated_principal_is_the_one_recorded` | same |
| Simulated evidence can never satisfy MINT in production | `lib/simulation.py` clamp | `test_adversarial.py::test_attack_09_...` | `make redteam` |
| No request-path module mutates `os.environ` — asserted by AST walk | structural | `test_adversarial.py::test_attack_10_...` | `make redteam` |
| One real external action: idempotent, reversible, independently verified | `command_os/external.py` | `tests/test_external_action.py` (15 tests); replay asserted by **counting lines in the sandbox file** | `pytest tests/test_external_action.py -v` |
| Replay duplicates no spend, no Hyperion event, no external action | `resume_mission` + idempotency key | `tests/test_command_os_checkpoint.py` | `pytest tests/test_command_os_checkpoint.py -v` |
| The report can never read COMPLETED over a refusal | `_mission_status` | `test_mission_causality.py::test_hostile_objective_does_not_report_healthy` | `make causality` |
| 20-attack red team, all defended, plus one **declared undefended gap** | — | `evidence/redteam/redteam-*.log` — 21 passed | `make redteam` |
| Full suite, emulator up | — | `evidence/tests/full-suite-emulator-*.log` — **586 passed, 1 skipped** | `FIRESTORE_EMULATOR_HOST=localhost:8080 make test` |
| Full suite, no emulator | — | **458 passed, 129 skipped, 0 failed** | `make test` |
| Headless-Chromium click-through: plan, auth refusal, mission, gate, external action | — | `evidence/browser/browser-check-*.json` + `command-os-mission.png` — **20/20** | `python evidence/browser/browser_check.py` |
| **The real ADK Gemma path executes and fails CLOSED** with no credentials | `countersign/verify.py:_run_gemma_async` | `evidence/adk/live-call-attempt-*.log` — real `Runner`, real `Workflow`, `DefaultCredentialsError`, result `available=False, agrees=None` | see that log's header |

### Explicitly NOT evidenced in this pass

| Capability | Status | Why |
| --- | --- | --- |
| Live Gemini planning | `CONFIGURED_NOT_EXERCISED` | No Google Cloud credentials in this environment. The code path is real and the failure mode is proven honest (row above); the success path has not run here. |
| Live Gemma challenge | `CONFIGURED_NOT_EXERCISED` | Same. |
| Veo / Lyria | `DESIGNED` | Not built. No credentials, and generated media would be presentation rather than evidence. |
| GitHub external-action backend | `CONFIGURED_NOT_EXERCISED` | Real adapter, no token. It raises rather than reporting success — `test_external_action.py::test_github_backend_refuses_rather_than_faking_success`. |
| Cloud Run deployment of this commit | **not deployed** | This session has no `gcloud` credentials and its egress proxy blocks `*.run.app`. The last recorded deploy (`unwind-00013-9h7`) predates this rewrite and does **not** contain it. |

---

## 9. Merge into the default branch (2026-08-20)

The Agentic Command OS was merged **in place** into the existing default
branch `claude/unwind-hackathon-foundation-s36wdi` (merge commit `5e19e60`).
Full account: [`evidence/merge/MERGE-VERIFICATION.md`](merge/MERGE-VERIFICATION.md).

| Claim | Source | Command | Result | Environment | Status |
| --- | --- | --- | --- | --- | --- |
| The merge cannot lose default-branch work | git | `git log forensic..default --oneline` | **0 commits** | local | VERIFIED |
| Nothing deleted or renamed | git | `git diff --diff-filter=DR --name-only <default> <forensic>` | **0 / 0** | local | VERIFIED |
| Frozen systems byte-identical | git | `git diff <default> <forensic> -- spine tower singularity court judgment settle corpus` | empty | local | VERIFIED |
| Merged tree == verified tree | git | `git rev-parse HEAD^{tree}` vs forensic | identical (`6a2860ab`) | local | VERIFIED |
| No API route lost | live import | enumerate `app.routes` | 27 → 29 | local | VERIFIED |
| Full suite post-merge | pytest | `FIRESTORE_EMULATOR_HOST=localhost:8080 make test` | **586 passed, 1 skipped** | local + emulator | VERIFIED |
| Red team post-merge | pytest | `make redteam` | **21 passed** | local + emulator | VERIFIED |
| All 7 cards click through | Chromium | `python evidence/browser/verify_all_cards.py` | **26/26** | local + emulator | VERIFIED |
| Anonymous mutation refused | curl | `curl -X POST .../api/command-os/mission` | **401** | local | VERIFIED |
| Gemini planning | `fleet/agents.py` | `evidence/adk/merged-live-attempt-20260820T041232Z.log` | plan labelled `ZERO_MODEL` | no credentials | **CONFIGURED_NOT_EXERCISED** |
| Gemma challenge | `countersign/verify.py` | same log | `available=False, agrees=None` | no credentials | **CONFIGURED_NOT_EXERCISED** |
| Veo mission replay | — | — | — | no credentials | **NOT_BUILT** |
| Lyria mission audio | — | — | — | no credentials | **NOT_BUILT** |
| Cloud Run deploy of this branch | `infra/deploy.sh` | `./infra/deploy.sh` | **not run** — no `gcloud`, proxy blocks `*.run.app` | sandbox | **NOT_DEPLOYED** |
| Live URL serves this branch | — | `curl .../api/healthz` | **HTTP 000** (proxy 403) | sandbox | **UNVERIFIABLE HERE** — last revision `unwind-00013-9h7` predates this rewrite |

---

## 10. Mission Time Machine fix + Mission Media Lab (2026-08-20)

Full root-cause account:
[`evidence/timemachine/TIME-MACHINE-FIX.md`](timemachine/TIME-MACHINE-FIX.md).

| Claim | Source | Command / test | Result | Environment | Status |
| --- | --- | --- | --- | --- | --- |
| Time Machine button opened a blank panel | `web/static/app.js` (before) | reproduced in Chromium | section visible, 402 chars of text, console 401 | local | **ROOT CAUSE CONFIRMED** |
| Cause: protected route fetched without a token | `/api/command-os/missions` | `curl -o /dev/null -w '%{http_code}'` | **401** anonymous, **200** authed | local | VERIFIED |
| Fix: NOT AUTHENTICATED ≠ no missions | `web/static/app.js` | browser walkthrough | four distinct states render | local | VERIFIED |
| Time Machine opens with real history | `command_os/checkpoint.py` | `verify_timemachine_and_media.py` | 5 missions, **12 checkpoints**, 12 arc nodes | local + emulator | VERIFIED |
| ESC returns to Agentic Command OS | `web/static/app.js` | same | `#command-os` visible, `#instrument` not | local | VERIFIED |
| RESUME is genuinely implemented | `command_os/mission.py:resume_mission` | same | labelled LIVE; disabled + explained when final | local | **LIVE** |
| REPLAY from arbitrary checkpoint | — | — | not implemented; UI says so | — | **NOT IMPLEMENTED** |
| Stored XSS in the objective | `web/static/app.js` | mission run with `<img src=q onerror=…>` | payload rendered as text, `window.__XSS__=0`, 0 `<img>` injected | local | **FIXED + TESTED** |
| Media: one brief, three modalities | `media/grounding.py` | `tests/test_media.py` | 17 passed | local | VERIFIED |
| Media cannot enter the authority path | `tests/test_media.py` | import-graph walk over `tower/warrant/hyperion/singularity` | no imports of `media` | local | VERIFIED |
| Grounded brief is inspectable | `GET /api/media/mission/{id}/brief` | `grounded-brief-20260820T092845Z.json` | 12 checkpoints, real arc, real isolated agent | local + emulator | VERIFIED |
| Gemini mission synthesis | `media/adapters.py:synthesize_mission` | `synthesize-attempt-20260820T092845Z.json`, `live-attempt-no-flag-20260820T092845Z.log` | `NOT_CONFIGURED`, no text, no artefact | no credentials | **CONFIGURED_NOT_EXERCISED** |
| Veo mission replay | `media/adapters.py:generate_replay` | `replay-attempt-20260820T092845Z.json`, same log | `NOT_CONFIGURED`, **no video exists** | no credentials | **CONFIGURED_NOT_EXERCISED** |
| Lyria mission signal | `media/adapters.py:generate_signal` | `signal-attempt-20260820T092845Z.json`, same log | `NOT_CONFIGURED`, **no audio exists** | no credentials | **CONFIGURED_NOT_EXERCISED** |
| Model IDs are current, not deprecated | `lib/config.py` | `tests/test_media.py::test_model_ids_are_current_not_deprecated` | `veo-3.1-generate-001` (3.0 shut down 2026-06-30), `lyria-002` GA | local | VERIFIED |
| Seven cards still intact | all | `verify_timemachine_and_media.py` | **33/33 checks** | local + emulator | VERIFIED |
| Full suite after these changes | `pytest` | `FIRESTORE_EMULATOR_HOST=… make test` | **603 passed, 1 skipped** | local + emulator | VERIFIED |
