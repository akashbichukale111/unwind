"""Trusted State: what a mission is willing to trust right now, as distinct
from what merely happened (memory).

WHY THIS IS CATEGORICAL, NOT A SCORE
-----------------------------------------
This repository has already rejected scalar agent "trust" once:
`lib/schema.py:AgentTrust` (a `reputation: float`) exists only so
`settle/loadrating.py:assert_not_agent_trust` can refuse it as a load-rating
input, with `tests/test_warrant_separation.py` proving the guard is neither
vacuous nor over-broad. "Never one number" is the same principle
`warrant/DESIGN.md` states for balances and `hyperion/schema.py`'s
`RiskAssessment` docstring states for risk. Trusted State follows the same
rule: every item below is a member of exactly one named bucket
(TRUSTED / UNTRUSTED / QUARANTINED / REVOKED), never a blended percentage.

MEMORY vs. TRUSTED STATE
------------------------------
Memory is "what happened" -- the full checkpoint trace, already served by
`/api/command-os/mission/{id}/checkpoints`. Trusted State is "what are we
willing to act on now" -- a strictly smaller fold over the same stages, plus
the real Hyperion events the mission's own `case_id`s produced (`hyperion/
guard.py:evaluate_with_hyperion` tags every event it writes with the
`case_id` it was called with, so this filter is exact, not a heuristic).

Singularity-Mesh events are deliberately NOT folded in here: `command_os/
mission.py` never calls `singularity.mesh_memory.write_genome_event` or
`write_behavior_event` (only the standalone `/api/singularity/*/probe`
routes do), and `MeshEvent` carries no `case_id` field to filter by even if
it did. Claiming to fold mission-scoped mesh events in would be exactly the
kind of number that looks real but isn't -- this module returns none rather
than a fabricated always-zero one.
"""

from __future__ import annotations

from typing import Any


def trusted_state_for_mission(mission_id: str) -> dict[str, Any]:
    """Real fold over the mission's own checkpoints plus the Hyperion events
    its `case_id`s produced -- never a fabricated summary. A mission with no
    events yet honestly returns empty buckets, the same "an empty fold is
    honestly labelled, not guessed" discipline
    `hyperion/immune_memory.py:aggregate_fleet_summary` already uses.
    """
    from command_os.checkpoint import get_mission_record, list_checkpoints
    from hyperion.immune_memory import list_events as list_hyperion_events

    record = get_mission_record(mission_id)
    checkpoints = list_checkpoints(mission_id)

    trusted: list[dict[str, Any]] = []
    untrusted: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    revoked: list[dict[str, Any]] = []

    for cp in checkpoints:
        item = {"seq": cp.seq, "stage": cp.stage.name, "status": cp.stage.status}
        allowed = cp.stage.detail.get("allowed")
        if cp.stage.n == 8 and cp.stage.detail.get("isolated"):
            quarantined.append(item)
        elif allowed is True:
            trusted.append(item)
        elif allowed is False:
            revoked.append(item)
        else:
            untrusted.append(item)

    case_ids = {
        v for k, v in (checkpoints[-1].ctx.items() if checkpoints else []) if k.endswith("case_id")
    }
    hyperion_events = [e for e in list_hyperion_events() if e.case_id in case_ids]

    return {
        "mission_id": mission_id,
        "mission_status": record.status if record else None,
        "trusted": trusted,
        "untrusted": untrusted,
        "quarantined": quarantined,
        "revoked": revoked,
        "hyperion_events_considered": len(hyperion_events),
    }
