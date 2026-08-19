# The Agentic Command OS demo — four minutes

**Every number below is produced live by the running system, from a real
call into the engines named in `docs/architecture.md`.** The one input that
is scripted (stage 4's adversarial observation) is labelled `SIMULATED` on
screen, in the API response, and here — never presented as organically
observed. If a figure here disagrees with what the screen shows, the screen
is right and this document is stale.

This is the demo for the layer added on top of the existing four-minute
UNWIND-core walkthrough (`docs/DEMO.md`) — it does not replace that script,
it sits above it, exactly as `command_os/` sits above `spine/`.

## Before you start

```bash
make install
make emulator                 # separate terminal — Command OS writes real events
make ui                       # http://127.0.0.1:8000
```

No GCP account needed for this layer specifically: the mission always sets
`UNWIND_COUNTERSIGN_SIMULATED=1`, so it makes zero model calls (see
`command_os/mission.py`'s module docstring). Full screen, 1600×900 or wider.

---

## The script

| Time | Screen | What you say |
| --- | --- | --- |
| **0:00–0:25** | Landing: AGENTIC COMMAND OS | "One high-level objective, one system that plans, builds a fleet, governs it, and recovers from an attack on its own — a closed loop, not a chatbot that stops at 'create → execute.'" |
| **0:25–0:55** | Click "Run mission" | "The objective is fixed for this demo: build and deploy a secure enterprise service. Watch the eleven stages run — every one of them is a real function call, not a slide." |
| **0:55–1:35** | Stage 1: AGENT FACTORY | "Seven roles from the real fleet topology — Sentinel, Orchestrator, five workers. This mission assigns Worker #04, Browser/Research — `singularity/fleet.py` already documents this worker as the fleet's designated attack surface, before this demo existed. Reused, not written for the occasion." |
| **1:35–2:00** | Stages 2–3: CAPABILITY GENOME, BEHAVIORAL DNA | "The genome negotiates what this agent may do for this task, right now — `ALLOW`, two actions, LOW risk. Behavioral DNA takes a baseline reading — `NORMAL`, score near zero. Both zero-model, pure functions, the same `compute_genome`/`detect_drift` that already had their own unit tests before this orchestration existed." |
| **2:00–2:40** | Stage 4 → 6: DRIFT → HYPERION → BLOCKED | "One scripted event: 147 tool calls, the finance dataset, a secret-access attempt. Labelled `SIMULATED` — say it out loud. Everything after it is real: `detect_drift` scores it `CRITICAL`. Hyperion scores the attempted action and logs it. The Gateway — the same one choke point Control Tower has always had — refuses it `SCOPE_EXCEEDED` before any work happens. Watch the reason code on screen; it is not a caption someone wrote, it is `decision.reason_code` from `tower/gateway.py`." |
| **2:40–3:15** | Stage 7–9: COUNTERSIGN, ISOLATED, SELF-HEAL | "An independent verifier — scripted, labelled, zero model calls — confirms the block was correct. The agent is isolated, mission-scoped, not a new enforcement layer pretending to be one. Then repair: a narrower genome is negotiated, a human concurs, the verifier agrees again, and warrant is re-minted — the exact `record_human_concurrence` → `verify_and_record` → `mint` chain `/api/instrument/earn` already uses for its own cold-start moment." |
| **3:15–3:40** | Stage 10–11: VALIDATION, RESUME | "The Gateway is asked again, at the narrowed genome. `ALLOWED`. The mission resumes. Nothing here is asserted — it is the same `evaluate_with_hyperion` call from stage 5, run a second time, returning a different, real answer." |
| **3:40–4:00** | Executive report + System Reality panel | "Agents in fleet, threats detected, agents isolated, repairs completed, validation: PASS, fleet status: HEALTHY — every number folded from the stages that just ran. Below it, System Reality: LIVE, SIMULATED, REFERENCE, DESIGNED, stated for every feature on this screen, including the ones this demo does *not* claim — no Digital Twin, no autonomous Red Team agent, no live agent spawning." |

**Closing card:** `CREATE → CAPABILITY → BEHAVIOR → RISK → AUTHORITY → EXECUTION → CHALLENGE → DETECTION → ISOLATION → REPAIR → VALIDATION → RESUME.` That closed loop is the product story, not any single card in it.

---

## The one moment that carries it

**Stage 6's reason code.** Everything before it is setup; everything after
it is recovery. A judge who reads `SCOPE_EXCEEDED` on screen and understands
that it came from the same four-check Gateway Control Tower has always had —
not a new "AI safety" layer bolted on for the demo — has understood the
whole architecture.

## If a step fails

The mission endpoint (`POST /api/command-os/mission`) returns `503` if
Firestore is unreachable, the same honest-degrade discipline every other
write-backed endpoint in this app already uses (`/api/instrument/burn`,
`/api/instrument/earn`, `/api/hyperion/probe`). The UI shows
`FIRESTORE UNREACHABLE` — never a fabricated trace. Start the emulator and
retry.

## What a judge will ask, and the short answer

- **"Is this fifteen new agent products?"** No — see
  `docs/COMMAND-OS-CONCEPT-MAP.md`. Fifteen buzzwords map onto six real
  modules and one new orchestrator; none of the fifteen names existed in
  this codebase before that mapping document.
- **"Did you build a new security layer, or reuse the old one?"** Reused.
  `command_os/mission.py` contains no new decision logic — every check is a
  call into `singularity/`, `hyperion/`, `tower/`, `warrant/`, or
  `countersign/`, unchanged.
- **"What's actually simulated here?"** Exactly one input: the adversarial
  `BehaviorObservation` in stage 4. Everything downstream reacts to it for
  real. The System Reality panel states this for every feature, not just
  this one.
- **"Why didn't UNWIND core (the claim-retraction engine) run in this
  mission?"** Because no claim was retracted — see "What this mission does
  not do" in `docs/architecture.md`. It stays fully live and reachable as
  its own card.
