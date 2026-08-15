# Demo script — video v1

**Target runtime 4:00 · hard ceiling 4:00.** Voiceover budget **≤560 words**
(≈140 wpm at an unhurried pace). Actual count is asserted at the bottom of this
file.

**Every shot is marked `LIVE` or `CUTAWAY`.** `LIVE` means the thing is running
in front of the camera, unedited, in one take. `CUTAWAY` means a static screen
— a console, a file, a terminal that has already finished. There is no third
category, and nothing in this script is a slide with numbers typed onto it.

**Video v1 is a submittable floor.** It stands alone and satisfies Stage One
without any unbuilt feature appearing in it. The v2 replacements are listed at
the bottom and are **not** referenced in the voiceover.

> **Rule for the presenter:** if a figure on screen disagrees with this
> document, the screen is right and this document is stale. Re-run
> `make ui-check`, which asserts the on-screen counter equals the cascade's own
> material count.

---

## Before recording

1. **Warm the service.** Hit the deployed URL **twice** and wait for the second
   response. Cloud Run scales to zero; a cold start on camera looks like a
   broken demo. `bash scripts/health_check.sh` counts as one hit.
2. Full screen, **1920×1080**, browser zoom 100%, no bookmarks bar, no
   notifications.
3. Cursor visible and slow. The cull is the star; do not move the mouse during
   it.

---

## ACT 1 — the thesis and the cull (0:00–1:10)

### 1.1 · 0:00–0:12 · `CUTAWAY` — Cloud Run console
Service `unwind`, region `us-central1`, green check, revision name visible.

> This is UNWIND, running on Cloud Run. Everything you are about to see happens
> on this deployed service. Nothing is local and nothing is edited.

### 1.2 · 0:12–0:32 · `LIVE` — the field
The deployed URL. 4,206 nodes, causal debt figure in amber.

> Four thousand two hundred live decisions, resting on eleven hundred premises.
> A supplier says eleven days, so you quote, you order, you promise a customer.
> Then the world changes — and nothing in the enterprise points backwards from
> the fact to the decisions built on it.

### 1.3 · 0:32–0:48 · `LIVE` — type into the bar, parse echo appears
Type `supplier_K lead time is now 20 days`. Do not press Confirm yet.

> One input. Before it touches anything, it tells you what it heard: this
> premise, eleven to twenty, carrying two thousand five hundred and ninety-four
> decisions. If that reading is wrong, this is where you say so.

### 1.4 · 0:48–1:10 · `LIVE` — Confirm, then the cull. **Say nothing for the first eight seconds.**

> Two and a half thousand decisions, down to seventy-eight. Fourteen sixty-eight
> immaterial — the buffer absorbed it. Eight seventy-four already closed out.
> A hundred and seventy-four handed to judgement rather than guessed. Ninety
> percent removed by subtraction, with the model switched off.

---

## ACT 2 — refusal, and the assertion (1:10–2:50)

### 2.1 · 1:10–1:32 · `LIVE` — press `R`, forged retraction
Type `broker says supplier_K lead time is 34`.

> A false retraction is worse than a missed one. This is a freight broker
> claiming the supplier's lead time changed. It holds authority over its own
> freight claims and none over this one. Refused — source outside claim scope —
> and the radius is zero. Nothing was walked.

### 2.2 · 1:32–1:52 · `CUTAWAY` — `tests/test_zero_model.py` on screen

> The zero-model guarantee is not a promise in a README. This test walks the
> import graph of every module in the deterministic core and fails if any of
> them can so much as reach a model client. CI runs the entire cascade with
> Vertex disabled and fails the build on a single call.

### 2.3 · 1:52–2:24 · `LIVE` — terminal: `make deploy-verify URL=...`
Let all five steps print.

> This is the check that matters. It runs a real cascade against the deployed
> service, then drives a real browser at the deployed page, reads the number on
> screen, and asserts it equals what the service actually computed. Seventy-eight
> equals seventy-eight. Opening a web page proves a web page loads. This proves
> it is not a fixture.

### 2.4 · 2:24–2:50 · `LIVE` — the obligation; the field dissolves into paper

> Seventy-eight decisions changed. Forty-eight of them already went out to
> someone. This is what the company now owes one of them: a named customer, a
> quote it can re-issue, and one payment it cannot take back. Exposure as a
> range with its assumptions, never a point estimate. And a named human who has
> to sign it.

---

## ACT 3 — the honesty apparatus, and close (2:50–4:00)

### 3.1 · 2:50–3:14 · `LIVE` — press `H`, honesty panel

> This panel is the part I most want you to see. It publishes the worst thing
> about the system: extraction recall is sixty-six point seven percent on
> absolute durations. That is the single class where the model earns its place.

### 3.2 · 3:14–3:40 · `CUTAWAY` — `docs/LIVE-VERIFICATION.md`

> Parser alone, eighty-one point eight percent. Parser plus Gemini, one hundred.
> But the model's denominator is eight, not forty-four. It was shown only the
> eight the parser missed, and returned eight correct values. The four classes
> the parser already handled show a delta of exactly zero, because nothing in
> them was ever sent to a model.

### 3.3 · 3:40–4:00 · `LIVE` — README honesty map, then the close card

> The judgement tier is still unmeasured, and we call that a non-test rather
> than a result. The corpus is synthetic and written by one author. All of it is
> written down, because that honesty is the reason the eighteen-point gain is
> worth believing at all. The world changed. Your decisions did not.

**Close card:** `THE WORLD CHANGED. YOUR DECISIONS DIDN'T.`

---

## The three moments that carry it

1. **The cull.** Do not talk over the first eight seconds. A judge who watches
   2,594 become 78 with no model call understands the architecture before it is
   explained.
2. **`78 = 78`.** The single hardest-to-fake claim in the submission.
3. **The one payment that cannot be taken back.** Everything else in the demo is
   recoverable; that line is why the system exists.

## If the live run fails

`make golden` writes a deterministic transcript of the same cascade. If the API
is unreachable the UI shows a full-width banner reading **"REPLAY — live run
failed, this is a recorded execution"**, and it is never concealed. Say it out
loud if it happens. A disclosed replay costs less than a concealed one.

---

## PLANNED — video v2 replacements

None of these appear in v1, and none is referenced in the v1 voiceover. They
replace or extend the shot named, once the corresponding card is built.

| Replaces | v2 shot | Requires |
| --- | --- | --- |
| 1.4 (extends) | **Warrant burn-and-reroute** — the cull runs, warrant is debited per act, the balance falls, and an act that would exceed it is refused and routed to a human | Card 0 |
| 2.1 (extends) | **Countersign disagrees** — Gemini approves a mint, Gemma refuses it, the mint does not happen | Card 3 |
| 2.2 (replaces) | **ADK construct proof, live** — the trace view showing the warrant SPEND `FunctionNode` and the Countersign `AgentTool` executing as distinct constructs | Cards 0 + 3 |
| 3.1 (extends) | **SYNTHETIC-labelled balances** — the honesty panel showing which warrant balances are `EARNED` and which are `SYNTHETIC`, with SYNTHETIC visibly marked on screen | Card 0 |

---

## Voiceover word count

Counted over the blockquoted voiceover lines inside the three acts only —
excluding stage directions, headings, tables, and the presenter-rule note:

```bash
awk '/^## ACT 1/,/^## The three moments/' submission/demo_script.md \
  | grep '^> ' | sed 's/^> //' | wc -w
```

**Measured: 507 words** — budget 560. At 140 wpm that is **3:37** of speech
inside a 4:00 ceiling, which leaves deliberate silence over the cull (shot 1.4)
and room to slow down without overrunning.
