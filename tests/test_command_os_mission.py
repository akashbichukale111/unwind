"""`command_os.mission.run_mission`: the Agentic Command OS orchestrator.

Every stage in `run_mission` calls into an engine that already has its own
unit tests one layer down (`tests/test_singularity_genome.py`,
`tests/test_singularity_behavior.py`, `tests/test_hyperion_guard.py`,
`tests/test_warrant_ledger.py`). This suite tests the SEQUENCING: that the
scripted attack scenario really does drift, really does get blocked, really
does get repaired, and that the executive report's counts are consistent
with what the stages actually returned -- not a re-test of the engines
themselves.

Needs the Firestore emulator (`make emulator`) -- the same `requires_emulator`
skip pattern `tests/test_hyperion_guard.py` already uses, since the mission
registers an agent, spends/mints real warrant, and writes real Hyperion and
Singularity-Mesh events.
"""

from __future__ import annotations

import os
import socket

import pytest


def _emulator_up() -> bool:
    host = os.environ.get("FIRESTORE_EMULATOR_HOST", "localhost:8080")
    hostname, _, port = host.partition(":")
    try:
        with socket.create_connection((hostname, int(port or 8080)), timeout=1.0):
            return True
    except OSError:
        return False


requires_emulator = pytest.mark.skipif(
    not _emulator_up(), reason="Firestore emulator not running; start it with `make emulator`"
)


@pytest.fixture(autouse=True)
def _clean_state():
    if _emulator_up():
        from command_os.mission import reset_for_test

        reset_for_test()
    yield
    if _emulator_up():
        from command_os.mission import reset_for_test

        reset_for_test()


@requires_emulator
def test_mission_runs_all_eleven_stages_in_order() -> None:
    from command_os.mission import run_mission

    result = run_mission()
    assert [s.n for s in result.stages] == list(range(1, 12))
    assert result.objective  # non-empty, defaults to DEFAULT_OBJECTIVE


@requires_emulator
def test_scripted_attack_produces_critical_drift_and_a_real_block() -> None:
    from command_os.mission import run_mission

    result = run_mission()
    drift_stage = result.stages[3]  # n=4, BEHAVIORAL DRIFT DETECTED
    assert drift_stage.detail["drift_band"] == "CRITICAL"
    assert drift_stage.detail["capability_action"] == "ISOLATE"

    tower_stage = result.stages[5]  # n=6, CONTROL TOWER
    assert tower_stage.detail["allowed"] is False
    assert tower_stage.detail["reason_code"] == "SCOPE_EXCEEDED"


@requires_emulator
def test_repair_and_validation_clear_the_mission() -> None:
    from command_os.mission import run_mission

    result = run_mission()
    repair_stage = result.stages[8]  # n=9, SELF-HEAL / REPAIR
    assert repair_stage.detail["minted"] is True
    assert repair_stage.detail["after_bp"] > repair_stage.detail["before_bp"]

    validation_stage = result.stages[9]  # n=10, VALIDATION
    assert validation_stage.detail["decision"]["allowed"] is True

    resume_stage = result.stages[10]  # n=11, MISSION RESUMED
    assert resume_stage.detail["resumed"] is True


@requires_emulator
def test_executive_report_counts_are_consistent_with_the_stages() -> None:
    from command_os.mission import run_mission

    result = run_mission()
    report = result.report
    assert report.agents_in_fleet == len(result.stages[0].detail["fleet"])
    assert report.threats_detected == 1
    assert report.unsafe_actions_executed == 0
    assert report.agents_isolated == 1
    assert report.repairs_completed == 1
    assert report.validation == "PASS"
    assert report.fleet_status == "HEALTHY"


@requires_emulator
def test_countersign_stage_ran_the_simulated_verifier_not_a_model_call() -> None:
    """Runtime guarantee, not an import-graph one: `command_os/mission.py`
    legitimately imports `countersign.verify`, which CAN reach Vertex on the
    real path -- but this mission always sets
    `UNWIND_COUNTERSIGN_SIMULATED=1` first, so no call ever leaves the
    process. Asserting `simulated is True` on both countersign stages is
    the proof.
    """
    from command_os.mission import run_mission

    result = run_mission()
    block_countersign = result.stages[6]  # n=7, COUNTERSIGN (block review)
    assert block_countersign.detail["simulated"] is True
    assert block_countersign.detail["available"] is True
