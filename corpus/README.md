# The UNWIND corpus

**This data is synthetic.** It was produced entirely by `corpus/generate.py`. It
is not derived from, sampled from, anonymised from, or inspired by any real
company, supplier, contract, customer or transaction. Every name in it is
invented. No figure in it is a measurement of anything in the world.

It is committed to the repository, so a cold clone needs no generation step.

## What it is

One scenario, built completely: a supplier lead-time premise
(`supplier_K.lead_time_days = 11`) feeding quotes, purchase orders, an ad flight
and customer promises across six months of decisions.

| File | Contents |
| --- | --- |
| `data/claims.jsonl` | Every premise, including the hub claim `clm_000000` |
| `data/conclusions.jsonl` | Every decision, with its premise edge set |
| `data/reverse_index.jsonl` | Direct (one-hop) claim → conclusion edges |
| `data/radius_truth.jsonl` | **Eval ground truth**: the hub's transitive closure with true depths and materiality |
| `data/sources.jsonl` | Sources and their authority scopes |
| `data/adversarial/` | One forged retraction. Stored, never processed. |
| `data/stats.json` | Everything measured below |
| `data/MANIFEST.sha256` | Per-file digests; how determinism is proven |

`reverse_index.jsonl` holds **direct edges only**, every row at `depth: 1`. The
transitive closure is deliberately *not* precomputed into it — precomputing it
would let the demo skip the traversal it exists to demonstrate. The closure
lives in `radius_truth.jsonl` as eval ground truth, which is a different thing
serving a different purpose.

## How materiality is computed

Every conclusion in the radius committed some lead time downstream. Its buffer
against the physical supplier constraint is `committed_lead_days - 11`. The
retraction moves the premise 11 → 20, a shock of +9 days. So:

```
material  <=>  9 > (committed_lead_days - 11)  <=>  committed_lead_days < 20
```

That is arithmetic, which is why it is a T1 rule and needs no model.

`committed_lead_days` is drawn from a two-component mixture, because commitments
genuinely are two populations rather than one spread:

- **Tight** (5% of commitments) — expedited and just-in-time work, priced off the
  supplier's real lead time with days of margin. Safety factor `U(1.05, 1.85)`.
- **Loose** (95%) — standard commercial terms. Lognormal with median safety
  factor `30/11`, anchored on the "ships within 30 days" boilerplate that
  dominates enterprise terms.

**[ASSUMPTION]** The 5% tight share is the assumption that carries the whole
result. It rests on expedited orders being a small minority of enterprise order
volume, because they carry premium freight cost. Change it and the die-back
changes — that is the honest behaviour, and it is why the generator *reports*
the die-back rather than asserting a target for it.

**[ASSUMPTION]** Buffer is drawn independently of depth: an internal handoff is
modelled as adding no buffer of its own. This makes deep dependents no safer
than shallow ones, which is the conservative direction.

A commitment that already closed out — delivery made, quote expired, flight
ended — before the retraction cannot be harmed by it, whatever its buffer was.
So `live material` is the stricter and more useful count:
`material AND closes_at > retraction_date`. Both are reported, because
conflating them would overstate the demo.

## Measured properties

Produced by `make corpus`; reproduce with `make corpus-verify`. Every number
here is read out of `data/stats.json`, which the generator wrote.

| Property | Measured |
| --- | --- |
| Claims | 1,083 |
| Conclusions | 4,004 |
| Reverse-index edges | 9,989 |
| Sources | 10 |
| Hub claim direct dependents | 704 |
| Hub claim **transitive** dependents (the blast radius) | 2,004 |
| Max premise-chain depth | 5 |
| Radius scoreable arithmetically | 2,000 (4 are unresolvable) |
| Material by arithmetic | 94 |
| **Die-back** | **95.3 %** |
| Live material survivors | 55 |
| — not escaped | 30 |
| — escaped | 25 |
| Material but already closed out | 39 |
| Median decision → retraction gap | 91.5 days |
| Median escape → retraction gap | 34 days (range 3–117) |
| Deliberately UNRESOLVED conclusions | 4 |
| Adversarial artifacts | 1, unprocessed |

Depth histogram: 704 at depth 1, 700 at 2, 400 at 3, 150 at 4, 50 at 5.

### Where the measurements differ from the specification

Stated plainly rather than tuned away:

- **Die-back 95.3 % against a ≈96 % target.** Within "roughly", and it fell out
  of the mixture on the first run. Not adjusted.
- **55 live material survivors against a ~31 target.** Nearly double. The cause
  is that commercial validity windows (45–180 days) are long relative to the
  six-month corpus, so more commitments are still open at the retraction than
  the target assumes.
- **Escaped/not-escaped is 25/30, against a ~19/~12 target — the ratio is
  inverted.** The cause is the kind mix: internal `plan` and `approval`
  decisions rarely produce an external effect, and they are a sixth of the
  corpus each. Raising their escape probability would flip the ratio, but it
  would also be a fiction about how internal approvals behave.
- **Median escape → retraction is 34 days, not "months".** This is structural,
  not a parameter choice: a commitment can only be a live survivor if it is
  still open at the retraction, which biases survivors toward recent decisions.
  The tail does reach 117 days. "Escaped months ago *and* still open now"
  requires long horizons, and the two constraints pull against each other.

### What is assigned rather than emergent

Three conclusions in the escaped live-material set have their reversibility
**assigned deterministically**, so the demo is guaranteed one of each class
rather than depending on a lucky draw:

| Conclusion | Reversibility | Effect |
| --- | --- | --- |
| `cnc_000079` | idempotent | re-issuing the corrected quote converges |
| `cnc_001211` | compensable | ad flight, USD 41,800.00 partially creditable |
| `cnc_001983` | irreversible | expedite premium paid, USD 12,650.00, non-refundable |

Those two money figures are invented parameters of the synthetic scenario. They
are not estimates of anything.

## The adversarial artifact

`data/adversarial/forged_retraction.json` is an email from Zenith Freight
Brokerage asserting that Kestrel's lead time is now 34 days. Zenith holds
authority over `freight_broker_Z.` and nothing else; the hub claim's
`authority_scope` names only `src_supplier_K` and `src_msa_K`. It therefore has
no standing, and accepting it would cascade a mass unwind of 2,004 real
commitments off a forged input.

**It is stored and not processed.** It appears in no `.jsonl` file — not in
`claims.jsonl`, not in `conclusions.jsonl`, not in `reverse_index.jsonl`. Task 3
feeds it to the authority gate, which must refuse it deterministically.

## Determinism

`corpus/generate.py` uses a single seeded `random.Random(20260831)`, iterates in
sorted order throughout, and writes JSON with sorted keys. No wall-clock time is
read; every timestamp derives from a fixed window start.

```
make corpus-verify     # regenerates into a temp dir, diffs MANIFEST.sha256
```

Verified: the regenerated manifest is byte-identical to the committed one.
