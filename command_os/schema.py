"""Typed models for Agentic Command OS mission runs and the Mission
Checkpoint Engine's persisted state.

Same discipline `singularity/schema.py` and `hyperion/schema.py` already use:
every field typed before any logic exists. `MissionStage.status` and
`MissionResult.status`/`MissionCheckpoint.status` are plain strings, not
closed enums, because the former carries a narrative label
(`"LIVE"` / `"SIMULATED"` / `"LIVE (reacting to SIMULATED input)"` /
`"UNAVAILABLE"`) rather than an enforcement decision -- unlike
`GenomeDecision` or `DriftBand` one layer down, nothing routes on it. The
latter (`RUNNING` / `AWAITING_HUMAN` / `COMPLETED` / `HALTED`) IS a closed,
routed vocabulary -- `command_os/mission.py:resume_mission` branches on it --
kept as a string here rather than an Enum only so a checkpoint document that
predates a future added status value still deserialises.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MissionStage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    n: int
    name: str
    status: str
    summary: str
    detail: dict[str, Any] = Field(default_factory=dict)


class MissionReport(BaseModel):
    """Every field here is folded from the stages that actually ran in this
    mission -- never hardcoded. See `command_os/mission.py:_build_report`."""

    model_config = ConfigDict(extra="forbid")

    agents_in_fleet: int
    threats_detected: int
    unsafe_actions_executed: int
    agents_isolated: int
    repairs_completed: int
    validation: str
    fleet_status: str


class MissionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mission_id: str
    objective: str
    #: RUNNING (mid-flight, only reachable via direct in-process return, never
    #: persisted as a final state) / AWAITING_HUMAN (paused at the gate,
    #: `report` is None) / COMPLETED / HALTED (human denied, or validation
    #: did not clear -- `report` is populated either way).
    status: str
    stages: list[MissionStage]
    report: MissionReport | None = None


class MissionCheckpoint(BaseModel):
    """One append-only entry in `command_os_missions/{mission_id}/checkpoints`.

    `ctx` is the mission's continuation state as of immediately after this
    stage completed -- everything `resume_mission` needs to pick up at
    `seq + 1` without re-deriving or re-executing anything already done.
    JSON-safe primitives only (mirrors `MeshEvent.detail` /
    `HyperionEvent`'s own to-Firestore discipline): case IDs, booleans,
    counts -- never a live object like an `AgentRegistryEntry`, which is
    re-fetched from the durable `tower.registry` on resume instead of
    round-tripped through this document.
    """

    model_config = ConfigDict(extra="forbid")

    mission_id: str
    seq: int
    stage: MissionStage
    ctx: dict[str, Any]
    status: str
    created_at: datetime


class MissionRecord(BaseModel):
    """The parent document for one mission -- `command_os_missions/{mission_id}`."""

    model_config = ConfigDict(extra="forbid")

    mission_id: str
    objective: str
    status: str
    created_at: datetime
    updated_at: datetime
