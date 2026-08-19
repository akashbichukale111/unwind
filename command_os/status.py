"""System Reality: the honest LIVE / SIMULATED / REFERENCE / ARCHITECTURE /
DESIGNED status of everything the Agentic Command OS surfaces, in one place.

This module invents no new status values for content that already has an
honest label -- `singularity.lifecycle.IMPLEMENTATION_STATUS` is reused
verbatim, and the Hyperion rows below are a direct transcription of
`hyperion/DESIGN.md`'s own "What is built" / "What is NOT built" tables, not
a re-assessment. Only the Command-OS-level rows at the bottom are new, and
each one is scoped to exactly what `command_os/mission.py` does or does not
do.
"""

from __future__ import annotations

from typing import Any


def system_reality() -> list[dict[str, Any]]:
    from singularity.lifecycle import IMPLEMENTATION_STATUS

    rows: list[dict[str, Any]] = []

    for feature, status in IMPLEMENTATION_STATUS.items():
        rows.append({"area": "Singularity-Mesh", "feature": feature, "status": status})

    # Transcribed from hyperion/DESIGN.md's "What is built" / "What is NOT
    # built" tables -- not re-derived here.
    for feature, status in (
        ("risk_scoring", "LIVE"),
        ("immune_event_log", "LIVE"),
        ("mcp_tool_call_guard", "ARCHITECTURE"),
        ("shadow_sandbox", "ARCHITECTURE"),
        ("quarantine_process_isolation", "ARCHITECTURE"),
        ("fleet_threat_propagation", "ARCHITECTURE"),
    ):
        rows.append({"area": "Hyperion-Zero", "feature": feature, "status": status})

    for feature, status, note in (
        (
            "master_orchestrator",
            "LIVE",
            "command_os/mission.py sequences real engine calls end-to-end for one mission",
        ),
        (
            "dynamic_agent_factory",
            "SIMULATED",
            "static 7-role roster (singularity/fleet.py); no live agent spawning",
        ),
        (
            "red_team_chaos_testing",
            "SIMULATED",
            "one scripted adversarial scenario per mission run; no autonomous red agent",
        ),
        (
            "digital_twin",
            "DESIGNED",
            "not built; no simulation or forecasting engine exists in this repository",
        ),
        (
            "cross_department_orchestration",
            "DESIGNED",
            "department names are documentation grouping only, not enforced routing",
        ),
        (
            "self_healing_repair",
            "LIVE",
            "genome re-negotiation + real re-mint via warrant/ledger.py, driven by command_os/mission.py",
        ),
    ):
        rows.append(
            {"area": "Agentic Command OS", "feature": feature, "status": status, "note": note}
        )

    return rows
