"""Context Firewall: decide what a resumed mission actually gets to see,
instead of handing it the entire checkpoint history unfiltered.

THREE SIGNALS, EACH DETERMINISTIC AND STATED AS ONE
---------------------------------------------------------
[ASSUMPTION] The brief this module implements against lists ten metadata
dimensions (importance, relevance, trust, freshness, source, authority,
missionId, agentId, timestamp, securityClassification). Three of those are
identifiers already present on every checkpoint (`missionId`/`agentId`/
`timestamp`) and not scoring signals at all; this module computes exactly
three real, independent signals over the rest -- freshness, trust, and
relevance -- the same "a demo-legible, reproducible policy, not a measured
or industry-standard one" discipline `hyperion/risk.py`'s weight table
already states for itself, rather than inventing seven more knobs with
nothing behind them.

  FRESHNESS  -- age of the checkpoint vs. `_STALE_AFTER_SECONDS`.
  TRUST      -- reuses `command_os.trust.trusted_state_for_mission`'s real
                categorical fold (never re-derived here, see that module for
                why it is categorical and not a score).
  RELEVANCE  -- whether this checkpoint's stage is one a resumed mission's
                remaining stages actually read from `ctx` (`_RELEVANT_STAGES`,
                a static fact about `command_os/mission.py`'s own stage
                functions, not a guess).

Each checkpoint gets exactly one decision: INCLUDE, SUMMARIZE, REJECT, or
QUARANTINE, with a stated reason -- never a silent pass-through of the full
history into a resumed mission's context.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

#: [ASSUMPTION] A checkpoint older than this is treated as stale context for
#: a resume decision. Chosen to be demo-legible (missions complete in
#: seconds; an hour is unambiguously "this happened a while ago"), not
#: measured from production traffic that does not exist in this repository.
_STALE_AFTER_SECONDS = 3600

#: Stage numbers whose detail a LATER stage's `ctx` actually reads (see
#: `command_os/mission.py`'s stage functions: 6 reads 5's decision, 7 reads
#: 5/6's case id and reason code, 8 reads 5's decision, 9/10 read 5-8's case
#: id and isolation state). Stages 1-3 establish the fleet/baseline once and
#: are never read again by a later stage function.
_RELEVANT_STAGES = {4, 5, 6, 7, 8, 9, 10}


def filter_context(mission_id: str, *, as_of: datetime | None = None) -> list[dict[str, Any]]:
    """One real decision per checkpoint the mission has accumulated so far.

    Called before `command_os.mission.resume_mission` reconstructs `ctx` --
    this module does not itself change what `resume_mission` does with the
    checkpoint's `ctx` (that reconstruction is unconditional, by design: the
    fields it needs are small, typed, and already trust-checked at the
    point they were written). What this module governs is what a UI or a
    caller *displays* as the mission's trusted context going into a resume,
    which is the sense in which a firewall decides what crosses a boundary.
    """
    from command_os.checkpoint import list_checkpoints
    from command_os.trust import trusted_state_for_mission

    now = as_of or datetime.now(UTC)
    checkpoints = list_checkpoints(mission_id)
    trust = trusted_state_for_mission(mission_id)
    quarantined_seqs = {item["seq"] for item in trust["quarantined"]}
    revoked_seqs = {item["seq"] for item in trust["revoked"]}

    decisions: list[dict[str, Any]] = []
    for cp in checkpoints:
        age_seconds = max(0.0, (now - cp.created_at).total_seconds())
        stale = age_seconds > _STALE_AFTER_SECONDS
        relevant = cp.stage.n in _RELEVANT_STAGES

        if cp.seq in revoked_seqs:
            decision, reason = "REJECT", "revoked: the underlying decision was not allowed"
        elif cp.seq in quarantined_seqs:
            decision, reason = "QUARANTINE", "the agent was isolated at this checkpoint"
        elif stale:
            decision, reason = (
                "REJECT",
                f"stale: {age_seconds:.0f}s old, over the {_STALE_AFTER_SECONDS}s floor",
            )
        elif not relevant:
            decision, reason = "SUMMARIZE", "not read by any later stage function"
        else:
            decision, reason = "INCLUDE", "fresh, trusted, and consumed by a later stage"

        decisions.append(
            {
                "seq": cp.seq,
                "stage": cp.stage.name,
                "decision": decision,
                "reason": reason,
                "signals": {
                    "freshness": "STALE" if stale else "FRESH",
                    "trust": (
                        "REVOKED"
                        if cp.seq in revoked_seqs
                        else "QUARANTINED"
                        if cp.seq in quarantined_seqs
                        else "TRUSTED"
                    ),
                    "relevance": "RELEVANT" if relevant else "LOW",
                },
            }
        )
    return decisions
