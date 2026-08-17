# UNWIND — judge card

*If you read one file, read this one. Every number here traces to
`evidence/INDEX.md`, and every row there names the exact command that
reproduces it. Nothing here is projected.*

---

**Project** — UNWIND, Consequence Clearing
**Track** — Google All Things Agentic Hackathon, Fortified Enterprise Fleet

**One line** — *Cache invalidation for decisions: when a fact turns out
false, everything it touched raises its hand, and the system computes what
must now be un-sent, un-paid, or apologised for.*

**The problem** — Premises don't fail because the model reasoned badly. They
fail because **the world changed after the reasoning was correct**. A quote
assumes an 11-day lead time; the lead time moves; nobody goes back to find
the 2,594 decisions built on it.

---

## ⚠ Read this before clicking anything

**The deployed URL runs Card 1 only.** Cards 0 (WARRANT), 2 (CONTROL TOWER)
and 3 (COUNTERSIGN) — including the four-card instrument this file
describes below — are built, tested (369 passing), and committed, but the
Cloud Run service has not been redeployed since they landed. A fresh health
check (`bash scripts/health_check.sh`) confirms the live service still
answers `"stage":"task-5-interface"`, the pre-Card-2 build tag — that is the
honest, current state, not an oversight. **The 10-minute path below tells
you exactly which parts are on the deployed URL and which need a two-command
local run.**

---

## The 10-minute judge path

### Minutes 0–3: the deployed URL (Card 1, live)

1. Open `https://unwind-hgeodtazqq-uc.a.run.app`. Wait for the field to
   render (4,206 points).
2. Type `supplier_K lead time is now 20 days`, press Enter, click Confirm.
   Watch the counter fall from 2,594 to 78 — zero model calls, arithmetic
   only.
3. Press `H` for the honesty panel. The worst extraction class (66.7%) is
   on screen, highlighted, not buried.

### Minutes 3–7: the four-card instrument (Cards 0–3, local — two commands)

```bash
make emulator          # terminal 1
make dev                # terminal 2 — http://127.0.0.1:8000
```

4. Open `http://127.0.0.1:8000`, wait for the field, press `T`.
5. Read Card 0's bars: every one is labelled `SYNTHETIC` in dim mono text —
   this is seeded demo history, not a real earned balance, and the UI says
   so on every bar, not just in a caption.
6. Click **"Overturn a HIGH-risk judgement (BURN)"**. Watch the amber bar
   drop past the oxide risk-class line — a real `BURN` event, wired through
   `tower/gateway.py`'s `FunctionNode`, live. The very next case of that
   class refuses `WARRANT_INSUFFICIENT`, no cache.
7. Click **"Earn the rookie's first delegation"**. A cold-start agent (zero
   warrant, no seeding) mints its first balance live — the bar's label
   flips from `SYNTHETIC` to `EARNED` in amber, because this one is real,
   on this run.

### Minutes 7–10: the honesty apparatus and the necessity-test cut

8. In the instrument's Card 3 panel: the measured Countersign agreement
   rate, **75.6% (31/41 scenarios)**, labelled `SIMULATED` because live
   Gemma was attempted this session and blocked by a real `404` (the
   project lacks Model Garden access to `gemma-3-27b-it`) — see
   `countersign/DESIGN.md` for the full escalation, including a genuine
   authenticated Vertex round-trip.
9. Read the README's "Prior art" section: the object-capability lineage,
   owned rather than hidden. Read "The honesty map": the Veo/Lyria cut, the
   residual Goodhart risk, the SYNTHETIC-seed policy.

---

## One test per moat

| Moat | Command |
| --- | --- |
| 1. Zero-model guarantee | `python -m pytest tests/test_zero_model.py -v` |
| 2. Deterministic refusal, reason codes | `python -m pytest tests/test_tower_gateway.py -v` |
| 3. `78 = 78`, real browser | `make ui-check` |
| 4. Principal separation (arbiter ≠ owner; countersigner ≠ judging side) | `python -m pytest tests/test_principals.py tests/test_countersign_verify.py -k reject -v` |
| 5. Honesty apparatus (worst class published, T2 a non-test) | `cat docs/T2-MEASUREMENT.md && cat docs/COVERAGE.md` |

Full moat-by-moat test list, including the ones this table compresses, is
`evidence/INDEX.md`.

---

## The four numbers to check

| Number | Where | Command |
| --- | --- | --- |
| **78 = 78** | on-screen counter equals the cascade's own computed material count | `make ui-check` |
| **Warrant re-derivation: 4/4 PASS** | every warrant balance bit-equal to a fresh fold of the ledger | `FIRESTORE_EMULATOR_HOST=localhost:8080 python scripts/rederive_warrant.py` |
| **Countersign agreement rate: 75.6% (31/41), SIMULATED** | measured over all 41 eval scenarios, live Gemma reported unreachable | `python scripts/run_countersign_eval.py` |
| **True test count: 369 passed** (with the emulator; 325 passed / 44 skipped without) | the whole suite, not a cherry-picked subset | `python -m pytest -q` |

---

## Where to look

| Question | File |
| --- | --- |
| Every claim ↔ evidence file ↔ reproduction command | `evidence/INDEX.md` |
| The live Gemini run | `docs/LIVE-VERIFICATION.md` |
| What each artifact proves, and does not | `docs/evidence/README.md` |
| Extraction coverage, incl. the worst class | `docs/COVERAGE.md` |
| Card 0's design, and what it does NOT solve (Goodhart, Sybil) | `warrant/DESIGN.md`, `warrant/FAILURE_MODES.md` |
| Card 3's design, and the exact live-Gemma escalation | `countersign/DESIGN.md` |
| Component-by-component justification | `ARCHITECTURE.md` |
| The 4-minute demo, shot by shot | `submission/demo_script.md` |
| The pre-submission checklist | `submission/CHECKLIST.md` |

Run it yourself, no GCP account needed:

```bash
make install && make test && make ui      # http://127.0.0.1:8000, Card 1
make emulator && make dev                 # + the four-card instrument, press T
```

---

## Final verdict, self-assessed

All four architectural cards are built and tested (369 passing), not three
of four still locked. The deployment has not caught up to the code — that
gap is disclosed above rather than papered over with a demo that quietly
runs against localhost while implying Cloud Run. Weakest points, unchanged
in kind from the Card-1-only submission and still true: T2 judgement quality
is unmeasured, the corpus is synthetic and single-author, live Gemma
verification is blocked by a Model Garden access gap this environment could
not clear, and warrant's Goodhart/Sybil risks are named, not solved.

**No self-score is offered.** Scoring is the judges' to do, and inventing a
number against a rubric this submission does not own would be exactly the
kind of unbacked figure the rest of this repository refuses to print. The
honesty here is not modesty — it is the reason the 75.6% and the +18.2 pp
are both worth believing.
