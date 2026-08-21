# Master prompt — run this in Claude Code, locally, in VS Code

**Why this file exists.** Every previous session ran in a sandbox with **no
`gcloud`, no ADC file, no metadata server and no Google Cloud connector**, so
no real model call was ever possible and all four models are honestly marked
`CONFIGURED_NOT_EXERCISED`. On your own machine that constraint is gone. This
is the prompt that turns that one difference into finished work.

**How to use it:** open this repo in VS Code, start Claude Code, and paste
everything inside the fenced block below as a single message.

**Before you paste**, confirm in a terminal:

```bash
gcloud --version                 # must print a version
gcloud auth application-default login
gcloud auth application-default set-quota-project <YOUR_PROJECT_ID>
gcloud config get-value project  # note this value, you will paste it in
```

Then replace `<YOUR_PROJECT_ID>` in the prompt with that value.

---

```
UNWIND — LOCAL EXECUTION: MAKE THE FOUR GOOGLE MODELS GENUINELY LIVE

You are running on my local machine in VS Code. Unlike every previous
session on this repository, this machine HAS `gcloud` and real Google Cloud
credentials. That single difference is the entire point of this task.

Repository: the UNWIND project, already open.
Branch: claude/unwind-hackathon-foundation-s36wdi   <- work ONLY on this branch
Project ID: <YOUR_PROJECT_ID>

============================================================
WHAT IS ALREADY DONE — DO NOT REBUILD ANY OF IT
============================================================

Read this so you do not waste the session re-deriving it.

  - 634 tests pass, 1 skipped. CI is green. Do not weaken any test.
  - Seven systems work: UNWIND CORE, WARRANT, CONTROL TOWER, COUNTERSIGN,
    HYPERION-ZERO, SINGULARITY-MESH, AGENTIC COMMAND OS.
  - Mission Time Machine works (12 real Firestore checkpoints, mission arc,
    RESUME live, REPLAY honestly marked NOT IMPLEMENTED).
  - Mission Media Lab exists with three adapters over one shared grounded
    brief built from real checkpoints (media/grounding.py).
  - Authentication works: lib/auth.py, real principals, no anonymous
    mutation. lib/gcp_auth.py resolves credentials via google.auth.default()
    and already understands ADC, service accounts, and Cloud Run service
    identity.
  - scripts/verify_models.py + `make verify-models` already exist and are
    credit-safe. USE THEM. Do not write a new verification script.
  - Model IDs live ONLY in lib/config.py. A model string anywhere else fails
    tests/test_config_singleton.py. If you need one, import it.

The ONLY reason the four models are not LIVE is that no previous environment
could reach Google. Your job is to close exactly that gap and prove it.

============================================================
ABSOLUTE RULES
============================================================

NEVER fake a model call, a response, a screenshot, a latency number, a
deployment, or a LIVE status. If something does not work, say so and say
why. A truthful NOT_CONFIGURED is worth more than a fabricated LIVE — the
whole credibility of this project rests on that, and a judge will check.

NEVER commit a credential. No API key, no service-account JSON, no token, no
ADC file. Check `git diff --cached` before every commit.

PROTECT THE CREDITS. This project runs on promotional credits.
  - Gemini: ONE tiny call.   - Gemma: ONE tiny call.
  - Veo: ONE generation.     - Lyria: ONE generation.
  No loops. No retries of anything expensive. No regenerating to get a
  nicer screenshot. If a generation succeeds once, that artefact is the
  artefact — reuse it.

PRESERVE everything listed above. Additive changes only. Do not refactor
working architecture because a different design looks cleaner.

Work only on branch claude/unwind-hackathon-foundation-s36wdi. Never force
push. Do not create a new Cloud Run service or a new URL.

============================================================
PHASE 1 — PROVE THE CREDENTIAL WORKS
============================================================

    python -c "import google.auth; c,p = google.auth.default(); print(p)"

It must print my project ID. If it does not, fix that before anything else —
every later phase depends on it.

Then confirm the app agrees:

    python -c "from lib.gcp_auth import resolve_auth; print(resolve_auth().as_record())"

Expect mode="adc" and my project. If it says mode="none", the resolver and
the SDK disagree, which is a real bug — find it and fix it.

Enable what is needed, only if it is missing:

    gcloud services enable aiplatform.googleapis.com --project <YOUR_PROJECT_ID>

============================================================
PHASE 2 — GEMINI AND GEMMA (nearly free)
============================================================

    export UNWIND_PROJECT_ID=<YOUR_PROJECT_ID>
    unset UNWIND_VERTEX_DISABLED
    make verify-models

This makes two tiny calls capped at 32 output tokens. A model only counts as
LIVE_VERIFIED if it echoes the sentinel UNWIND_VERTEX_LIVE — a 200 that
returns something else is a failure, not a pass.

If a check fails, the status already tells you the fix:

  AUTH_REQUIRED    re-run `gcloud auth application-default login`
  ACCESS_REQUIRED  enable the Vertex AI API; grant roles/aiplatform.user
  QUOTA_LIMITED    wait, or raise the quota; do NOT hammer it
  UNAVAILABLE      wrong model ID or wrong region for this project. Check
                   what is actually available:
                       gcloud ai models list --region=us-central1
                   If a pinned ID is genuinely wrong, fix it in
                   lib/config.py ONLY, and say in the commit what changed
                   and why.

Gemma note: gemma-3-27b-it may need to be deployed from Vertex Model Garden
before it can be called. If it is not deployed, that is a real blocker —
either deploy it or mark Gemma ACCESS_REQUIRED with the exact reason. Do not
substitute a Gemini model and call it Gemma; COUNTERSIGN's entire value is
that its verifier is a DIFFERENT model family, and warrant/ledger.py refuses
a same-family countersign on purpose.

============================================================
PHASE 3 — VEO AND LYRIA (these cost real money)
============================================================

Only after Phase 2 passes:

    make verify-models ARGS=--media

ONE video, ONE audio clip. If either fails, report the exact error and STOP —
do not retry. Veo is a long-running operation; let it poll to completion
rather than firing a second request.

If it succeeds, the artefacts land in .media/ (gitignored). Verify the files
are real and non-empty, and that the Media Lab can play them.

============================================================
PHASE 4 — MAKE THE UI TELL THE TRUTH
============================================================

Whatever Phase 2 and 3 actually returned must be what the UI shows.

  - GET /api/media/status must report the real per-model status.
  - The System Reality panel (command_os/status.py) must agree with it.
  - Only a model that genuinely returned a good response may read LIVE.
  - A model that failed keeps its classified status (AUTH_REQUIRED /
    ACCESS_REQUIRED / QUOTA_LIMITED / UNAVAILABLE / ERROR) and shows the
    real reason.

Update these to match reality, and nowhere claim more than the evidence:
  README.md, docs/, evidence/INDEX.md, command_os/status.py

============================================================
PHASE 5 — SCREENSHOTS OF THE REAL THING
============================================================

Run the app locally and capture, with a real browser:

    FIRESTORE_EMULATOR_HOST=localhost:8080 UNWIND_OPERATOR_TOKENS="demo:you@example.com" \
      make dev

Capture into docs/shots/, replacing the current NOT_CONFIGURED versions ONLY
for models that genuinely went live:

    10-gemini-live.png    the real synthesis text on screen
    11-gemma-live.png     the real countersign verdict
    12-veo-live.png       the video element actually playing
    13-lyria-live.png     the audio element actually playing
    14-model-status.png   the status panel showing real statuses

Reuse the existing capture script as a base:
    evidence/browser/capture_product_shots.py

Do not re-run a generation just to retake a screenshot. If a model did NOT
go live, keep its honest NOT_CONFIGURED screenshot — that is still true and
still worth showing.

Embed the new screenshots in README.md under "Live Product Evidence" and
verify every path resolves.

============================================================
PHASE 6 — EVIDENCE
============================================================

evidence/models/verification-*.json is written automatically by
`make verify-models`. Commit it — it is the primary proof.

Add a row to evidence/INDEX.md for each model:

    CLAIM | SOURCE | COMMAND | RESULT | ENVIRONMENT | STATUS

with the real latency, the real model ID, and the verbatim error for
anything that failed. Never a credential.

============================================================
PHASE 7 — DEPLOY (only after the above is green)
============================================================

Deploy the CURRENT branch to the EXISTING service. No new service, no new
URL:

    UNWIND_PROJECT_ID=<YOUR_PROJECT_ID> UNWIND_RUN_REGION=us-central1 \
      UNWIND_VERTEX_LOCATION=global ./infra/deploy.sh

Production authentication must use the Cloud Run SERVICE IDENTITY, not a
key. Grant the runtime service account roles/aiplatform.user. lib/gcp_auth.py
already picks up the metadata server automatically — verify that it does
rather than assuming.

Set before or during deploy:
    UNWIND_ENV=production
    UNWIND_OPERATOR_TOKENS=...   (or UNWIND_TRUST_IAP_HEADER=1 behind IAP)

Without one of those, production correctly refuses every mutating caller.
That is intended, not a bug — but you must configure it or the deployed app
will look broken.

Then verify the PUBLIC URL actually serves the new code:

    make deploy-verify URL=https://unwind-hgeodtazqq-uc.a.run.app
    curl -s https://unwind-hgeodtazqq-uc.a.run.app/api/media/status

Confirm the revision, 100% traffic, and that the served asset version
matches this commit. Capture 15-cloud-run-live.png from the public URL.

============================================================
PHASE 8 — REGRESSION
============================================================

    make test          # 634 passed, 1 skipped or better. Never fewer.
    ruff check . && ruff format --check .
    python evidence/browser/verify_mission_button.py            # 11/11
    python evidence/browser/verify_timemachine_and_media.py     # 33/33

All seven cards must still open and render. Then commit and push, and wait
for CI to go green. If CI fails, fix it and push again — do not stop at
local success. Run the suite with everything STAGED, because that is what CI
scans (git ls-files).

============================================================
PHASE 9 — THE BIGGEST REMAINING SCORE GAP
============================================================

Do this only if Phases 1-8 are complete and green. It is the single
highest-value improvement left, and it needs no credentials.

THE PROBLEM: this project is called "UNWIND — Consequence Clearing" and its
real engine (spine/) answers "which decisions rested on this claim?" — the
2,594 -> 78 cull. But command_os/ and fleet/ NEVER IMPORT spine/. The agent
layer decides authority without ever asking the question the product is
named after. A hostile judge will call it two products bolted together.

THE FIX: before an agent acts, ask UNWIND what the action would break.

  proposed action
    -> the claims it would change   (recon already extracts these)
    -> spine reverse index          (run_cascade — real, deterministic)
    -> dependent decisions          (the real blast radius)
    -> materiality regimes          (already computed)
    -> feeds the uncertainty tax in warrant/economics.py
    -> feeds the Gateway's decision

The join key already exists and already matches: the corpus claim
clm_000000 has canonical "supplier_K.lead_time_days", and
fleet/data/incident/premise-feed.json carries exactly that premise changing
11 -> 20. Verified: run_cascade on it returns radius 2594 across six regimes.

Show it as a CONSEQUENCE GRAPH in the Command OS. That single change makes
the product's name true of its flagship feature, unifies the architecture
into one story, and is pure deterministic arithmetic — no model, no
credentials, no new risk.

============================================================
FINAL REPORT — tell me exactly this
============================================================

For each of Gemini, Gemma, Veo, Lyria:
    MODEL ID | AUTH MODE | REAL CALL ATTEMPTED | REAL CALL SUCCEEDED |
    STATUS | ARTEFACT PRODUCED | LATENCY | EXACT BLOCKER if not live

Then:
    Credits spent (what actually ran)
    Tests: passed / failed / skipped
    CI: green or red
    Cloud Run revision + traffic + public URL
    Screenshots captured and embedded
    Git commit, and whether local HEAD == remote HEAD
    Anything still not working, stated plainly

Separate clearly: REAL SUCCESS vs CONFIGURED ONLY vs BLOCKED BY ACCESS vs
NOT TESTED. If you could not do something, say which one it is and why.
```

---

## What to expect

**Phase 2 costs almost nothing** — two calls of 32 output tokens. Run it
first and stop there if you want to confirm the setup cheaply.

**Phase 3 costs real credits.** One video, one audio clip. Only run it when
you actually want the artefacts.

**The most likely failure is `ACCESS_REQUIRED` on Gemma**, because
`gemma-3-27b-it` usually has to be deployed from Vertex Model Garden before
it can be called. That is a console action, not a code fix — and if it turns
out not to be available on your project, marking Gemma `ACCESS_REQUIRED`
with the real reason is the correct outcome, not a failure of the work.
