"""Typed models for one Agentic Command OS mission run.

Same discipline `singularity/schema.py` and `hyperion/schema.py` already use:
every field typed before any logic exists. `status` is a plain string, not a
closed enum, because it carries a narrative label
(`"LIVE"` / `"SIMULATED"` / `"LIVE (reacting to SIMULATED input)"` /
`"UNAVAILABLE"`) rather than an enforcement decision -- unlike
`GenomeDecision` or `DriftBand` one layer down, nothing routes on this value.
"""

from __future__ import annotations

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
    mission -- never hardcoded. See `command_os/mission.py:run_mission`."""

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
    stages: list[MissionStage]
    report: MissionReport
