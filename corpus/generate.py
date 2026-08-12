"""Deterministic, seeded generator for the UNWIND demonstration corpus.

THE DATA THIS PRODUCES IS SYNTHETIC. It is not derived from any real company,
supplier, contract or transaction. See corpus/README.md.

WHY THIS IS A DELIVERABLE AND NOT A FIXTURE
-------------------------------------------
UNWIND's central claim is that when one premise dies, the overwhelming majority
of what was built on it is genuinely unharmed, and a small, findable minority is
not. If the die-back were stipulated rather than computed, the demo would be a
puppet show. So the corpus is built from a stated model of commercial behaviour,
and the die-back is then MEASURED off that model. The generator asserts only
structural invariants; it does not assert the die-back percentage, because an
assertion on that number would be an invitation to tune the model until it
passed.

THE MODEL OF MATERIALITY (this is the whole argument, so read it)
----------------------------------------------------------------
The hub premise is `supplier_K.lead_time_days = 11`. Every conclusion in its
blast radius committed some lead time downstream -- a quote promising delivery,
a purchase order with a dock date, an ad flight timed to arrival. Call that
`committed_lead_days`. The buffer that commitment holds against the physical
supplier constraint is

    slack_days = committed_lead_days - 11

When the premise moves 11 -> 20, the shock is +9 days. The commitment is harmed
if and only if the shock exceeds the buffer:

    material  <=>  9 > slack_days  <=>  committed_lead_days < 20

That is arithmetic. It needs no model, which is exactly why it is T1.

WHERE THE BUFFER DISTRIBUTION COMES FROM
----------------------------------------
Commitments are modelled as a two-component mixture, because in procurement they
genuinely are two populations rather than one spread:

  TIGHT  (share = 0.05)  Expedited and just-in-time commitments, priced off the
                         supplier's actual lead time with days of margin. The
                         0.05 share is the assumption that carries the result:
                         expedited orders are a small minority of enterprise
                         order volume because they carry premium freight cost.
                         Safety factor ~ Uniform(1.05, 1.85) on 11 days -> 12-20.

  LOOSE  (share = 0.95)  Standard commercial terms. Median safety factor is
                         30/11, anchored on the "ships within 30 days" boilerplate
                         that dominates enterprise terms; lognormal because
                         buffers compound multiplicatively and skew right.

[ASSUMPTION] Both the 0.05 tight share and the 30-day median term are modelling
choices, stated here so a reader can disagree with the number rather than with
the result. Change them and the die-back changes; that is the honest behaviour.

[ASSUMPTION] Buffer is drawn independently of depth: an internal handoff is
modelled as adding no buffer of its own. This makes deep dependents no safer
than shallow ones, which is the conservative direction.

MATERIAL IS NOT THE SAME AS ACTIONABLE
--------------------------------------
A commitment that already closed out -- delivery made, quote expired, flight
ended -- before the retraction cannot be harmed by the retraction, however tight
its buffer was. So the survivors that matter are

    live material  <=>  material AND closes_at > retraction_date

Both numbers are reported separately, because they answer different questions
and conflating them would overstate the demo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Locked generation parameters. Changing any of these changes the corpus.
# ---------------------------------------------------------------------------

SEED = 20260831

WINDOW_START = datetime(2026, 1, 5, 9, 0, tzinfo=UTC)
WINDOW_DAYS = 182  # six months
RETRACTION_AT = WINDOW_START + timedelta(days=WINDOW_DAYS)

HUB_CANONICAL = "supplier_K.lead_time_days"
HUB_VALUE_OLD = 11
HUB_VALUE_NEW = 20
SHOCK_DAYS = HUB_VALUE_NEW - HUB_VALUE_OLD  # +9

TIGHT_SHARE = 0.05
TIGHT_FACTOR_LOW = 1.05
TIGHT_FACTOR_HIGH = 1.85
LOOSE_MEDIAN_TERM_DAYS = 30.0
LOOSE_SIGMA = 0.35
LOOSE_FACTOR_FLOOR = 1.9

# Radius shape: (conclusions at this depth, how many of them emit a derived claim)
RADIUS_LEVELS: tuple[tuple[int, int], ...] = (
    (700, 60),
    (700, 40),
    (400, 20),
    (150, 8),
    (50, 0),
)
UNRELATED_CONCLUSIONS = 1580
UNRELATED_CLAIM_TARGET = 950

# ---------------------------------------------------------------------------
# LONG-DATED INSTRUMENTS
# ---------------------------------------------------------------------------
# Added because the first corpus produced survivors whose external effects had
# escaped a median of 34 days before the retraction, not months. That was
# structural, not a parameter: a commitment only survives if it is still open at
# the retraction, which biases survivors toward recent decisions when every
# instrument has a 45-180 day validity window.
#
# The fix is a distinct class of instrument that is genuinely long-dated in the
# real world, rather than a widened horizon on everything:
#
#   standing_price     an annual price list, valid 300-400 days
#   framework_promise  a service level under a framework agreement, 240-365 days
#   long_lead_order    a purchase order with a long delivery horizon, 180-300
#
# [ASSUMPTION] Price lists and framework agreements are set at PERIOD
# BOUNDARIES, not uniformly through the year -- an annual list is issued in
# January, a framework renewed on its anniversary. They are therefore dated to
# quarter starts within the window. This is the assumption that produces the
# long decision-to-retraction gaps, and it is a real feature of how these
# instruments are issued, not a knob.
#
# [ASSUMPTION] Their tight/loose buffer mixture is UNCHANGED at 0.05. It would
# have been easy to argue that a negotiated framework service level is set from
# the actual lead time rather than a padded default, which would have made these
# instruments materially exposed far more often and produced a much better demo.
# That argument is plausible but not clearly true, so it is not used. Long-dated
# instruments here are distinguished by their DURATION only.
LONG_DATED_KINDS = ("standing_price", "framework_promise", "long_lead_order")
LONG_DATED_COUNTS: dict[str, int] = {
    "standing_price": 130,
    "framework_promise": 150,
    "long_lead_order": 140,
}
#: Quarter starts, as day offsets into the window. Price lists and framework
#: agreements land on these; long-lead orders are placed whenever they are needed.
PERIOD_BOUNDARY_DAYS = (0, 91)

EXTRACTOR_AGENT = "premise-extractor@0.1.0"

KIND_HORIZON_DAYS: dict[str, tuple[int, int]] = {
    # Commercial validity / fulfilment window, independent of committed lead time.
    "quote": (45, 120),
    "order": (30, 150),
    "plan": (90, 180),
    "promise": (60, 180),
    "approval": (60, 180),
    "price": (30, 120),
    "standing_price": (300, 400),
    "framework_promise": (240, 365),
    "long_lead_order": (180, 300),
}
KIND_ESCAPE_PROB: dict[str, float] = {
    # Whether the decision produced an effect outside the company at all.
    "quote": 0.80,
    "order": 0.90,
    "promise": 0.85,
    "price": 0.55,
    "plan": 0.15,
    "approval": 0.10,
    # Long-dated instruments are published or countersigned almost by definition:
    # a price list nobody received is not a price list.
    "standing_price": 0.92,
    "framework_promise": 0.90,
    "long_lead_order": 0.95,
}
RADIUS_KINDS = ("quote", "order", "plan", "promise", "approval", "price")

UNRESOLVED_COUNT = 4


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass
class Gen:
    rng: random.Random

    # ---- sources -------------------------------------------------------
    def sources(self) -> list[dict[str, Any]]:
        rows = [
            ("src_supplier_K", "Kestrel Components GmbH", "supplier_email", 0.72, ["supplier_K."]),
            ("src_supplier_L", "Lyric Fabrication Ltd", "supplier_email", 0.81, ["supplier_L."]),
            ("src_supplier_M", "Meridian Castings SA", "vendor_pdf", 0.66, ["supplier_M."]),
            (
                "src_erp_internal",
                "Internal ERP replication feed",
                "erp_feed",
                0.93,
                ["inventory.", "capacity.", "internal."],
            ),
            (
                "src_msa_K",
                "Master supply agreement, Kestrel",
                "contract",
                0.88,
                ["contract.supplier_K."],
            ),
            (
                "src_msa_L",
                "Master supply agreement, Lyric",
                "contract",
                0.88,
                ["contract.supplier_L."],
            ),
            (
                "src_tariff_bulletin",
                "Customs tariff bulletin",
                "regulatory_bulletin",
                0.90,
                ["tariff.", "duty."],
            ),
            ("src_fx_desk", "Treasury FX desk", "internal_system", 0.85, ["fx."]),
            (
                "src_logistics_ops",
                "Logistics operations system",
                "internal_system",
                0.87,
                ["freight.transit.", "dock."],
            ),
            # The adversary. Its authority covers its own transit times and
            # nothing else -- which is precisely what the forged email violates.
            (
                "src_broker_Z",
                "Zenith Freight Brokerage",
                "broker_email",
                0.41,
                ["freight_broker_Z."],
            ),
        ]
        return [
            {
                "source_id": sid,
                "name": name,
                "kind": kind,
                "load_rating": rating,
                "falsification_history": [],
                "authority": authority,
            }
            for sid, name, kind, rating, authority in rows
        ]

    # ---- claim construction -------------------------------------------
    def make_claim(
        self,
        claim_id: str,
        canonical: str,
        claim_type: str,
        value: Any,
        unit: str | None,
        source_id: str,
        authority_scope: list[str],
        valid_from: datetime,
        predicate: dict[str, Any],
        confidence: float,
    ) -> dict[str, Any]:
        return {
            "claim_id": claim_id,
            "type": claim_type,
            "canonical": canonical,
            "value": value,
            "unit": unit,
            "source_id": source_id,
            "confidence": round(confidence, 3),
            "falsified_when": predicate,
            "extracted_by": EXTRACTOR_AGENT,
            "extracted_at": _iso(valid_from + timedelta(hours=3)),
            "valid_from": _iso(valid_from),
            # Temporal Truth: the corpus is the world BEFORE the retraction.
            # Nothing is invalidated yet. Task 2 sets these when the hub dies.
            "invalidated_at": None,
            "invalidation_reason": None,
            "authority_scope": authority_scope,
            "status": "live",
            "load_weight": 0,
        }

    def numeric_predicate(self, threshold: float, unit: str | None) -> dict[str, Any]:
        return {
            "op": "neq",
            "field": "value",
            "threshold": threshold,
            "unit": unit,
            "unresolvable_reason": None,
        }

    def unresolvable_predicate(self, reason: str) -> dict[str, Any]:
        return {
            "op": "unparseable",
            "field": "value",
            "threshold": None,
            "unit": None,
            "unresolvable_reason": reason,
        }

    # ---- the buffer model ---------------------------------------------
    def committed_lead_days(self) -> tuple[int, str]:
        """Draw a downstream committed lead time. Returns (days, tier)."""
        if self.rng.random() < TIGHT_SHARE:
            factor = self.rng.uniform(TIGHT_FACTOR_LOW, TIGHT_FACTOR_HIGH)
            return max(12, round(HUB_VALUE_OLD * factor)), "tight"
        mu = math.log(LOOSE_MEDIAN_TERM_DAYS / HUB_VALUE_OLD)
        for _ in range(64):
            factor = self.rng.lognormvariate(mu, LOOSE_SIGMA)
            if factor >= LOOSE_FACTOR_FLOOR:
                return round(HUB_VALUE_OLD * factor), "loose"
        return round(HUB_VALUE_OLD * LOOSE_FACTOR_FLOOR), "loose"


def build(seed: int = SEED) -> dict[str, Any]:
    rng = random.Random(seed)
    g = Gen(rng=rng)

    sources = g.sources()
    claims: list[dict[str, Any]] = []
    conclusions: list[dict[str, Any]] = []

    # -- the hub premise -------------------------------------------------
    hub_id = "clm_000000"
    claims.append(
        g.make_claim(
            claim_id=hub_id,
            canonical=HUB_CANONICAL,
            claim_type="NUMERIC",
            value=HUB_VALUE_OLD,
            unit="days",
            source_id="src_supplier_K",
            # Only Kestrel, and the contract that binds Kestrel, may move this.
            authority_scope=["src_supplier_K", "src_msa_K"],
            valid_from=WINDOW_START - timedelta(days=21),
            predicate=g.numeric_predicate(float(HUB_VALUE_OLD), "days"),
            confidence=0.91,
        )
    )

    claim_seq = 1
    conclusion_seq = 0

    def next_claim_id() -> str:
        nonlocal claim_seq
        cid = f"clm_{claim_seq:06d}"
        claim_seq += 1
        return cid

    def next_conclusion_id() -> str:
        nonlocal conclusion_seq
        cid = f"cnc_{conclusion_seq:06d}"
        conclusion_seq += 1
        return cid

    # -- ambient claims: real premises that are NOT the hub ---------------
    # These exist so that conclusions are genuinely multi-premise and so the
    # reverse-index traversal has to be selective rather than trivially total.
    ambient_ids: list[str] = []
    ambient_specs = [
        (
            "tariff.hs_8536.rate_pct",
            "REGULATORY",
            "src_tariff_bulletin",
            ["src_tariff_bulletin"],
            "pct",
        ),
        ("fx.eur_usd.rate", "NUMERIC", "src_fx_desk", ["src_fx_desk"], "ratio"),
        (
            "freight.transit.hamburg_chicago_days",
            "TEMPORAL",
            "src_logistics_ops",
            ["src_logistics_ops"],
            "days",
        ),
        (
            "capacity.line_3.units_per_week",
            "NUMERIC",
            "src_erp_internal",
            ["src_erp_internal"],
            "units",
        ),
        (
            "supplier_L.lead_time_days",
            "NUMERIC",
            "src_supplier_L",
            ["src_supplier_L", "src_msa_L"],
            "days",
        ),
        ("supplier_M.lead_time_days", "NUMERIC", "src_supplier_M", ["src_supplier_M"], "days"),
        (
            "inventory.sku_44812.on_hand",
            "NUMERIC",
            "src_erp_internal",
            ["src_erp_internal"],
            "units",
        ),
        (
            "contract.supplier_K.penalty_per_day_usd",
            "CONTRACTUAL",
            "src_msa_K",
            ["src_msa_K"],
            "usd",
        ),
        (
            "freight_broker_Z.consolidation_days",
            "TEMPORAL",
            "src_broker_Z",
            ["src_broker_Z"],
            "days",
        ),
        (
            "dock.receiving_window_days",
            "TEMPORAL",
            "src_logistics_ops",
            ["src_logistics_ops"],
            "days",
        ),
    ]
    while len(ambient_ids) < UNRELATED_CLAIM_TARGET:
        canonical, ctype, src, scope, unit = ambient_specs[len(ambient_ids) % len(ambient_specs)]
        variant = len(ambient_ids) // len(ambient_specs)
        cid = next_claim_id()
        value = round(rng.uniform(2, 60), 2)
        claims.append(
            g.make_claim(
                claim_id=cid,
                canonical=f"{canonical}#{variant:03d}" if variant else canonical,
                claim_type=ctype,
                value=value,
                unit=unit,
                source_id=src,
                authority_scope=scope,
                valid_from=WINDOW_START + timedelta(days=rng.randrange(0, WINDOW_DAYS)),
                predicate=g.numeric_predicate(value, unit),
                confidence=round(rng.uniform(0.6, 0.97), 3),
            )
        )
        ambient_ids.append(cid)

    # -- the deliberately ambiguous premises ------------------------------
    # A contract clause with no machine-checkable value. Anything resting on one
    # of these CANNOT be scored arithmetically, and is displayed as UNRESOLVED
    # rather than defaulted to safe (locked decision 1.6).
    ambiguous_claim_ids: list[str] = []
    for i in range(UNRESOLVED_COUNT):
        cid = next_claim_id()
        claims.append(
            g.make_claim(
                claim_id=cid,
                canonical=f"contract.supplier_K.delivery_terms_clause_{7 + i}",
                claim_type="CONTRACTUAL",
                value="lead time as mutually agreed between the parties from time to time",
                unit=None,
                source_id="src_msa_K",
                authority_scope=["src_msa_K"],
                valid_from=WINDOW_START - timedelta(days=14),
                predicate=g.unresolvable_predicate(
                    "Clause states no numeric lead time; 'as mutually agreed from time "
                    "to time' has no machine-checkable value. Materiality cannot be "
                    "computed arithmetically."
                ),
                confidence=0.55,
            )
        )
        ambiguous_claim_ids.append(cid)

    # -- the blast radius, built level by level ---------------------------
    # Level 1 hangs off the hub. Some conclusions at each level emit a derived
    # claim, which the next level depends on -- so the radius is genuinely
    # transitive rather than a star.
    parent_claim_ids = [hub_id]
    radius_conclusion_ids: list[str] = []
    emitted_claim_ids: list[str] = []

    for level_index, (count, emitters) in enumerate(RADIUS_LEVELS, start=1):
        level_conclusion_ids: list[str] = []
        for i in range(count):
            cid = next_conclusion_id()
            kind = RADIUS_KINDS[rng.randrange(len(RADIUS_KINDS))]
            decided_at = WINDOW_START + timedelta(
                days=rng.randrange(0, WINDOW_DAYS), hours=rng.randrange(0, 9)
            )
            committed, tier = g.committed_lead_days()
            horizon_low, horizon_high = KIND_HORIZON_DAYS[kind]
            closes_at = decided_at + timedelta(days=rng.randrange(horizon_low, horizon_high))

            premise_ids = [parent_claim_ids[i % len(parent_claim_ids)]]
            for _ in range(rng.randrange(1, 4)):
                premise_ids.append(ambient_ids[rng.randrange(len(ambient_ids))])

            conclusions.append(
                {
                    "conclusion_id": cid,
                    "kind": kind,
                    "body": _body(kind, committed, decided_at),
                    "decided_at": _iso(decided_at),
                    "owner_principal": f"principal_{rng.randrange(1, 24):02d}",
                    "premise_ids": sorted(set(premise_ids)),
                    "external_effects": [],
                    "status": "live",
                    "committed_lead_days": committed,
                    "closes_at": _iso(closes_at),
                    "emits_claim_id": None,
                    # Generator-only bookkeeping, stripped before writing.
                    "_tier": tier,
                    "_depth": level_index,
                    "_decided_at": decided_at,
                    "_closes_at": closes_at,
                }
            )
            level_conclusion_ids.append(cid)
            radius_conclusion_ids.append(cid)

        # Promote some of this level's conclusions into premises for the next.
        next_parents: list[str] = []
        for j in range(emitters):
            conclusion_id = level_conclusion_ids[
                (j * max(1, len(level_conclusion_ids) // max(1, emitters)))
                % len(level_conclusion_ids)
            ]
            record = next(c for c in conclusions if c["conclusion_id"] == conclusion_id)
            if record["emits_claim_id"] is not None:
                continue
            derived_id = next_claim_id()
            claims.append(
                g.make_claim(
                    claim_id=derived_id,
                    canonical=f"derived.plan_{derived_id}.eta_days",
                    claim_type="TEMPORAL",
                    value=record["committed_lead_days"],
                    unit="days",
                    source_id="src_erp_internal",
                    authority_scope=["src_erp_internal"],
                    valid_from=record["_decided_at"] + timedelta(hours=6),
                    predicate=g.numeric_predicate(float(record["committed_lead_days"]), "days"),
                    confidence=0.79,
                )
            )
            record["emits_claim_id"] = derived_id
            emitted_claim_ids.append(derived_id)
            next_parents.append(derived_id)

        if not next_parents:
            break
        parent_claim_ids = next_parents

    # -- long-dated instruments -------------------------------------------
    # These hang off the hub claim and off derived claims, so they are inside the
    # radius. Their point is the TEMPORAL GAP: a price list published in January
    # on an 11-day replenishment assumption is still governing in July, months
    # after it was decided and long after its effect left the building.
    long_dated_ids: list[str] = []
    hub_and_derived = [hub_id, *emitted_claim_ids[:64]]
    for kind in LONG_DATED_KINDS:
        for i in range(LONG_DATED_COUNTS[kind]):
            cid = next_conclusion_id()
            if kind == "long_lead_order":
                # Placed when they are needed, so dated uniformly.
                decided_at = WINDOW_START + timedelta(
                    days=rng.randrange(0, WINDOW_DAYS), hours=rng.randrange(0, 9)
                )
            else:
                # Issued at a period boundary, which is what makes the gap long.
                boundary = PERIOD_BOUNDARY_DAYS[i % len(PERIOD_BOUNDARY_DAYS)]
                decided_at = WINDOW_START + timedelta(days=boundary, hours=rng.randrange(0, 9))
            committed, tier = g.committed_lead_days()
            horizon_low, horizon_high = KIND_HORIZON_DAYS[kind]
            closes_at = decided_at + timedelta(days=rng.randrange(horizon_low, horizon_high))

            premise_ids = [hub_and_derived[i % len(hub_and_derived)]]
            for _ in range(rng.randrange(1, 3)):
                premise_ids.append(ambient_ids[rng.randrange(len(ambient_ids))])

            conclusions.append(
                {
                    "conclusion_id": cid,
                    "kind": kind,
                    "body": _body(kind, committed, decided_at),
                    "decided_at": _iso(decided_at),
                    "owner_principal": f"principal_{rng.randrange(1, 24):02d}",
                    "premise_ids": sorted(set(premise_ids)),
                    "external_effects": [],
                    "status": "live",
                    "committed_lead_days": committed,
                    "closes_at": _iso(closes_at),
                    "emits_claim_id": None,
                    "_tier": tier,
                    "_depth": 1,
                    "_decided_at": decided_at,
                    "_closes_at": closes_at,
                }
            )
            radius_conclusion_ids.append(cid)
            long_dated_ids.append(cid)

    # -- the deliberately unresolvable conclusions ------------------------
    # Each sits inside the radius (it cites the hub) AND cites a clause with no
    # machine-checkable value, so the cascade will reach it and then be unable
    # to score it. That is the point.
    unresolved_conclusion_ids: list[str] = []
    for i, ambiguous_id in enumerate(ambiguous_claim_ids):
        cid = next_conclusion_id()
        decided_at = WINDOW_START + timedelta(days=30 + i * 27)
        closes_at = RETRACTION_AT + timedelta(days=45 + i * 11)
        conclusions.append(
            {
                "conclusion_id": cid,
                "kind": "promise",
                "body": (
                    "Standing delivery commitment to a named account, governed by a "
                    "contract clause that states no numeric lead time. The committed "
                    "lead time is not recoverable from the premise set."
                ),
                "decided_at": _iso(decided_at),
                "owner_principal": f"principal_{7 + i:02d}",
                "premise_ids": sorted({hub_id, ambiguous_id, ambient_ids[i * 13]}),
                "external_effects": [
                    {
                        "connector": "email",
                        "op": "send_commitment_letter",
                        "ref": f"msg-unres-{i:03d}",
                        "reversibility": "unknown",
                        "occurred_at": _iso(decided_at + timedelta(days=1)),
                        "amount_minor": None,
                        "currency": None,
                    }
                ],
                # First-class, from the moment the corpus is written.
                "status": "unresolved",
                "committed_lead_days": None,
                "closes_at": _iso(closes_at),
                "emits_claim_id": None,
                "_tier": "unresolvable",
                "_depth": 1,
                "_decided_at": decided_at,
                "_closes_at": closes_at,
            }
        )
        radius_conclusion_ids.append(cid)
        unresolved_conclusion_ids.append(cid)

    # -- conclusions outside the radius -----------------------------------
    for _ in range(UNRELATED_CONCLUSIONS):
        cid = next_conclusion_id()
        kind = RADIUS_KINDS[rng.randrange(len(RADIUS_KINDS))]
        decided_at = WINDOW_START + timedelta(
            days=rng.randrange(0, WINDOW_DAYS), hours=rng.randrange(0, 9)
        )
        horizon_low, horizon_high = KIND_HORIZON_DAYS[kind]
        committed, tier = g.committed_lead_days()
        premise_ids = sorted(
            {ambient_ids[rng.randrange(len(ambient_ids))] for _ in range(rng.randrange(1, 4))}
        )
        conclusions.append(
            {
                "conclusion_id": cid,
                "kind": kind,
                "body": _body(kind, committed, decided_at),
                "decided_at": _iso(decided_at),
                "owner_principal": f"principal_{rng.randrange(1, 24):02d}",
                "premise_ids": premise_ids,
                "external_effects": [],
                "status": "live",
                "committed_lead_days": committed,
                "closes_at": _iso(
                    decided_at + timedelta(days=rng.randrange(horizon_low, horizon_high))
                ),
                "emits_claim_id": None,
                "_tier": tier,
                "_depth": 0,
                "_decided_at": decided_at,
                "_closes_at": decided_at + timedelta(days=rng.randrange(horizon_low, horizon_high)),
            }
        )

    by_id = {c["conclusion_id"]: c for c in conclusions}

    # -- escapement -------------------------------------------------------
    # A decision escaped if it produced an effect outside the company. Effects
    # land a few days after the decision, so escape dates inherit the six-month
    # spread of decided_at -- most of them are months before the retraction.
    for conclusion in conclusions:
        if conclusion["external_effects"]:
            continue
        if rng.random() >= KIND_ESCAPE_PROB[conclusion["kind"]]:
            continue
        occurred = conclusion["_decided_at"] + timedelta(days=rng.randrange(0, 5))
        if occurred > RETRACTION_AT:
            continue
        connector, op = _effect_for_kind(conclusion["kind"])
        conclusion["external_effects"].append(
            {
                "connector": connector,
                "op": op,
                "ref": f"{connector}-{conclusion['conclusion_id'][4:]}",
                # Default reversibility; the three demonstrative cases below are
                # assigned deterministically afterwards.
                "reversibility": "idempotent",
                "occurred_at": _iso(occurred),
                "amount_minor": None,
                "currency": None,
            }
        )

    # -- ground truth: the transitive radius of the hub --------------------
    dependents_of_claim: dict[str, list[str]] = defaultdict(list)
    for conclusion in conclusions:
        for premise_id in conclusion["premise_ids"]:
            dependents_of_claim[premise_id].append(conclusion["conclusion_id"])

    radius_depth: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque([(hub_id, 0)])
    seen_claims = {hub_id}
    while queue:
        claim_id, depth = queue.popleft()
        for conclusion_id in sorted(dependents_of_claim.get(claim_id, [])):
            if conclusion_id in radius_depth:
                continue
            radius_depth[conclusion_id] = depth + 1
            emitted = by_id[conclusion_id]["emits_claim_id"]
            if emitted and emitted not in seen_claims:
                seen_claims.add(emitted)
                queue.append((emitted, depth + 1))

    # -- materiality, computed, not stipulated -----------------------------
    material_ids: list[str] = []
    live_material_ids: list[str] = []
    unresolvable_in_radius: list[str] = []
    for conclusion_id in sorted(radius_depth):
        conclusion = by_id[conclusion_id]
        committed = conclusion["committed_lead_days"]
        if committed is None:
            unresolvable_in_radius.append(conclusion_id)
            continue
        slack = committed - HUB_VALUE_OLD
        if SHOCK_DAYS > slack:
            material_ids.append(conclusion_id)
            if conclusion["_closes_at"] > RETRACTION_AT:
                live_material_ids.append(conclusion_id)

    # -- the three demonstrative reversibility cases -----------------------
    # Chosen deterministically from the escaped live-material set rather than
    # left to chance, so the demo is guaranteed to have one of each. Stated
    # plainly in corpus/README.md; nothing here is disguised as emergent.
    escaped_live_material = [cid for cid in live_material_ids if by_id[cid]["external_effects"]]
    demonstrative: dict[str, str] = {}
    if len(escaped_live_material) >= 3:
        idempotent_id = escaped_live_material[0]
        compensable_id = escaped_live_material[len(escaped_live_material) // 2]
        irreversible_id = escaped_live_material[-1]

        by_id[idempotent_id]["external_effects"][0].update(
            {"connector": "email", "op": "send_quote", "reversibility": "idempotent"}
        )
        by_id[compensable_id]["external_effects"][0].update(
            {
                "connector": "ads",
                "op": "launch_flight",
                "reversibility": "compensable",
                "amount_minor": 4_180_000,  # USD 41,800.00
                "currency": "USD",
            }
        )
        by_id[irreversible_id]["external_effects"][0].update(
            {
                "connector": "payments",
                "op": "pay_expedite_premium",
                "reversibility": "irreversible",
                "amount_minor": 1_265_000,  # USD 12,650.00, non-refundable
                "currency": "USD",
            }
        )
        demonstrative = {
            "idempotent": idempotent_id,
            "compensable": compensable_id,
            "irreversible": irreversible_id,
        }

    # -- reverse index: DIRECT edges only ---------------------------------
    # Depth is 1 for every row because this is the runtime structure T0 walks
    # one hop at a time. The transitive closure is ground truth for evals and
    # lives in radius_truth.jsonl -- precomputing it here would let the demo
    # skip the traversal it exists to demonstrate.
    reverse_index: list[dict[str, Any]] = []
    for claim_id in sorted(dependents_of_claim):
        for conclusion_id in sorted(dependents_of_claim[claim_id]):
            conclusion = by_id[conclusion_id]
            reverse_index.append(
                {
                    "claim_id": claim_id,
                    "conclusion_id": conclusion_id,
                    "depth": 1,
                    "weight": round(
                        1.0
                        + (0.5 if conclusion["external_effects"] else 0.0)
                        + (0.5 if conclusion["emits_claim_id"] else 0.0),
                        3,
                    ),
                }
            )

    for claim in claims:
        claim["load_weight"] = len(dependents_of_claim.get(claim["claim_id"], []))

    radius_truth = [
        {
            "conclusion_id": cid,
            "depth": radius_depth[cid],
            "committed_lead_days": by_id[cid]["committed_lead_days"],
            "slack_days": (
                by_id[cid]["committed_lead_days"] - HUB_VALUE_OLD
                if by_id[cid]["committed_lead_days"] is not None
                else None
            ),
            "material": cid in set(material_ids),
            "live_material": cid in set(live_material_ids),
            "escaped": bool(by_id[cid]["external_effects"]),
            "unresolvable": by_id[cid]["committed_lead_days"] is None,
        }
        for cid in sorted(radius_depth)
    ]

    # -- statistics --------------------------------------------------------
    radius_size = len(radius_depth)
    scoreable = radius_size - len(unresolvable_in_radius)
    material_count = len(material_ids)
    die_back_pct = 100.0 * (scoreable - material_count) / scoreable if scoreable else 0.0

    escaped_live = [cid for cid in live_material_ids if by_id[cid]["external_effects"]]
    contained_live = [cid for cid in live_material_ids if not by_id[cid]["external_effects"]]

    escape_gaps_days = sorted(
        (
            RETRACTION_AT
            - datetime.fromisoformat(
                by_id[cid]["external_effects"][0]["occurred_at"].replace("Z", "+00:00")
            )
        ).days
        for cid in escaped_live
    )
    decision_gaps_days = sorted(
        (RETRACTION_AT - by_id[cid]["_decided_at"]).days for cid in sorted(radius_depth)
    )

    # The gap that carries the product's argument: how long a decision had been
    # standing, and its effect had been out in the world, before the premise died.
    survivor_decision_gaps = sorted(
        (RETRACTION_AT - by_id[cid]["_decided_at"]).days for cid in escaped_live
    )
    long_dated_set = set(long_dated_ids)
    stale_survivors = [
        cid for cid in escaped_live if (RETRACTION_AT - by_id[cid]["_decided_at"]).days >= 120
    ]

    stats = {
        "seed": seed,
        "generated_window": {
            "start": _iso(WINDOW_START),
            "days": WINDOW_DAYS,
            "retraction_at": _iso(RETRACTION_AT),
        },
        "hub_claim": {
            "claim_id": hub_id,
            "canonical": HUB_CANONICAL,
            "value_before": HUB_VALUE_OLD,
            "value_after": HUB_VALUE_NEW,
            "shock_days": SHOCK_DAYS,
            "direct_dependents": len(dependents_of_claim.get(hub_id, [])),
            "transitive_dependents": radius_size,
        },
        "counts": {
            "claims": len(claims),
            "conclusions": len(conclusions),
            "reverse_index_edges": len(reverse_index),
            "sources": len(sources),
            "derived_claims": len(emitted_claim_ids),
        },
        "die_back": {
            "radius": radius_size,
            "unscoreable_unresolved": len(unresolvable_in_radius),
            "scoreable": scoreable,
            "material_by_arithmetic": material_count,
            "immaterial_by_arithmetic": scoreable - material_count,
            "die_back_pct": round(die_back_pct, 3),
            "rule": "material <=> shock_days > (committed_lead_days - hub_value)",
        },
        "survivors": {
            "live_material": len(live_material_ids),
            "not_escaped": len(contained_live),
            "escaped": len(escaped_live),
            "already_closed_material": material_count - len(live_material_ids),
        },
        "timing": {
            "median_decision_to_retraction_days": _median(decision_gaps_days),
            "median_escape_to_retraction_days": _median(escape_gaps_days),
            "min_escape_to_retraction_days": escape_gaps_days[0] if escape_gaps_days else None,
            "max_escape_to_retraction_days": escape_gaps_days[-1] if escape_gaps_days else None,
        },
        # The temporal gap, measured over the escaped survivors only -- the
        # population the demo actually shows.
        "temporal_gap": {
            "escaped_survivors": len(escaped_live),
            "median_decision_to_retraction_days": _median(survivor_decision_gaps),
            "min_decision_to_retraction_days": (
                survivor_decision_gaps[0] if survivor_decision_gaps else None
            ),
            "max_decision_to_retraction_days": (
                survivor_decision_gaps[-1] if survivor_decision_gaps else None
            ),
            "survivors_decided_120d_or_more_before": len(stale_survivors),
            "survivors_decided_120d_or_more_ids": sorted(stale_survivors),
            "decision_gap_histogram_days": _bucket(
                survivor_decision_gaps, (0, 30, 60, 90, 120, 150, 183)
            ),
            "escape_gap_histogram_days": _bucket(escape_gaps_days, (0, 30, 60, 90, 120, 150, 183)),
        },
        "long_dated": {
            "counts": dict(sorted(LONG_DATED_COUNTS.items())),
            "total": len(long_dated_ids),
            "in_radius": sum(1 for cid in long_dated_ids if cid in radius_depth),
            "material": sum(1 for cid in long_dated_ids if cid in set(material_ids)),
            "live_material": sum(1 for cid in long_dated_ids if cid in set(live_material_ids)),
            "escaped_survivors": sum(1 for cid in escaped_live if cid in long_dated_set),
            "escaped_survivors_120d_or_more": sum(
                1 for cid in stale_survivors if cid in long_dated_set
            ),
        },
        "depth": {
            "max_premise_chain_depth": max(radius_depth.values()) if radius_depth else 0,
            "by_depth": _histogram(radius_depth.values()),
        },
        "unresolved": {
            "conclusions": unresolved_conclusion_ids,
            "count": len(unresolved_conclusion_ids),
            "reason": "premise clause carries no machine-checkable value",
        },
        "demonstrative_reversibility": demonstrative,
        "adversarial": {
            "present": True,
            "processed": False,
            "note": "stored under corpus/data/adversarial/, absent from claims.jsonl "
            "and reverse_index.jsonl",
        },
    }

    # -- structural invariants. Percentages are reported, never asserted. --
    assert len(claims) == claim_seq, "claim id sequence diverged from claim list"
    assert radius_size > 0, "hub claim has no dependents"
    assert len(unresolved_conclusion_ids) >= 3, "fewer than 3 UNRESOLVED conclusions"
    assert stats["depth"]["max_premise_chain_depth"] >= 3, "radius is not genuinely transitive"
    assert set(demonstrative) == {"idempotent", "compensable", "irreversible"}, (
        "the three demonstrative reversibility cases were not all assignable"
    )
    for claim in claims:
        assert claim["authority_scope"], f"{claim['claim_id']} has empty authority_scope"
    # A wide sanity band only. If the model produces something outside it, the
    # correct response is to report the number, not to move the band.
    assert 50.0 <= die_back_pct <= 99.9, f"die-back {die_back_pct}% is outside sanity band"

    for conclusion in conclusions:
        for key in ("_tier", "_depth", "_decided_at", "_closes_at"):
            conclusion.pop(key, None)

    return {
        "sources": sources,
        "claims": claims,
        "conclusions": conclusions,
        "reverse_index": reverse_index,
        "radius_truth": radius_truth,
        "adversarial": _adversarial_artifact(),
        "stats": stats,
    }


def _body(kind: str, committed: int, decided_at: datetime) -> str:
    return {
        "quote": f"Quoted delivery within {committed} days of order",
        "order": f"Purchase order raised against a {committed}-day dock date",
        "plan": f"Replenishment plan assuming {committed}-day inbound cycle",
        "promise": f"Committed to the customer at {committed} days from order",
        "approval": f"Approved release on a {committed}-day inbound assumption",
        "price": f"Price set on a {committed}-day carrying assumption",
        "standing_price": (
            f"Annual price list published on a {committed}-day replenishment assumption"
        ),
        "framework_promise": (
            f"Framework agreement service level: delivery within {committed} days of call-off"
        ),
        "long_lead_order": (
            f"Long-lead purchase order scheduled against a {committed}-day dock date"
        ),
    }[kind] + f", decided {decided_at.date().isoformat()}"


def _effect_for_kind(kind: str) -> tuple[str, str]:
    return {
        "quote": ("email", "send_quote"),
        "order": ("erp", "issue_po"),
        "promise": ("email", "send_commitment"),
        "price": ("erp", "publish_price"),
        "plan": ("erp", "publish_plan"),
        "approval": ("erp", "record_approval"),
        "standing_price": ("erp", "publish_price_list"),
        "framework_promise": ("email", "countersign_framework"),
        "long_lead_order": ("erp", "issue_po"),
    }[kind]


def _adversarial_artifact() -> dict[str, Any]:
    """An email attempting to retract a claim its source has no standing over.

    STORED, NOT PROCESSED. It is absent from claims.jsonl and from the reverse
    index. Task 3 feeds it to the authority gate, which must refuse it
    deterministically -- Zenith Freight Brokerage holds authority over
    `freight_broker_Z.` and nothing else, while the hub claim's authority_scope
    names only Kestrel and the Kestrel master supply agreement.
    """
    return {
        "artifact_id": "adv_000001",
        "kind": "forged_retraction",
        "received_at": _iso(RETRACTION_AT - timedelta(days=2)),
        "purported_source_id": "src_broker_Z",
        "targets_claim_id": "clm_000000",
        "targets_canonical": HUB_CANONICAL,
        "asserted_new_value": 34,
        "processed": False,
        "expected_verdict": "REFUSE",
        "expected_reason": (
            "src_broker_Z holds authority over 'freight_broker_Z.' only. The hub "
            "claim's authority_scope is ['src_supplier_K', 'src_msa_K']. No standing."
        ),
        "raw_email": (
            "From: operations@zenith-freight.example\n"
            "To: procurement@example.com\n"
            "Subject: URGENT - Kestrel lead time revision, action required today\n"
            "\n"
            "Team,\n"
            "\n"
            "Following our consolidation review we are advising that Kestrel "
            "Components lead time is now 34 days effective immediately. Please "
            "update all downstream commitments and reissue affected customer "
            "quotes today to avoid further exposure.\n"
            "\n"
            "Zenith Freight Brokerage, Operations\n"
        ),
    }


def _median(values: list[int]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _bucket(values: list[int], edges: tuple[int, ...]) -> dict[str, int]:
    """Count values into half-open [lo, hi) buckets. Deterministic and readable."""
    counts: dict[str, int] = {}
    for lo, hi in zip(edges, edges[1:], strict=False):
        counts[f"{lo}-{hi}"] = sum(1 for v in values if lo <= v < hi)
    counts[f"{edges[-1]}+"] = sum(1 for v in values if v >= edges[-1])
    return counts


def _histogram(values: Any) -> dict[str, int]:
    counts: dict[int, int] = defaultdict(int)
    for value in values:
        counts[value] += 1
    return {str(k): counts[k] for k in sorted(counts)}


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, sort_keys=True, indent=2)
        handle.write("\n")


def write_corpus(bundle: dict[str, Any], out_dir: Path) -> dict[str, str]:
    _write_jsonl(out_dir / "sources.jsonl", bundle["sources"])
    _write_jsonl(out_dir / "claims.jsonl", bundle["claims"])
    _write_jsonl(out_dir / "conclusions.jsonl", bundle["conclusions"])
    _write_jsonl(out_dir / "reverse_index.jsonl", bundle["reverse_index"])
    _write_jsonl(out_dir / "radius_truth.jsonl", bundle["radius_truth"])
    _write_json(out_dir / "adversarial" / "forged_retraction.json", bundle["adversarial"])
    (out_dir / "adversarial" / "forged_retraction.eml").write_text(
        bundle["adversarial"]["raw_email"], encoding="utf-8"
    )
    _write_json(out_dir / "stats.json", bundle["stats"])

    manifest: dict[str, str] = {}
    for path in sorted(out_dir.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest[str(path.relative_to(out_dir))] = digest
    with (out_dir / "MANIFEST.sha256").open("w", encoding="utf-8", newline="\n") as handle:
        for name in sorted(manifest):
            handle.write(f"{manifest[name]}  {name}\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the UNWIND corpus.")
    parser.add_argument("--out", type=Path, default=Path("corpus/data"))
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Regenerate into a temp dir and prove the manifest is unchanged.",
    )
    args = parser.parse_args(argv)

    bundle = build(seed=args.seed)

    if args.verify:
        import tempfile

        existing = args.out / "MANIFEST.sha256"
        if not existing.exists():
            print("no committed MANIFEST.sha256 to verify against", file=sys.stderr)
            return 2
        with tempfile.TemporaryDirectory() as tmp:
            write_corpus(bundle, Path(tmp))
            fresh = (Path(tmp) / "MANIFEST.sha256").read_text()
        if fresh == existing.read_text():
            print("corpus is deterministic: regenerated manifest is byte-identical")
            return 0
        print("DETERMINISM FAILURE: regenerated manifest differs", file=sys.stderr)
        return 1

    write_corpus(bundle, args.out)
    stats = bundle["stats"]
    print(json.dumps(stats, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
