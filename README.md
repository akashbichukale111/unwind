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

## ⚠ Status: Task 1 of 5 — scaffolding and corpus only

**No part of the product loop is built.** There is no extraction, no watcher, no
cascade, no scoring, no court, no obligation, and no UI. What exists is the
skeleton those will be built into, plus a corpus whose properties are measured
rather than asserted.

### The honesty map

| | Component | Evidence |
| --- | --- | --- |
| **[BUILT]** | Repo skeleton, `pyproject`, Makefile, CI | `make test` → 41 passed |
| **[BUILT]** | `lib/schema.py` — typed models for all 7 collections | `tests/test_schema.py` |
| **[BUILT]** | `lib/config.py` — sole model string, pinned region | `tests/test_config_singleton.py` greps the tree |
| **[BUILT]** | `lib/pubsub.py` — 6 topics, local shim, idempotent consumption | `tests/test_pubsub.py` |
| **[BUILT]** | `lib/firestore.py` + reverse-index traversal on the emulator | `tests/test_firestore_emulator.py` → 3 passed |
| **[BUILT]** | `lib/telemetry.py` — OTel, console exporter | `/healthz` reports `telemetry_exporter` |
| **[BUILT]** | `lib/vertex.py` — single model door, Vertex backend pinned | `tests/test_tiering.py` |
| **[BUILT]** | `agents/smoke/` — ADK 2 agent, delete-ready | `adk web agents` lists `["smoke"]` |
| **[BUILT]** | `services/api/` — FastAPI, SSE transport | `/healthz` 200; SSE emits `event: stub` |
| **[BUILT]** | The corpus — 4,004 conclusions, 1,083 claims, measured die-back | `corpus/data/stats.json`, `make corpus-verify` |
| **[BUILT]** | `evals/` — 9 metric definitions + runner | `make eval` → exit 0, 0 scenarios |
| **[DESIGNED]** | Tiered degradation T0/T1/T2 | Door exists and closes; nothing behind it yet |
| **[DESIGNED]** | Retraction authority gate | Fields exist on claims and sources; **nothing checks them** |
| **[DESIGNED]** | Firestore rules + composite indexes | Written, **never deployed** |
| **[DESIGNED]** | `infra/deploy.sh` → Cloud Run | Written, **never run** |
| **[FUTURE]** | Extraction, watchers, cascade, materiality, escapement | Task 2 |
| **[FUTURE]** | Five-state decision, authority enforcement | Task 3 |
| **[FUTURE]** | Repair court, obligations, compensation synthesis | Task 4 |
| **[FUTURE]** | Load rating, the operator UI, the demo | Task 5 |

### What has actually been run

Run in this environment, output observed:

- `make test` → **41 passed** (38 in-process, plus 3 against a live Firestore
  emulator). `ruff check` and `ruff format --check` clean over 31 files.
- `make corpus` → wrote `corpus/data/`; `make corpus-verify` → *"corpus is
  deterministic: regenerated manifest is byte-identical"*.
- `make eval` → exit 0, `evals/results/latest.json` written, and it says in the
  file that nothing was evaluated.
- `adk web agents` → server up, `/list-apps` → `["smoke"]`.
- `uvicorn services.api.main:app` against the emulator → `/healthz` 200, SSE
  endpoint streams its `stub` event.
- Firestore emulator v1.19.8 → running, corpus slice loaded, reverse index walked.

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

Task 1 builds **none** of it.

---

## The corpus

One scenario, built completely: a supplier lead-time premise feeding quotes,
purchase orders, an ad flight and customer promises across six months.
**Synthetic** — see [`corpus/README.md`](corpus/README.md) for the generation
model, the assumptions it rests on, and every measured property.

The headline: **the hub claim `supplier_K.lead_time_days = 11` carries 2,004
transitive dependents. Moving it to 20 harms 94 of them. 95.3 % die back.**
That percentage is computed from `committed_lead_days` on committed rows, not
chosen — `tests/test_corpus.py` recomputes it from `radius_truth.jsonl` and
asserts the stats file agrees.

| | Measured | Target in the brief |
| --- | --- | --- |
| Conclusions / claims | 4,004 / 1,083 | ~4,000 / ~1,100 |
| Hub transitive dependents | 2,004 | ~2,000 |
| **Die-back** | **95.3 %** | ≈96 % |
| Live material survivors | 55 | ~31 |
| — not escaped / escaped | 30 / 25 | ~12 / ~19 |
| Max premise-chain depth | 5 | "report actual" |
| UNRESOLVED conclusions | 4 | ≥3 |
| Adversarial artifacts (unprocessed) | 1 | 1 |

The last three rows of divergence are explained, not tuned away, in
`corpus/README.md § Where the measurements differ from the specification`.

---

## Running it

Nothing here needs a Google Cloud account.

```bash
make install                 # uv venv (Python 3.12) + deps
make emulator                # terminal 1: Firestore emulator (needs Java 11+)
make test                    # terminal 2: 41 tests, 3 of which need the emulator
make dev                     # terminal 2: API on http://127.0.0.1:8000/healthz
make corpus-verify           # proves the committed corpus is reproducible
make eval                    # runs the harness over zero scenarios, honestly
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
| Model | `gemini-3.6-flash` | GA on Vertex AI since 2026-07-21; verified against Google's model documentation on 2026-08-12 |
| Region | `us-central1` | Pinned in `lib/config.py`, never inferred |
| Backend | Vertex AI | `GOOGLE_GENAI_USE_ENTERPRISE=true`, set from config in `lib/vertex.py` |
| Python | 3.12.3 | `pyproject.toml` requires `>=3.12,<3.13` |

The model string appears in `lib/config.py` and nowhere else in the repository.
`tests/test_config_singleton.py` greps every tracked file to prove it.

**Two things changed since this project was specified**, both reported rather
than silently worked around:

- `GOOGLE_GENAI_USE_VERTEXAI` is **deprecated** in google-adk 2.6.3 /
  google-genai 2.17.0, replaced by `GOOGLE_GENAI_USE_ENTERPRISE`. Setting the old
  flag still works but emits a `DeprecationWarning`, so `lib/vertex.py` sets the
  new one.
- "Gemini 3.5" is not a single flagship. The current family is `gemini-3.1-pro`,
  `gemini-3.6-flash` and `gemini-3.5-flash-lite`. `gemini-3.6-flash` is the
  newest GA Flash model and is what is pinned.

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
