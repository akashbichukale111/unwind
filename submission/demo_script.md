# UNWIND — demo script v1

**Target runtime: ≤ 4:00. Target voiceover: ≤ 560 words at real speaking pace
(counted below with `python3 -c "print(len(text.split()))"` on the exact
voiceover text — this cut is 392 words, leaving margin for pacing pauses).**
Every shot is marked **LIVE** (recorded off the running deployed system, no
edit) or **CUTAWAY** (a second live artifact — a terminal, a doc — cut to
mid-narration, still unedited and unscripted in content). Nothing in this cut
is staged footage or a slide. This script must stand alone as a submittable
floor for Stage One; the PLANNED column at the bottom lists what v2 adds and
is explicitly out of scope for this recording.

---

## Act 1 — 0:00–1:10 — thesis, live, on the deployed URL

| Time | Shot | Screen | LIVE/CUTAWAY |
| --- | --- | --- | --- |
| 0:00–0:15 | Open on the **Cloud Run console** tab for service `unwind`, region `us-central1`, then cut to the deployed UI at `https://unwind-hgeodtazqq-uc.a.run.app` | Cloud Run dashboard → live UI | **LIVE** |
| 0:15–0:35 | Type the retraction into the running UI bar | `supplier_K lead time is now 20 days` | **LIVE** |
| 0:35–1:10 | Parse echo renders, then the cull runs and the counter falls | 2,594 → 78, breakdown on screen | **LIVE** |

**Voiceover (Act 1, 143 words):**

> "Premises don't fail because a model reasoned badly. They fail because the
> world changed after the reasoning was correct. This is UNWIND, deployed
> right now on Cloud Run — that's the console, that's the live revision.
>
> A supplier's lead time moves from eleven days to twenty. I type that fact
> into the running deployment — no script, no edit.
>
> It reads back what it heard before it acts — that's the parse echo, so a
> misparse is a question, not a correction someone receives. Confirmed, and
> now watch: two thousand five hundred ninety-four dependent decisions light
> up, and the system reduces that to seventy-eight — by arithmetic alone,
> with the model switched off. Fourteen sixty-eight die back on the buffer.
> Eight seventy-four were already closed out. A hundred seventy-four go to
> judgement instead of being guessed at. Ninety percent of this is
> subtraction."

---

## Act 2 — 1:10–2:50 — refusal before traversal, and 78 = 78 proven live

| Time | Shot | Screen | LIVE/CUTAWAY |
| --- | --- | --- | --- |
| 1:10–1:35 | Type the forged, out-of-scope retraction | `broker says supplier_K lead time is 34` | **LIVE** |
| 1:35–1:55 | Refusal renders with its reason code, radius zero | `source_outside_claim_scope`, radius 0 | **LIVE** |
| 1:55–2:25 | Run `make deploy-verify URL=...` (or the on-screen assertion) against the deployed service | terminal: `counter integrity OK`, `on-screen counter 78 = cascade material 78` | **LIVE** |
| 2:25–2:50 | Cut to a terminal running the zero-model guarantee test | `pytest tests/test_zero_model.py -v` → PASS | **CUTAWAY** |

**Voiceover (Act 2, 136 words):**

> "Now the adversarial case. A freight broker tries to retract the
> supplier's lead time — a claim it has no authority over. Watch the
> radius.
>
> Refused, by reason code, before a single node is traversed. Radius zero.
> This gate runs deterministically, at radius zero, before the graph is
> ever walked — a forged retraction never gets the chance to cascade.
>
> And this number on screen isn't decoration. Here's the same assertion
> running live against this deployment: a headless browser reads the
> on-screen counter, and asserts it equals the number the cascade actually
> computed. Seventy-eight equals seventy-eight — verified, not trusted.
>
> And the zero-model guarantee itself is enforced the same way — this test
> walks the import graph of every module in the deterministic core and
> fails the build if any path can reach a model client."

---

## Act 3 — 2:50–4:00 — the honesty apparatus, and close

| Time | Shot | Screen | LIVE/CUTAWAY |
| --- | --- | --- | --- |
| 2:50–3:15 | Press **H** for the honesty panel in the running UI | 81.8% overall extraction recall, worst class `temporal:absolute-duration` at 66.7%, highlighted | **LIVE** |
| 3:15–3:35 | Cut to `docs/LIVE-VERIFICATION.md` | recall 81.8% → 100.0% (+18.2 pp); denominator note (8, not 44) | **CUTAWAY** |
| 3:35–3:50 | Cut to the T2 non-test finding | "0 of 60 resolved — a non-test, not a model failure" | **CUTAWAY** |
| 3:50–4:00 | Closing card | `THE WORLD CHANGED. YOUR DECISIONS DIDN'T.` | **LIVE** |

**Voiceover (Act 3, 113 words):**

> "Press H for the honesty panel. Eighty-one point eight percent extraction
> recall overall, and it shows you the worst class too — sixty-six point
> seven percent on absolute durations — highlighted, not buried.
>
> That's exactly where Gemini earns its place: shown only what the parser
> missed, it closes that gap — recall goes eighty-one-point-eight to one
> hundred percent. But the model's own denominator is eight, not
> forty-four. State it that way, always.
>
> And the honest failure: the judgement tier resolved zero of sixty
> attempted nodes live against Vertex. Not a model failure — a non-test,
> and the repository says so, not just to me.
>
> The world changed. Your decisions didn't — until now."

---

## Word count

Counted programmatically from the exact voiceover text above (`.split()` on
whitespace), not eyeballed.

| Act | Words |
| --- | --- |
| Act 1 | 143 |
| Act 2 | 136 |
| Act 3 | 113 |
| **Total** | **392** (budget: ≤560) |

---

## PLANNED for v2 — explicitly not in this cut

Video v1 above is a complete, submittable Stage One floor on its own. These
shots depend on code that does not exist yet (CARD 0/2/3 — see the README's
ADK 2 mapping table) and are reserved for a v2 recording once that build
lands. Marking them PLANNED here — rather than script text implying they
happen — is the same honesty discipline the rest of this repository applies.

| Shot | What it proves | Status |
| --- | --- | --- |
| Warrant burn-and-reroute | A delegated act debits warrant; insufficient warrant triggers structural refusal and human routing | **PLANNED** — CARD 0 not built |
| Countersign disagree | Gemma, as an independent-family verifier, refuses to countersign a mint the primary model proposed | **PLANNED** — CARD 3 not built |
| ADK construct proof, live | One ADK 2 construct from the locked mapping table (e.g. registry→coordinator dynamic selection) shown executing, not just diagrammed | **PLANNED** — reserved per the Stage One prompt's instruction that this proof ships in v2 |
| SYNTHETIC-labelled balances | Warrant balances rendered on screen with an explicit `SYNTHETIC` tag, so a judge never mistakes a demo balance for a real one | **PLANNED** — CARD 0 not built |

## Recording notes

- Full screen, 1600×900 or wider. No cuts within a LIVE shot — CUTAWAY shots
  are separate unedited clips, not compositing.
- Hit the deployed URL twice before recording (cold-start avoidance) — see
  `submission/recording_checklist.md`.
- If the live run fails mid-recording, `make golden` and the UI's own
  "REPLAY" banner are the disclosed fallback described in `docs/DEMO.md` —
  say so on camera rather than concealing it.
