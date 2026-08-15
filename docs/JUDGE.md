# UNWIND — judge card

*If you read one file, read this one. Every number here was produced by a
committed script. Nothing is projected.*

---

**Project** — UNWIND, Consequence Clearing
**Track** — Google All Things Agentic Hackathon, Fortified Enterprise Fleet

**One line** — *Cache invalidation for decisions: when a fact turns out false,
everything it touched raises its hand, and the system computes what must now be
un-sent, un-paid, or apologised for.*

**The problem** — Premises don't fail because the model reasoned badly. They
fail because **the world changed after the reasoning was correct**. A quote
assumes an 11-day lead time; the lead time moves; nobody goes back to find the
2,594 decisions built on it.

**Target users** — Operations, commercial and supply-chain teams who own
commitments made to counterparties.

---

## What it does, in one pass

```
type a fact that changed
  → parse echo          what it heard, BEFORE it acts
  → authority gate      does this source have standing?      (T0, no model)
  → blast radius        2,594 dependent decisions             (T0, no model)
  → materiality         shock > slack, subtraction            (T1, no model)
  → THE CULL            2,594 → 78     ~90% removed by arithmetic
  → four regimes        only material×escaped is an alert
  → the court           owners argue, a third principal rules (T2, model)
  → obligation          named customer, money, a human signs
```

---

## Core technology

Python 3.12 · **ADK 2.6.3** (`Workflow`, `FunctionNode`, `Edge`, `ctx.route`) ·
**Gemini via Vertex AI** · Firestore · Pub/Sub · **Cloud Run — deployed and
verified**.

⚠ **One ADK 2 construct is load-bearing today** — the `Workflow` of
`FunctionNode`s in `agents/cascade/workflow.py`. `AgentTool`, dynamic scheduling
and the durable runtime are **locked design, not built**, and the architecture
diagram draws them dashed. The court's parallelism is a thread pool, and
`ARCHITECTURE.md` says so.

**Gemini's role** — the *second pass*. The deterministic parser goes first on
purpose: a regex has **no instruction-following surface**, so prompt injection
fails structurally rather than through a filter. Gemini is shown only what the
parser cannot read, plus the prose for pleas, rulings and corrections. **It is
not the decision-maker.**

**Agent count, accurately** — **5 model-driven roles** in the product path
(blind re-deriver, commitment owner, arbiter rationale, correction drafter,
claim reconciler) + 1 evaluation-only. The 12 "owners" seated in the demo are
**12 instances of one role**, not 12 agents. Decisions are deterministic; the
model writes prose.

---

## ⭐ Most innovative

**The arithmetic cull.** 2,594 dependents reduced to 78 with the model switched
off — roughly 90% removed by subtraction. Enforced in CI: the full cascade runs
with `UNWIND_VERTEX_DISABLED=1` and the build fails if a single model call
happens. Cheaper, faster, auditable, and it survives a Vertex outage.

---

## Strongest proof — live, measured

| | |
| --- | --- |
| Vertex call | **OK**, 0 model errors |
| Model / location | `gemini-3.5-flash-lite` (GA) / `global` |
| Parser only | **81.8%** (36/44) |
| Parser + Gemini | **100.0%** (44/44) |
| **Delta** | **+18.2 pp** |

Only one class moved — `temporal:absolute-duration`, 66.7% → 100.0%. The four
classes already at 100% show a delta of exactly zero, because nothing in them
was ever sent to the model. **That is the second-pass architecture measured
rather than argued.**

⚠ **The model's denominator is 8, not 44.** The parser missed 8 claims; Gemini
saw those 8 and got 8 right. The 100% is a property of the *combined pipeline
over 44 gold claims* — not a claim that the model extracts perfectly.

---

## Other measured results

| | |
| --- | --- |
| Tests | **261 passed / 11 skipped** |
| Eval scenarios | **41 passed**, 5 classes |
| False-retraction rate | **0.0** |
| Model calls on T0/T1 | **0** |
| Duplicate obligations | **0** |
| Interface | **60 fps** at 4,206 nodes; on-screen counter asserted equal to the cascade's own count |
| CI gates | **20** |

---

## ⚠ Biggest weaknesses — stated, not hidden

1. **Three of the four architectural cards are not built.** WARRANT, CONTROL
   TOWER and COUNTERSIGN are locked design only. What is built is UNWIND CORE,
   and the architecture diagram draws the other three dashed rather than
   implying them.
2. **T2 judgement quality is unmeasured.** The live run attempted 60 nodes and
   resolved **0**, with 0 exceptions. This is a **non-test, not a failure**: all
   174 queue nodes carry `committed_lead_days = None`, and the assessor returns
   UNRESOLVED *before* the model's answer is consulted. The corpus fixed the
   outcome, not Gemini.
3. **Synthetic corpus.** Artifacts and extraction lexicon were written by the
   same author. `docs/COVERAGE.md` states this at length.
4. **The agents don't decide.** Owner stance and arbiter tally are arithmetic.
   Honest framing: multi-principal orchestration with LLM narration.

---

## Deployment status

**DEPLOYED AND VERIFIED.** `https://unwind-hgeodtazqq-uc.a.run.app` — service
`unwind`, region `us-central1`. `make deploy-verify` reports **5/5 PASS, exit 0**
against the live URL, and step 5 drives a real headless browser at the deployed
page and asserts the on-screen counter equals the cascade's own computed count:
**78 = 78**.

Still not deployed, and stated rather than blurred: Firestore rules and composite
indexes are written and never applied. Model Armor was never configured —
deliberately not scripted, because a template without a verification looks like a
defence and is not one.

---

## Where to look

| Question | File |
| --- | --- |
| The live Gemini run | `docs/LIVE-VERIFICATION.md` |
| What each artifact proves, and does not | `docs/evidence/README.md` |
| Extraction coverage, incl. the worst class | `docs/COVERAGE.md` |
| The 4-minute demo | `docs/DEMO.md` |
| How to deploy, and what was wrong before | `docs/DEPLOY.md` |
| Why this is a protocol, not just a product | `docs/RETRACTION-FEED.md` |
| Component-by-component justification | `ARCHITECTURE.md` |

Run it yourself, no GCP account needed:

```bash
make install && make ui      # http://127.0.0.1:8000
```

---

## Final verdict, self-assessed

A contrarian architecture, proved rather than claimed: ~90% of the work happens
without the model, and CI fails the build if a single model call escapes into the
deterministic tier. Weakened by a judgement tier that has never been meaningfully
exercised, a synthetic single-author corpus, and three of four architectural
cards still unbuilt.

**No self-score is offered.** Scoring is the judges' to do, and inventing a
number against a rubric this submission does not own would be exactly the kind of
unbacked figure the rest of this repository refuses to print. The honesty here is
not modesty — it is the reason the +18.2 pp is worth believing.
