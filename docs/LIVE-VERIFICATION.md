# Live verification

Produced by `make verify-live`. Every number below came from a real call to
Vertex AI; nothing here was produced by a stub.

- **Run at**: 2026-08-13T17:14:18.000937+00:00
- **Project**: `project-895d4ca8-d301-447d-916`
- **Model**: `gemini-3.5-flash-lite`

## The headline: what Gemini is actually for

The deterministic parser handles the easy half **on purpose** — a regex has no
instruction-following surface for an injected instruction to attack. Gemini is
shown only the artifacts the parser could not read. This table is the delta.

| | Recall |
| --- | --- |
| Parser only | **81.8%** |
| Parser + Gemini | **100.0%** |
| **Delta** | **+18.2 pp** |

Gold claims scored: **44**.

## By claim type

| Class | Gold | Parser | + Gemini | Delta | Model tried | Rescued | Wrong |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `numeric:currency` | 4 | 100.0% | 100.0% | +0.0 pp | 0 | 0 | 0 |
| `numeric:percentage` | 4 | 100.0% | 100.0% | +0.0 pp | 0 | 0 | 0 |
| `numeric:quantity` | 8 | 100.0% | 100.0% | +0.0 pp | 0 | 0 | 0 |
| `temporal:absolute-duration` | 24 | 66.7% | 100.0% | +33.3 pp | 8 | 8 | 0 |
| `temporal:relative-date` | 4 | 100.0% | 100.0% | +0.0 pp | 0 | 0 | 0 |

## What Gemini caught that the parser did not

- `temporal:absolute-duration` — gold `10.0`, model `10.0`
  > Typical turnaround is ten working days from release.
- `temporal:absolute-duration` — gold `12.0`, model `12.0`
  > Current cycle time sits at twelve days end to end.
- `temporal:absolute-duration` — gold `10.0`, model `10.0`
  > Typical turnaround is ten working days from release.
- `temporal:absolute-duration` — gold `12.0`, model `12.0`
  > Current cycle time sits at twelve days end to end.
- `temporal:absolute-duration` — gold `10.0`, model `10.0`
  > Typical turnaround is ten working days from release.
- `temporal:absolute-duration` — gold `12.0`, model `12.0`
  > Current cycle time sits at twelve days end to end.
- `temporal:absolute-duration` — gold `10.0`, model `10.0`
  > Typical turnaround is ten working days from release.
- `temporal:absolute-duration` — gold `12.0`, model `12.0`
  > Current cycle time sits at twelve days end to end.

## Method

- Pass 2 sees the artifact text and the field name. **It never sees the gold**
  **value.** A model shown the answer would score 100 % and prove nothing.
- A rescue counts only when the model's number matches gold within
  0.001. Close is not correct.
- The comparison refuses to run against `ScriptedT2Model` or an unavailable
  model, so no number on this page can have come from a stub.

## T2 over the undecidable queue

The nodes T1 could not decide arithmetically, run against the live model.

- Queue size: **174**
- Attempted (capped): **60**
- Resolved by the model: **0**
- Still UNRESOLVED: **60**

UNRESOLVED remaining is not a failure. The assessor under-reports by design:
a thin margin returns UNRESOLVED rather than escalating, because an obligation
an owner rejects burns the attention the real ones need.

## The raw Vertex response

One real call, pasted verbatim. This is the artifact that proves the
mandatory Gemini-via-Vertex requirement is satisfied by running code.

```
Just as cache invalidation requires clearing outdated data when the underlying system changes, decisions based on facts must be actively revisited and revised whenever those underlying facts no longer hold true.
```

Model `gemini-3.5-flash-lite`, project `project-895d4ca8-d301-447d-916`, location `global`.

### Why Flash and not Pro

As of 2026-08-12 no Gemini 3.x **Pro** model is GA -- the 3.x Pro line is
preview only. Both models this repository uses are GA, which is a deliberate
choice for live-demo reliability: a preview model can change or throttle
underneath a demo, and the delta above does not need Pro to be persuasive.
