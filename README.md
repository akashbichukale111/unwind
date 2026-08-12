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

---

## ⚠ Status: Task 2 of 5 — the deterministic spine

**The cascade runs end to end with Vertex switched off.** A retraction is gated
for authority, the blast radius is traversed structurally, every dependent is
scored arithmetically, and the result is split into the four regimes — **2,424
dependents in, 50 correction obligations out, zero model calls.**

Still not built: extraction, watchers, T2 judgement, the five-state decision
router, the repair court, obligations, compensation, and any UI.

### The honesty map

| | Component | Evidence |
| --- | --- | --- |
| **[BUILT]** | Repo skeleton, `pyproject`, Makefile, CI | `make test` → 121 passed |
| **[BUILT]** | `lib/schema.py` — typed models for all 9 collections | `tests/test_schema.py` |
| **[BUILT]** | `lib/config.py` — the only two model strings, pinned region | `tests/test_config_singleton.py` greps the tree |
| **[BUILT]** | `lib/pubsub.py` — 6 topics, local shim | `tests/test_pubsub.py` |
| **[BUILT]** | `lib/idempotency.py` — **Firestore-backed** seen-set | `tests/test_cascade_firestore.py` survives a new client |
| **[BUILT]** | `lib/firestore.py` — typed accessors + `cascades/` collection | `tests/test_cascade_firestore.py` |
| **[BUILT]** | `lib/telemetry.py` — OTel spans carrying `unwind.tier` | `make cascade --trace` |
| **[BUILT]** | `lib/vertex.py` — single model door, Vertex backend pinned | `tests/test_zero_model.py` |
| **[BUILT]** | **Authority gate** — deterministic, refusal is a recorded event | `make cascade-forged` → `source_outside_claim_scope`, radius 0 |
| **[BUILT]** | **T0 traversal** — transitive closure, cycle detection | recall 1.0 / precision 1.0 over 2,424 nodes |
| **[BUILT]** | **T1 arithmetic materiality** — no model, `pending_judgment` for the rest | materiality accuracy 1.0 |
| **[BUILT]** | **Escapement lookup** — fails safe to ESCAPED | `tests/test_spine.py` |
| **[BUILT]** | **Four-regime router** — a rule, exhaustively tested | `tests/test_regimes.py`, all 8 cells |
| **[BUILT]** | **Temporal Truth propagation** — prior value stays readable | `tests/test_spine.py` |
| **[BUILT]** | **Impact cartographer + cascade budgeter** | policy tiers LOW→CRITICAL, LOW path complete |
| **[BUILT]** | **Causal debt scorer** — attributable to named premises | `make debt`, `tests/test_debt.py` |
| **[BUILT]** | ADK 2 `Workflow` of `FunctionNode`s, route-driven | `agents/cascade/workflow.py`, no `LlmAgent` in the graph |
| **[BUILT]** | The corpus — 4,004 conclusions, 1,083 claims | `corpus/data/stats.json`, `make corpus-verify` |
| **[BUILT]** | `evals/` — 9 metrics, 1 scenario, committed results | `make eval` → 1 passed, 0 model calls |
| **[DESIGNED]** | Firestore rules + composite indexes | Written, **never deployed** |
| **[DESIGNED]** | `infra/deploy.sh` → Cloud Run | Written, **never run** |
| **[FUTURE]** | Extraction, watchers, falsification parser | Task 3 |
| **[FUTURE]** | T2 materiality, five-state decision router | Task 3 |
| **[FUTURE]** | Repair court, obligations, compensation synthesis | Task 4 |
| **[FUTURE]** | Load rating, the operator UI, the demo | Task 5 |

### What has actually been run

Run in this environment, output observed:

- `make test` → **121 passed** (110 in-process, 11 against a live Firestore
  emulator). `ruff check` and `ruff format --check` clean over 53 files.
- `make eval` → **1 scenario passed, 0 model calls.**
- `UNWIND_VERTEX_DISABLED=1 make eval` → same result. The cascade does not need
  Vertex, and CI enforces that on every push.
- `make cascade` → 2,424 dependents, four regimes, `model_calls: 0`.
- `make cascade-forged` → refused, `source_outside_claim_scope`, radius 0.
- `make debt` → total attributed across 15,739 named contributions.
- `make corpus-verify` → *"corpus is deterministic: regenerated manifest is
  byte-identical"*.
- ADK workflow through `InMemoryRunner` with Vertex disabled → completed,
  `policy_tier: CRITICAL`, `tier_reached: T1`.

**Never run:** any Vertex AI call, any Cloud Run deploy, any real Pub/Sub topic,
any Firestore rules or index deployment, `npm install` in `web/`. There were no
GCP credentials in the build environment. **There is no deployed URL.**

### Numbers

Every number in this repository was produced by a committed script
(`corpus/generate.py` → `corpus/data/stats.json`, or `pytest`). **No latency,
cost, accuracy or benchmark figure is stated anywhere**, because none has been
measured. The two dollar amounts in the corpus (USD 41,800 and USD 12,650) are
invented parameters of a synthetic scenario, not estimates.

---

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
make test                    # terminal 2: 121 tests, 11 of which need the emulator
make dev                     # terminal 2: API on http://127.0.0.1:8000/healthz
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

`infra/deploy.sh` wraps `adk deploy cloud_run` and additionally creates the six
Pub/Sub topics, the composite indexes and the rules — the things `adk deploy`
does not own. Flag names were verified against `adk deploy cloud_run --help` on
2.6.3.

**[UNVERIFIED] It has never been executed.** No credentials existed in the build
environment. To verify it yourself:

```bash
gcloud auth login && gcloud auth application-default login
export UNWIND_PROJECT_ID=your-project
./infra/deploy.sh                                  # end to end
gcloud pubsub topics list --project "$UNWIND_PROJECT_ID"
gcloud firestore indexes composite list --project "$UNWIND_PROJECT_ID"
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
