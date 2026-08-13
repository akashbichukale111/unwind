# Live verification — NOT YET RUN

**This file is a placeholder, and its presence with this heading means the
credentialed run has not happened.** `make verify-live` overwrites it entirely.
Nothing below is a measurement.

## Status: Branch B

Task 5 §5.0 defines three branches. **Branch B applies**: GCP credentials exist
on the maintainer's machine and have never existed in the build container where
this repository was written.

What that means precisely:

- The Vertex/ADK foundation gate **passed** — a real smoke test (Vertex request,
  Gemini tool call, `echo_tier(T0)`, final response, no 401/403/404) was run and
  reported by the maintainer on project `project-895d4ca8-d301-447d-916`,
  location `global`, model `gemini-3.5-flash-lite`.
- **No model call has ever been made from this repository.** Every T2 number in
  the repo came from `ScriptedT2Model` and is labelled as such wherever it
  appears.

## What is therefore unmeasured

| | Status |
| --- | --- |
| Parser-only recall | **81.8% measured** (`make coverage`) |
| Parser-only, worst class `temporal:absolute-duration` | **66.7% measured** |
| **Parser + Gemini recall** | **UNMEASURED** |
| **Delta by claim type** | **UNMEASURED** |
| T2 accuracy over the undecidable queue | UNMEASURED (orchestration only) |
| Model Armor blocking anything | UNMEASURED — not configured |
| Cloud Run deploy URL | **DOES NOT EXIST** — `infra/deploy.sh` never run |
| Firestore rules / composite indexes | Never deployed |

## To fill this file in

On a machine with credentials, from a clone of this repository:

```bash
make install

# Whichever of these matches your setup:
export UNWIND_PROJECT_ID=project-895d4ca8-d301-447d-916    # with gcloud ADC
# or
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
# or
export GOOGLE_APPLICATION_CREDENTIALS_JSON="$(cat /path/to/key.json)"

make verify-live
```

That single command makes one real Vertex call and prints the raw response, runs
the parser-only vs parser-plus-Gemini recall comparison over the same 64
artifacts and the same gold set, runs T2 over the undecidable queue, rewrites
this file with the results, and prints a JSON summary short enough to paste.

**It cannot silently degrade.** It exits non-zero with a specific reason if
credentials are absent (2), if Vertex is unreachable (3), or if it is pointed at
a stub (4) — and writes nothing on any of those paths. The recall comparison
refuses to score `ScriptedT2Model` even if the stub is relabelled with the real
production model id, because the check is on behaviour, not on the name.

## Method, for when the numbers arrive

- Pass 1 is the deterministic parser, called exactly as `judgment/coverage.py`
  calls it — not a second implementation that could disagree.
- Pass 2 shows Gemini **only the artifacts pass 1 missed**, and the prompt
  carries the artifact text and the field name. **It never carries the gold
  value.** A model shown the answer would score 100% and prove nothing;
  `tests/test_recall_compare.py` asserts the prompt does not contain it.
- A rescue counts only when the model's number matches gold within 0.001.
