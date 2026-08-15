# Devpost submission draft — UNWIND

Every field below is drafted for direct copy-paste into the Devpost form.
Numbers here are the same numbers the repository and the deployed service
report — nothing here was invented for the form.

---

## Project name

**UNWIND**

## Tagline

**Consequence Clearing — when a fact turns out false, UNWIND finds every
decision it touched and reduces the count by arithmetic before a model
ever looks at it.**

## Elevator pitch (short, ~2 sentences)

Premises don't fail because a model reasoned badly — they fail because the
world changed after the reasoning was correct. UNWIND watches the claims a
business's decisions actually depend on, and when one is retracted, walks
2,594 dependent decisions back to a reverse index, cuts that to 78 that
still need a human — by pure subtraction, zero model calls — and drafts the
correction obligation for the 174 that need judgement.

## Description

### The problem

A supplier's lead time moves from 11 days to 20. A tariff rate changes. A
contract clause is reinterpreted. Every decision an organisation already
made that rested on the old value — quotes, purchase orders, customer
promises — is now silently wrong, and nothing in the enterprise points
backward from the changed fact to the decisions built on it. Correction
propagates socially: someone remembers, sends an email, hopes. The
decisions that already escaped into the world — sent, signed, shipped,
paid — are the expensive ones.

### What UNWIND does

1. **Extract** a typed premise from a conclusion and record the dependency
   edge, so the graph exists before anything breaks.
2. **Watch** the claim with a dormant watcher; a sentinel flags silence.
3. **Propagate** — when a claim is retracted, walk the reverse index to the
   full transitive closure. On the demo corpus: **2,594 dependent
   decisions**.
4. **Score** materiality (shock vs. slack, subtraction) and escapement
   (did it already leave the building) — a deterministic router, not a
   prompt, so the core novelty of the product cannot hallucinate. This
   reduces 2,594 to **78** — **1,468 immaterial, 874 already closed out,
   174 sent to judgement** — and it is **pure arithmetic: zero model
   calls**. `tests/test_zero_model.py` walks the import graph of every
   module in the deterministic core and fails the build if a single path
   can reach a model client; the guarantee is enforced on every CI push
   with Vertex AI disabled.
5. **Arbitrate** the 174 — commitment owners argue their case as parallel
   single-turn agent tools, and a third principal (with no stake in any
   outcome) rules. This is where Gemini is used.
6. **Settle** and **draft the correction** — a named counterparty, the
   actions still reversible, the exposure that is not (as a range, with
   its assumptions), and a named human who must sign.

### Why the model is the second pass, not the first

The deterministic parser handles extraction first, on purpose: a regex has
no instruction-following surface for a prompt injection to attack.
**Measured, not asserted:** parser-only recall is **81.8%**; parser +
Gemini is **100.0%** — a **+18.2 percentage point** delta, verified in a
live run against Vertex AI on 2026-08-13 (project
`project-895d4ca8-d301-447d-916`, model `gemini-3.5-flash-lite`, 0 model
errors). Read the 100% honestly: **the model's own denominator is 8, not
44** — the parser missed 8 of 44 gold claims, Gemini was shown only those
8, and got 8 right. Only one extraction class ever moved
(`temporal:absolute-duration`, 66.7% → 100.0%); the other four classes were
already at 100% and see a delta of exactly zero, because nothing in them
was ever sent to the model.

### Findings, stated plainly

- **Worst extraction class:** `temporal:absolute-duration` at 66.7%
  parser-only recall — published, not hidden, because it is exactly where
  the second pass earns its place.
- **T2 (judgement) is a non-test, and we say so.** The live run attempted
  60 nodes and resolved 0 — not a model failure. All 174 queue nodes carry
  `committed_lead_days = None`, and the assessor returns UNRESOLVED before
  the model's answer is even consulted. What the run does prove: the
  orchestration executes end-to-end against live Vertex with 0 exceptions
  across 60 nodes (120 model calls).
- **The corpus is synthetic and single-author.** Artifacts and the
  extraction lexicon were written by the same person; `docs/COVERAGE.md`
  states exactly what that does and does not represent, rather than
  burying it in a footnote.
- **Tests, run today:** `pytest -q` → **261 passed, 11 skipped** (272
  collected; the 11 skips need a live Firestore emulator).

### Deployed and verified

Live on Cloud Run (`us-central1`), UI and API served from one origin —
<https://unwind-hgeodtazqq-uc.a.run.app>. `make deploy-verify` asserts the
deployed service's own cascade totals agree with what it actually sent
over SSE, that the adversarial refusal still refuses by reason code, and
(via a real headless browser) that the on-screen cull counter equals the
cascade's own computed material count — 78 = 78.

### Architecture

Four cards. **CARD 1 · UNWIND CORE** is frozen and is what's deployed
today: UI → FastAPI on Cloud Run → `spine/` (the zero-model boundary,
2,594 → 78 by arithmetic) → the 174 that need judgement cross into
`court/` + `judgment/`, the only tier allowed to call Vertex AI → Firestore
holds state throughout. **CARD 0 · WARRANT**, **CARD 2 · CONTROL TOWER**,
and **CARD 3 · COUNTERSIGN** are locked design for the build phase, mapped
onto concrete ADK 2 constructs (`FunctionNode`, dynamic node scheduling,
single-turn `AgentTool`, a durable long-running runtime) but not yet built
— see the README's ADK 2 mapping table and `assets/architecture.svg`.

## Built with

Python 3.12 · ADK 2.6.3 (`Workflow`, `FunctionNode`, `Edge`, `ctx.route`,
single-turn `AgentTool`) · Gemini via Vertex AI (`gemini-3.5-flash-lite`,
`gemini-3.6-flash`) · Google Cloud Run · Firestore · Pub/Sub · FastAPI ·
pytest · Playwright (headless-browser verification) · ruff

## Try it out

- **Repo:** <https://github.com/akashbichukale111/unwind>
- **Live deployment:** <https://unwind-hgeodtazqq-uc.a.run.app>
- **Video:** _[YouTube URL — placeholder until recorded, see
  `submission/recording_checklist.md`]_

## What's next

- Build CARD 0 (WARRANT), CARD 2 (CONTROL TOWER), CARD 3 (COUNTERSIGN) —
  the locked design in the README's ADK 2 mapping table.
- Close the T2 judgement-quality gap with a fair fixture (see
  `docs/T2-MEASUREMENT.md` for why the obvious fixture is a mirror, not a
  measurement, and what would fix that).
- Firestore rules and composite indexes are written but never deployed —
  a separate step via the Firebase CLI.
