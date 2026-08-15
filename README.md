# UNWIND

**Cache invalidation for decisions — when a fact turns out false, everything it
touched raises its hand, and the system computes what must now be un-sent,
un-paid, or apologised for.**

Every decision an organisation makes rests on specific claims about the world: a
supplier will ship in 11 days, a tariff rate is 8%, a clause means X. Those
claims expire. When one changes, nothing in the enterprise points backwards from
the claim to the decisions built on it — the dependency edge was never recorded.
So correction propagates socially: someone remembers, sends an email, hopes. The
result is a permanent, invisible population of decisions that are already wrong
and still operating, and the ones that already escaped into the world — sent,
signed, shipped, paid — are the expensive ones. UNWIND records the edge, watches
the claim, and when it dies, walks backwards.

Premises do not fail because the model reasoned badly. They fail because the
world changed after the reasoning was correct.

**Category:** Consequence Clearing · **Track:** Fortified Enterprise Fleet ·
Google "All Things Agentic" Hackathon

**The verified cascade:** move one supplier lead time 11→20 days, and reverse-index
traversal finds **2,594 dependent decisions**. Reducing that to the **78** that need
a human is **pure arithmetic — zero model calls** (1,468 immaterial · 874
closed-out · 174 sent to judgement). `tests/test_zero_model.py` walks the import
graph of every module under `spine/` and fails the build if any of it can reach a
model client.

---

## Quickstart

```bash
git clone https://github.com/akashbichukale111/unwind
cd unwind
make install && make ui      # http://127.0.0.1:8000 — no GCP account needed
```

`UNWIND_VERTEX_DISABLED=1` closes the one door to a model (`lib/vertex.py`); the
full cascade, the whole test suite and the whole UI run with it set, on every CI
push. See [Running it](#running-it) for the complete sequence, including tests
and the credentialed path.

## Architecture

![UNWIND architecture — UI to Cloud Run to spine (zero-model boundary) to court/judgment to Vertex AI to Firestore, with the four-card overlay](assets/architecture.svg)

One request, traced left to right: **UI → FastAPI on Cloud Run → `spine/`**
(T0 traversal + T1 materiality — the zero-model boundary, 2,594 → 78 by pure
arithmetic) **→** the 174 that need judgement cross into **`court/` +
`judgment/`**, the only tier allowed to call **Vertex AI** (Gemini) **→
Firestore** holds state throughout. The vertical stack on the left situates this
deployed system — **CARD 1 · UNWIND CORE (frozen)** — among the three other
cards, which are locked design, not yet built: **CARD 0 · WARRANT**,
**CARD 2 · CONTROL TOWER**, **CARD 3 · COUNTERSIGN**. A judge should be able to
trace one request through this diagram in under 15 seconds.

**Deployed:** <https://unwind-hgeodtazqq-uc.a.run.app> — Cloud Run, `us-central1`,
project `project-895d4ca8-d301-447d-916`. Verified live end to end; see
[Deployment](#deployment) and [`scripts/health_check.sh`](scripts/health_check.sh).

## ADK 2 — the locked construct mapping

This mapping is **locked architecture for the build phase, not a claim that it is
already running.** Stated honestly: `agents/` is currently ~310 lines
(`agents/cascade/`, `agents/smoke/`) with **no `LlmAgent` anywhere in it** — the
cascade graph is `FunctionNode`s and routing, deliberately model-free. The
constructs below land as the four cards are built; an honest "landing next"
beats an implied "already done."

| Locked construct | ADK 2 primitive | Card |
| --- | --- | --- |
| Gateway reason codes | deterministic router branches | CARD 2 · CONTROL TOWER |
| Warrant SPEND-or-refuse | `FunctionNode` | CARD 0 · WARRANT |
| Registry → coordinator selection | dynamic node scheduling | CARD 2 · CONTROL TOWER |
| Countersign (Gemma verifier) | single-turn `AgentTool` | CARD 3 · COUNTERSIGN |
| Case pause/resume | durable `LongRunningFunctionTool` runtime | CARD 2 · CONTROL TOWER |

What *is* built and running today uses ADK 2 already: `agents/cascade/workflow.py`
is a `Workflow` of `FunctionNode`s branching on `ctx.route`, and the repair court
(`court/owners.py`) runs commitment owners as single-turn agent tools fanned out
in parallel under one arbiter. See `ARCHITECTURE.md` § "ADK 2 features" for the
full, currently-true accounting.

## Prior art — what WARRANT is and isn't

WARRANT is object-capability security where the capabilities are earned rather
than granted: a classical capability is granted and delegable; a warrant is
minted only from countersigned, human-validated outcomes, is non-transferable
across principals, decays with idleness, and is scoped per risk class. Nobody
hands it over; nobody can hand it on. Classical object-capability systems (E,
Cap'n Proto's RPC, macaroons) answer "who may invoke this" by tracking
possession of an unforgeable token that can be delegated onward at will; WARRANT
answers a different question — "has this principal actually earned the right to
act again" — by minting authority only from a countersigned, human-validated
outcome, letting it decay with idleness, and refusing it structurally the moment
a delegation would cross a principal boundary. It is a security primitive for
agentic systems specifically: the risk classical capabilities don't model is an
agent that reasons correctly, acts, and is proven wrong by a world that moved —
WARRANT is what runs out before that agent gets to act on stale authority again.

## Honesty map, at a glance

- **Worst extraction class:** `temporal:absolute-duration` at **66.7%** parser-only
  recall (see [Live verification](#live-verification)).
- **The headline delta:** parser+Gemini recall **81.8% → 100.0%, +18.2 pp** — and
  the model's own denominator is **8, not 44**. Stated that way everywhere in
  this repository, always.
- **T2 is a non-test:** the live run attempted 60 nodes and resolved 0 — not a
  model failure, because all 174 queue nodes carry `committed_lead_days = None`
  and the assessor returns UNRESOLVED before the model's answer is consulted.
  See [T2 — attempted, resolved nothing](#t2--attempted-resolved-nothing-and-that-is-a-non-test).
- **The corpus is synthetic and single-author:** artifacts and the extraction
  lexicon were written by the same person. `docs/COVERAGE.md` states this at
  length rather than burying it.
- **Test count, true today:** `make test` → **261 passed, 11 skipped** (272
  collected; the 11 skips need a live Firestore emulator) — regenerated by
  running `pytest -q`, not typed by hand.

---

## ⚠ Status: Task 5 of 5 — the interface, the demo, the submission

**Type a fact that changed. Watch 2,594 decisions light up and 78 survive.
Then read the correction one of them now owes a named customer.**

The whole demo runs with the model switched off. That is not a degraded mode —
the blast radius is a graph traversal and materiality is subtraction, so 90% of
the die-back is arithmetic. Gemini is the second pass, on the part a parser
cannot read.

```bash
make install && make ui      # http://127.0.0.1:8000 — no GCP account needed
```

✅ **Gemini via Vertex AI is verified running.** `make verify-live` executed on
2026-08-13 against project `project-895d4ca8-d301-447d-916`, location `global`,
model `gemini-3.5-flash-lite`: **Vertex call OK, 0 model errors**, and the
headline measurement below. See [Live verification](#live-verification).

⚠ **The T2 judgement tier is still unmeasured**, and the live run is the reason
we now know that precisely rather than vaguely — see the same section. Numbers
elsewhere in this repo that come from `ScriptedT2Model` remain labelled as such.

⚠ **Why this needs ADK 2.** Commitment owners are *single-turn agent tools*, not
sub-agents. A sub-agent takes the floor and does not give it back; the court
needs N owners discovered at runtime, run in parallel, with the arbiter keeping
the gavel to rule. `tests/test_court.py` measures that the pleas genuinely
overlap in wall-clock time rather than trusting the docstring.

### The honesty map

| | Component | Evidence |
| --- | --- | --- |
| **[BUILT]** | Deterministic spine — traversal, T1, four regimes | `make test` → 261 passed, 11 skipped |
| **[BUILT]** | **CLOSED-OUT** as a named regime and reason code | 874 nodes in the demo cascade; `tests/test_regimes.py` |
| **[BUILT]** | **Five-state router** wrapping the authority gate | EXECUTE/ASK_HUMAN/RETRY/DEFER/REFUSE, one vocabulary |
| **[BUILT]** | **DEFER** on a contested premise | `make cascade --claim <contested>` → defer, both sides named |
| **[BUILT]** | Numeric + temporal extractors, relative dates tracked apart | `docs/COVERAGE.md`, recall measured not asserted |
| **[BUILT]** | **Coverage auditor** — may mark unresolved, never safe | `make coverage`; guard + vacuity test |
| **[BUILT]** | Claim reconciler — reversible, logged, low-margin → human | `tests/test_judgment.py` |
| **[BUILT]** | Watchers (1,146 dormant) + drift sentinel | `make sentinel`; sentinel may not retract, tested |
| **[BUILT]** | **Blind re-deriver** — blindness enforced in 3 layers | `tests/test_blindness.py` incl. vacuity fixture |
| **[BUILT]** | **T2 assessor as a separate principal** | refuses to grade its own work, tested |
| **[BUILT]** | Quarantined extraction principal | cannot name an out-of-scope claim, tested |
| **[BUILT]** | Confidence floor scaled by blast radius | tested at both ends |
| **[BUILT]** | Two-source rule above exposure | tested; duplicate ids do not count as two |
| **[BUILT]** | **Confidence gate with echo-back** | rendered before acting, in every state |
| **[BUILT]** | Both adversarial cases refused by reason code | `make adversarial`; enforced in CI |
| **[BUILT]** | 41 eval scenarios across 5 classes | `make eval` → 41 passed, 0 model calls |
| **[BUILT]** | **Repair court** — owners, arbiter, four-turn protocol | `make court`; N owners run in parallel, tested |
| **[BUILT]** | **Arbiter is a third principal** (ruling 1.10) | separation checked over a whole bench, 6 vacuity cases |
| **[BUILT]** | Turn cap + cost ledger + conservative default | no `while` in `court/protocol.py`, asserted by test |
| **[BUILT]** | Dynamic team formation, dissolved on settlement | size is a function of the radius; two radii, two sizes |
| **[BUILT]** | Irreversibility triage, conservative under doubt | max(record, op table); fires on 232 real effects |
| **[BUILT]** | Counterparty cartographer — **no send capability** | AST guard + a fixture that CAN send, so it is not vacuous |
| **[BUILT]** | **Correction obligation** — the product's output | `make obligation`; range + assumptions + named human |
| **[BUILT]** | Approval broker — may request, may not approve | `approve()` raises; only `human::` may sign |
| **[BUILT]** | Load rating — versioned, reversible, contestable | refuses anything carrying agent-trust fields |
| **[BUILT]** | `multi_premise/` — 10 scenarios | radii merge, 0 duplicate obligations, arbiter allocates |
| **[BUILT]** | Golden court transcript | `make golden`; CI fails on drift |
| **[VERIFIED]** | **Gemini via Vertex AI** | live run 2026-08-13: call OK, 0 model errors, **81.8% → 100.0%** recall (+18.2 pp) |
| **[BUILT, NOT VERIFIED]** | T2 judgement (`judgment/assessor.py`) | executes live with 0 exceptions; **0 of 60 resolved** — the sample cannot resolve, see below |
| **[DESIGNED]** | Compensation-path synthesis | Deliberately not built; `synthesise()` raises |
| **[DESIGNED]** | Model Armor on the extraction path | **[UNVERIFIED]** — see below |
| **[DESIGNED]** | Contractual/regulatory/relational extractors | Their claims come from the corpus |
| **[DESIGNED]** | Firestore rules + composite indexes | Written; **never deployed**, no project state changed |
| **[VERIFIED]** | `infra/deploy.sh` → Cloud Run | **Deployed and live** — `make deploy-verify` reports **5/5 PASS** |
| **[BUILT]** | **The field** — 4,206 nodes, canvas | **60 fps measured** (`make ui-check`), depth axis = time |
| **[BUILT]** | **Load-bearing lines** — thickness ∝ dependents | from the reverse index; slack on retraction is a spring |
| **[BUILT]** | **The cull** — 2,594 → 78 on real events | counter asserted equal to the cascade's own count |
| **[BUILT]** | Parse echo + refusal, both on screen | a misparse arrives as a question |
| **[BUILT]** | **The obligation** — dark field → bone paper | renders the real Task 4 object |
| **[BUILT]** | Court, load-rating drop, honesty panel | dissent shown; worst class highlighted |
| **[VERIFIED]** | `make verify-live` — the credentialed runner | **executed**; refuses stubs; wrote `docs/LIVE-VERIFICATION.md` |
| **[DESIGNED]** | `docs/RETRACTION-FEED.md` — the protocol | schema fields exist; no feed published |
| **[FUTURE]** | Video, Devpost entry | — |

## Live verification

**Observed, not projected.** `make verify-live` on an authenticated machine,
2026-08-13. The command refuses to run against a stub and writes nothing on any
failure path, so every figure here came from a real Vertex call.

| | |
| --- | --- |
| Project | `project-895d4ca8-d301-447d-916` |
| Location | `global` |
| Model | `gemini-3.5-flash-lite` (GA) |
| Vertex call | **OK** |
| Model errors | **0** |

### Parser only vs parser + Gemini

| | Recall |
| --- | --- |
| Parser only | **81.8%** (36 / 44) |
| Parser + Gemini | **100.0%** (44 / 44) |
| **Delta** | **+18.2 percentage points** |

| Class | Gold | Parser | + Gemini | Delta |
| --- | ---: | ---: | ---: | ---: |
| `numeric:currency` | 4 | 100.0% | 100.0% | 0.0 |
| `numeric:percentage` | 4 | 100.0% | 100.0% | 0.0 |
| `numeric:quantity` | 8 | 100.0% | 100.0% | 0.0 |
| **`temporal:absolute-duration`** | **24** | **66.7%** | **100.0%** | **+33.3 pp** |
| `temporal:relative-date` | 4 | 100.0% | 100.0% | 0.0 |

**This is the architectural argument, measured.** The parser is deliberately
first because a regex has no instruction-following surface to attack. It is
already perfect on four classes, so Gemini never sees them — their delta is
zero. The model is shown only what the parser could not read, and it closed
exactly that gap.

**How to read the 100%, honestly:** the model's denominator is **8, not 44**.
The parser missed 8 claims; Gemini saw those 8 and returned 8 correct values.
The 100% describes the *combined pipeline over 44 gold claims* — not a claim
that the model extracts perfectly. 44 claims is a small sample from a synthetic
corpus; `docs/COVERAGE.md` sets out what that corpus does and does not
represent.

### T2 — attempted, resolved nothing, and that is a non-test

| Queue | Attempted | Resolved | Unresolved | Exceptions |
| ---: | ---: | ---: | ---: | ---: |
| 174 | 60 | **0** | **60** | 0 |

Not a success, and not a model failure. **All 174 queue nodes have
`committed_lead_days = None`** — verified against the corpus. `assess()` returns
UNRESOLVED whenever the original commitment carries no numeric term, and that
branch runs *before* the model's answer is consulted. The outcome was fixed by
the corpus, not decided by Gemini.

What the run does establish: 60 nodes, 120 model calls, **zero exceptions**. The
orchestration works end to end against live Vertex. Judgement quality remains
unmeasured, and closing it needs a fixture that does not exist yet — see
[Remaining work](#remaining-work).

## Evidence

- **[`docs/LIVE-VERIFICATION.md`](docs/LIVE-VERIFICATION.md)** — the live run in
  full, the method, and what is still unverified. Normally generated by
  `make verify-live`.
- **[`docs/evidence/README.md`](docs/evidence/README.md)** — the evidence index:
  what each artifact proves and what it does not.
- **[`docs/JUDGE.md`](docs/JUDGE.md)** — the one-page judge card. If you read
  one file, read that one.
- **[`docs/T2-MEASUREMENT.md`](docs/T2-MEASUREMENT.md)** — why T2 judgement
  quality is still unmeasured, and the one part of a fair fixture that could not
  be built.
- **[`docs/DEPLOY.md`](docs/DEPLOY.md)** — the deployment sequence, and the four
  defects a line-by-line review found in a script that had never run.
- **[`docs/COVERAGE.md`](docs/COVERAGE.md)** — the extraction confusion matrix,
  regenerated in CI, drift fails the build.
- **`docs/shots/`** — interface screenshots, produced by `make ui-check` rather
  than hand-captured.
- **Terminal screenshot of the live run** — **not in this repository.** It exists
  only as a chat attachment and could not be copied onto the machine that
  authored this commit, so no file was created and none was recreated.
  `docs/LIVE-VERIFICATION.md` is the authoritative evidence for the run; the
  evidence index says where the image goes if it is added later.

### What has actually been run

- `make verify-live` → **executed 2026-08-13** on an authenticated machine.
  Vertex call OK, 0 model errors, recall **81.8% → 100.0%** (+18.2 pp over
  44 gold claims). T2: 60 attempted, 0 resolved, 0 exceptions — see
  [Live verification](#live-verification).
- `make test` → **261 passed, 11 skipped** (272 collected; the 11 skips need a
  live Firestore emulator). `ruff check` and `ruff format --check` clean.
- `make eval` → **41 scenarios passed, 0 failed, 0 model calls.**
  False-retraction rate **0.0**.
- `UNWIND_VERTEX_DISABLED=1 make eval` → identical. Enforced in CI.
- `make ui-check` → drives a real Chromium: **60 fps median at 4,206 nodes**
  (three 2-second samples, all 60), the on-screen cull counter equals the
  cascade's own material count (**78**), no horizontal scroll at 380px, zero
  app-origin console errors.
- `make contrast` → all 42 token pairs recomputed; every text colour ≥ 4.5:1,
  no eighth colour, no gradient, no radius above 4px.
- `make court` → 4 turns, converged, 12 owners seated from 48 eligible,
  **12 obligations raised**, with Vertex disabled.
- `make obligation` → one full correction obligation: a named counterparty, one
  re-issuable email, one unrecoverable payment, exposure **USD 8,925.00** as a
  range with its assumptions, routed to a `human::` signatory.
- `make multi-premise` → two radii merged; **0 duplicate obligations.**
- `make golden` → byte-stable; CI fails on drift.
- `make adversarial` → both attacks refused with `source_outside_claim_scope`
  and a radius of 0. Enforced in CI by reason code.
- `make coverage` → overall extraction recall **81.8%**; worst class
  `temporal:absolute-duration` at **66.7%**.
- `make sentinel` → 1,146 watchers armed, 440 silence signals.
- `make corpus-verify` → byte-identical.

**Run elsewhere, not here:** the Vertex smoke test — reported passing by the
maintainer on their own machine. Recorded as evidence, not reproduced.

**Never run:** any Firestore rules or index deployment, Model Armor,
`npm install` in `web/`.

**Cloud Run deployment is live and verified.** `infra/deploy.sh` provisioned
the runtime service account, the six Pub/Sub topics, and the Cloud Run service
itself; `make deploy-verify` reports **5/5 PASS** (exit 0) against the deployed
URL — see [Deployment](#deployment) below.

### The interface

Seven colours, four typefaces, one canvas. The field is dark and structural; the
obligation is warm paper. The transition between them is the point of the whole
screen.

Contrast is measured rather than eyeballed, and measuring it found a real
tension in the palette: against the field ground, only bone (14.98:1) and amber
(6.21:1) clear 4.5:1 — graphite is 2.34:1 and the rust is 2.40:1. So the rust
and the patina do lines, fills and the paper, where the rust reads at 6.24:1,
and field text is bone at opacities that still measure above the floor.
`make contrast` re-derives this and fails the build.

### Forty distinct arguments across 170 conclusions

The hub radius reaches **170 clause-governed conclusions**, but they rest on
**40 distinct contractual claims**. The court therefore hears forty distinct
arguments, replicated across 170 commitments — and the demo says so. Inflating
the clause set to make the hearing look busier would read as padding; an honest
large number beats a manufactured one. Both figures come from
`corpus/data/stats.json`.

### Numbers

Every number in this repository was produced by a committed script
(`corpus/generate.py` → `corpus/data/stats.json`, or `pytest`). **No latency,
cost, accuracy or benchmark figure is stated anywhere**, because none has been
measured. The three dollar amounts in the corpus (USD 41,800, USD 12,650 and
USD 8,925) are invented parameters of a synthetic scenario, not estimates —
and residual exposure is always reported as a **range with its assumptions**,
with any effect that carries no recorded amount counted separately rather than
priced.

**Every T2 number in this repository came from `ScriptedT2Model`.** That is a
harness measuring itself on the model's side. What it measures honestly is the
orchestration around the model: principal separation, blindness, the turn cap,
and whether an unavailable model yields UNRESOLVED instead of a guess.

---

## Remaining work

Stated as facts about this repository, not as a roadmap.

### Verified by execution
- Gemini via Vertex AI: one real call, **0 model errors**.
- Parser vs parser+Gemini recall: **81.8% → 100.0%**, **+18.2 pp**, 44 gold claims.
- Interface: **60 fps** at 4,206 nodes; cull counter equals the cascade's own count.
- 41 eval scenarios, **0 model calls** on the T0/T1 path, false-retraction rate **0.0**.
- **Cloud Run deployment**: `make deploy-verify URL=...` reports **5/5 PASS**,
  exit 0, against the live service — healthz, same-origin UI, a real cascade
  (radius 2,594 → material 78, counter-integrity confirmed), the adversarial
  refusal (`source_outside_claim_scope`, radius 0), and a real headless-browser
  check (4,206 nodes rendered, on-screen counter 78 = cascade material 78).

### Built, executes live, but the result proves nothing about quality
- **T2 judgement.** 60 nodes, 120 model calls, **0 exceptions** — but **0
  resolved**, because all 174 queue nodes carry `committed_lead_days = None` and
  the assessor declines before the model's answer is used. A fixture was
  designed and **deliberately not built**: mechanical answer-withholding is
  achievable, but the clause text and the scoring key would be written by the
  same author, which makes a judgement benchmark a mirror rather than a
  measurement. Full reasoning in
  [`docs/T2-MEASUREMENT.md`](docs/T2-MEASUREMENT.md).

### Never executed
- **Firestore rules and composite indexes.** Written under `infra/`, never
  deployed; no GCP project state has been changed by this repository.
- **Model Armor.** Never configured, so it has never blocked anything. The
  extraction quarantine is the real defence and does not depend on it.
- **Compensation-path synthesis.** Deliberately `[DESIGNED]`; `synthesise()`
  raises rather than emitting a reverse path that looks executable.
- **The retraction feed.** Schema fields exist and the authority gate is built
  and tested; no feed has been published or consumed.

### Not code
- Demo video, Devpost entry, and the terminal screenshot at
  `docs/evidence/live-vertex-verification.png`.

## The primitive

**The retractable decision** — a decision stored together with the live, typed
premise set it depends on, such that any premise change propagates to it, is
scored for **materiality** and **escapement**, is triaged for **reversibility**,
and is converted into either a silent death, an in-place correction, a
synthesised compensation, or a human-signed correction obligation.

### The four regimes — and only one cell is an alert

|  | **not escaped** | **escaped** |
| --- | --- | --- |
| **immaterial** | dies silently, logged | dies silently, logged |
| **material** | corrected in place | → **correction obligation** |

This split is a **deterministic router**, not a prompt. The core novelty must not
be able to hallucinate.

### The eight-step loop

1. **Extract** — conclusion → typed premises → claims + reverse edges
2. **Fragility** — before acting: which premise, if wrong, is expensive?
3. **Watch** — dormant watcher per live claim; sentinel on silence
4. **Propagate** — claim dies → reverse index walked → blast radius
5. **Score** — materiality × escapement → four regimes
6. **Arbitrate** — commitment owners argue; neutral arbiter rules
7. **Settle** — idempotent / compensable / irreversible
8. **Learn** — load rating of the lying source drops

Task 2 builds **step 4 and the arithmetic half of step 5**. Steps 1–3 and 6–8 are not built.

---

## The corpus

One scenario, built completely: a supplier lead-time premise feeding quotes,
purchase orders, an ad flight and customer promises across six months.
**Synthetic** — see [`corpus/README.md`](corpus/README.md) for the generation
model, the assumptions it rests on, and every measured property.

The headline: **the hub claim `supplier_K.lead_time_days = 11` carries 2,424
transitive dependents. Moving it to 20 leaves 78 that are materially harmed and
still open — 50 of which already escaped. 95.2 % die back on the buffer
arithmetic alone; 96.8 % need no action at all.**

Those percentages are computed from `committed_lead_days` on committed rows, not
chosen. `tests/test_corpus.py` recomputes the die-back from `radius_truth.jsonl`
and asserts the stats file agrees, and the eval recomputes the whole split from
`claims.jsonl` + `conclusions.jsonl` + `reverse_index.jsonl` without ever reading
the marking scheme.

| | Measured | Target in the brief |
| --- | --- | --- |
| Conclusions / claims | 4,004 / 1,083 | ~4,000 / ~1,100 |
| Hub transitive dependents | 2,424 | ~2,000 |
| **Die-back** | **95.165 %** | ≈96 % |
| Live material survivors | 78 | withdrawn as inconsistent |
| — not escaped / escaped | 28 / 50 | ~12 / ~19 |
| **Escaped survivors decided ≥120d before** | **12** | ≥5 |
| Median escape → retraction gap | 63.5 days (max 181) | "months" |
| Max premise-chain depth | 5 | "report actual" |
| UNRESOLVED conclusions | 4 | ≥3 |
| Adversarial artifacts (refused, not processed) | 1 | 1 |

Every divergence is explained, not tuned away, in
`corpus/README.md § Where the measurements differ from the specification`.

---

## Running it

Nothing here needs a Google Cloud account.

```bash
make install                 # uv venv (Python 3.12) + deps
make emulator                # terminal 1: Firestore emulator (needs Java 11+)
make test                    # terminal 2: 256 tests, 11 of which need the emulator
make dev                     # terminal 2: API on http://127.0.0.1:8000/api/healthz
make corpus-verify           # proves the committed corpus is reproducible
make eval                    # runs the hub-retraction scenario, reports real metrics
make eval-vertex-off         # THE GUARANTEE: same run with Vertex disabled
make cascade                 # one cascade: 2,424 dependents -> four regimes
make cascade-forged          # the forged retraction, refused with its reason
make debt                    # standing causal debt, before anything breaks
make web-ui                  # `adk web agents` — tracing UI for the smoke agent
```

`make demo` and `make golden` **exit non-zero and say they are not built.** They
are stubs for Tasks 4 and 5 and will never print a false pass.

### With credentials

```bash
gcloud auth application-default login
export UNWIND_PROJECT_ID=your-project
make smoke                   # one real Vertex call through the smoke agent
./infra/deploy.sh            # [UNVERIFIED] never executed — see below
```

### Model and version verification

| | Value | How it was checked |
| --- | --- | --- |
| ADK | `google-adk==2.6.3` | `adk --version`; installed from PyPI |
| Model (fast) | `gemini-3.5-flash-lite` | GA on Vertex AI; re-verified 2026-08-12 |
| Model (deep) | `gemini-3.6-flash` | GA on Vertex AI since 2026-07-21; re-verified 2026-08-12 |
| Region | `us-central1` | Pinned in `lib/config.py`, never inferred |
| Backend | Vertex AI | `GOOGLE_GENAI_USE_ENTERPRISE=true`, set from config in `lib/vertex.py` |
| Python | 3.12.3 | `pyproject.toml` requires `>=3.12,<3.13` |

Both model strings appear in `lib/config.py` and nowhere else in the repository.
`tests/test_config_singleton.py` greps every tracked file to prove it.

⚠ **`MODEL_DEEP` is not a Pro model, deliberately.** As of 2026-08-12 no Gemini
3.x Pro is generally available on Vertex AI — `gemini-3.1-pro` is *preview*. A
GA-only constraint currently excludes the entire Pro line, so the deep tier is
the strongest GA model instead. Promoting it when 3.1 Pro reaches GA is a
one-line change in `lib/config.py`. **Both strings need re-verifying before
submission.**

**Two things changed since this project was specified**, both reported rather
than silently worked around:

- `GOOGLE_GENAI_USE_VERTEXAI` is **deprecated** in google-adk 2.6.3 /
  google-genai 2.17.0, replaced by `GOOGLE_GENAI_USE_ENTERPRISE`. Setting the old
  flag still works but emits a `DeprecationWarning`, so `lib/vertex.py` sets the
  new one.
- "Gemini 3.5" is not a single flagship. The current family is `gemini-3.1-pro`
  (preview), `gemini-3.6-flash` (GA) and `gemini-3.5-flash-lite` (GA). The two
  GA models are what is pinned.

### Deployment

`infra/deploy.sh` runs `gcloud run deploy --source .` (buildpacks + the root
`Procfile`), so the deployed artifact is the real FastAPI app serving both
`/api/*` and `web/static` from one origin — not the ADK dev UI. It also
provisions the runtime service account (three least-privilege roles, no
Owner/Editor) and the six Pub/Sub topics. Firestore rules and composite
indexes are a separate step via the Firebase CLI — see `docs/DEPLOY.md` §5.

**[VERIFIED] Deployed and live**, verified end to end with `make deploy-verify`:

```
[1/5] healthz OK  stage=task-5-interface        (GET /api/healthz)
[2/5] UI served from the same origin
[3/5] real cascade: radius 2,594 -> material 78, counter integrity OK
[4/5] adversarial refusal OK — source_outside_claim_scope, radius 0
[5/5] real headless-browser check: 4,206 nodes rendered, counter 78 = material 78

DEPLOYMENT VERIFIED — it renders AND it computes.        5/5 PASS, exit 0
```

Service `unwind`, region `us-central1`, project
`project-895d4ca8-d301-447d-916`. The current live revision can always be
confirmed with:

```bash
gcloud run services describe unwind --project project-895d4ca8-d301-447d-916 \
  --region us-central1 --format="value(status.url,status.latestReadyRevisionName)"
```

To redeploy or reverify yourself:

```bash
gcloud auth login && gcloud auth application-default login
export UNWIND_PROJECT_ID=project-895d4ca8-d301-447d-916
./infra/deploy.sh                                  # end to end
make deploy-verify URL=https://unwind-hgeodtazqq-uc.a.run.app
gcloud pubsub topics list --project "$UNWIND_PROJECT_ID"
```

---

## Layout

```
lib/        config · vertex · firestore · pubsub · telemetry · schema
agents/     smoke/   one delete-ready ADK 2 agent
services/   api/     FastAPI + SSE transport
corpus/     generate.py + committed data + measured stats
evals/      harness · metrics · five empty scenario classes · results
web/        Next.js 15 skeleton, no UI
infra/      firestore.rules · indexes.json · deploy.sh · emulator.sh · dev.sh
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for one justifying sentence per
component, and the four Google Cloud services with the reason each is present.
