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
- Redeployment of Cards 0–3 and the four-card instrument to the live Cloud Run URL — **not done this pass**; the deployed URL still serves Card 1 only (`evidence/health/health-20260817T020614Z.md` shows `"stage":"task-5-interface"`).

## 7. Screenshot inventory (each proves exactly its caption)

| File | What it proves | What it does NOT prove |
| --- | --- | --- |
| `docs/shots/01-field.png` | The field renders with the full node count | Nothing about warrant, tower or countersign — Card 1 only |
| `docs/shots/05-split.png` | The on-screen counter after a cascade | The specific number equals the cascade's own count — that assertion lives in `scripts/measure_ui.py`, not the pixel content |
| `docs/shots/09-honesty.png` | The honesty panel is reachable and renders | The numbers on it are current — cross-check against `docs/COVERAGE.md` |
| `docs/evidence/deploy-preflight-passed.png` | `make deploy-check` passed at capture time | The deploy itself — preflight checks inputs, not a running service |
| `evidence/observability/trace_view.png` | A captured Cloud Trace waterfall existed on 2026-08-15 | That a trace exists FOR THIS SESSION's Card 0/3 work — it is Card 2 evidence only |
