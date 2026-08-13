# Live verification — RUN, 2026-08-13

⚠ **TRANSCRIPTION — the generated original supersedes this file.**

`make verify-live` GENERATES this file. The run happened on the maintainer's
authenticated Codespace, and the generator's output there is the authoritative
artifact: it carries the raw Vertex response verbatim, the per-rescue text
excerpts, and the exact `ran_at` timestamp. **This copy was written from the
observed console output** on a machine that had no credentials, so it reproduces
the numbers faithfully but not those three things.

**To replace this file with the real one**, from the Codespace:

```bash
git checkout <your-branch> -- .          # or just overwrite the file
cp /path/to/generated/LIVE-VERIFICATION.md docs/LIVE-VERIFICATION.md
# then re-append the "T2 ... a non-test" section below, which the
# generator does not produce
git commit -am "docs: restore generated LIVE-VERIFICATION.md"
```

Everything below is the observed run, plus a T2 diagnosis the generator does not
perform.

## Status: Branch B, executed

Credentials exist on the maintainer's GitHub Codespace and have never existed in
the build container where this repository was written. The run below happened on
the Codespace.

```bash
export UNWIND_PROJECT_ID=project-895d4ca8-d301-447d-916
export UNWIND_VERTEX_LOCATION=global
make verify-live
```

| | |
| --- | --- |
| Project | `project-895d4ca8-d301-447d-916` |
| Location | `global` |
| Model | `gemini-3.5-flash-lite` (GA) |
| Vertex call | **OK** |
| Model errors | **0** |

## The headline measurement

The deterministic parser handles the easy half **on purpose** — a regex has no
instruction-following surface for an injected instruction to attack. Gemini is
shown only the artifacts the parser could not read. This is the delta.

| | Recall |
| --- | --- |
| Parser only | **81.8%** |
| Parser + Gemini | **100.0%** |
| **Delta** | **+18.2 pp** |

Gold claims scored: **44**.

### By claim type

| Class | Gold | Parser | + Gemini | Delta |
| --- | ---: | ---: | ---: | ---: |
| `numeric:currency` | 4 | 100.0% | 100.0% | 0.0 |
| `numeric:percentage` | 4 | 100.0% | 100.0% | 0.0 |
| `numeric:quantity` | 8 | 100.0% | 100.0% | 0.0 |
| **`temporal:absolute-duration`** | **24** | **66.7%** | **100.0%** | **+33.3 pp** |
| `temporal:relative-date` | 4 | 100.0% | 100.0% | 0.0 |

Exactly one class moved, and it is the class the parser was already known to be
worst at (`docs/COVERAGE.md`, measured long before this run). The four classes
at 100% show a zero delta because nothing in them was ever sent to the model.

### How to read the 100%

**The model's denominator is 8, not 44.** The parser missed 8 claims; Gemini saw
those 8 and returned 8 correct values. The 100% figure describes the *combined
pipeline over 44 gold claims* — it is not a claim that the model extracts
perfectly. 44 claims is a small sample from a synthetic corpus; see
`docs/COVERAGE.md` for what that corpus does and does not represent.

## T2 over the undecidable queue — a non-test

| | |
| --- | --- |
| Queue size | 174 |
| Attempted | 60 |
| Resolved | **0** |
| Still unresolved | **60** |
| Exceptions | 0 |

**Zero resolved is neither success nor model failure. The sample could not have
resolved.**

Every one of the 174 queue nodes has `committed_lead_days = None` — verified
against the corpus, not assumed. These are the clause-governed conclusions whose
governing premise states a mechanism rather than a period.
`judgment/assessor.py` returns UNRESOLVED whenever the original commitment
carries no numeric term, and that branch executes **before the model's answer is
consulted**. So the outcome was fixed by the corpus, not decided by Gemini.

That the assessor declines here is arguably correct behaviour: there is genuinely
nothing to compare a re-derivation against. But correct behaviour and a
meaningful test are different things, and this run is the second, not the first.

**What the run does establish:** the T2 path executes end-to-end against a live
Vertex model with zero exceptions across 60 nodes — 120 model calls, one
re-derivation and one assessment each. The orchestration works. **Judgement
quality remains unmeasured.**

**What would close it:** a corpus fixture where the original commitment carries a
numeric term AND the premise is genuinely ambiguous, so the assessor reaches the
comparison branch and the model's answer decides the outcome. That fixture does
not exist yet.

## Method

- Pass 1 is the deterministic parser, called exactly as `judgment/coverage.py`
  calls it — not a second implementation that could disagree.
- Pass 2 sees **only the artifacts pass 1 missed**. Its prompt carries the
  artifact text and the field name and **never the gold value**;
  `tests/test_recall_compare.py` asserts the prompt does not contain it. A model
  shown the answer would score 100% and prove nothing.
- A rescue counts only when the model's number matches gold within 0.001.
- The comparison refuses to run against `ScriptedT2Model`, or against a stub
  relabelled with the real production model id — the check is on behaviour, not
  on the name. No number on this page can have come from a stub.

## Still not verified

| | |
| --- | --- |
| Cloud Run deployment | **Never run.** `infra/deploy.sh` exists; there is no URL. |
| Firestore rules / composite indexes | **Never deployed.** Files exist under `infra/`. |
| Model Armor | **Never configured.** Stays `[DESIGNED]`; the extraction quarantine is the real defence and is unaffected. |
| T2 judgement quality | See above. |
| Compensation-path synthesis | Deliberately `[DESIGNED]`; `synthesise()` raises. |
