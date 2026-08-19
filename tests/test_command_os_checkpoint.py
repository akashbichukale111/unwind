"""`command_os.checkpoint`: the Mission Checkpoint Engine's persistence
layer, and `command_os.mission.resume_mission`'s three real cases --
ALREADY COMPLETED, REQUIRES HUMAN APPROVAL, and REPLAYABLE FROM THE NEXT
STAGE (crash recovery).

Needs the Firestore emulator (`make emulator`) -- same `requires_emulator`
pattern every other command_os test uses.
"""

from __future__ import annotations

import os
import socket
import uuid

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
    from command_os.mission import reset_for_test

    reset_for_test()
    yield
    reset_for_test()


@requires_emulator
def test_checkpoints_survive_and_are_ordered() -> None:
    from command_os.checkpoint import list_checkpoints
    from command_os.mission import reset_for_test, run_mission

    result = run_mission()
    checkpoints = list_checkpoints(result.mission_id)
    assert [c.seq for c in checkpoints] == list(range(1, 12))
    assert [c.status for c in checkpoints[:-1]] == ["RUNNING"] * 10
    assert checkpoints[-1].status == "COMPLETED"
    reset_for_test(result.mission_id)


@requires_emulator
def test_resuming_an_already_completed_mission_does_not_rerun_anything() -> None:
    """ALREADY COMPLETED: the stored trace is returned as-is -- no new
    warrant spend, no new Hyperion event."""
    from command_os.mission import reset_for_test, resume_mission, run_mission
    from hyperion.immune_memory import list_events

    first = run_mission()
    events_before = len(list_events())

    second = resume_mission(first.mission_id)

    assert second.status == "COMPLETED"
    assert len(second.stages) == len(first.stages) == 11
    assert len(list_events()) == events_before  # nothing new was written
    reset_for_test(first.mission_id)


@requires_emulator
def test_resume_without_a_decision_on_an_awaiting_human_mission_raises() -> None:
    """REQUIRES HUMAN APPROVAL: the crash-recovery path refuses to silently
    proceed past a gate nobody actually cleared."""
    from command_os.mission import reset_for_test, resume_mission, run_mission

    paused = run_mission(auto_approve=False)
    assert paused.status == "AWAITING_HUMAN"

    with pytest.raises(ValueError, match="AWAITING_HUMAN"):
        resume_mission(paused.mission_id)
    reset_for_test(paused.mission_id)


@requires_emulator
def test_approving_the_gate_resumes_into_the_same_repair_chain() -> None:
    from command_os.mission import reset_for_test, resume_mission, run_mission

    paused = run_mission(auto_approve=False)
    resumed = resume_mission(paused.mission_id, human_decision="approve")

    assert resumed.status == "COMPLETED"
    assert len(resumed.stages) == 11
    assert resumed.report.validation == "PASS"
    reset_for_test(paused.mission_id)


@requires_emulator
def test_denying_the_gate_halts_without_attempting_repair() -> None:
    from command_os.mission import (
        _ensure_mission_agent,
        reset_for_test,
        resume_mission,
        run_mission,
    )
    from warrant.ledger import current_balance

    paused = run_mission(auto_approve=False)
    agent = _ensure_mission_agent()
    balance_before = current_balance(agent.principal, "research", "LOW")

    halted = resume_mission(paused.mission_id, human_decision="deny")

    assert halted.status == "HALTED"
    assert len(halted.stages) == 8  # stages 9-11 never ran
    assert halted.report.repairs_completed == 0
    assert halted.report.validation == "FAIL"
    balance_after = current_balance(agent.principal, "research", "LOW")
    assert balance_after == balance_before  # no mint happened
    reset_for_test(paused.mission_id)


@requires_emulator
def test_resume_from_a_simulated_crash_continues_past_the_last_completed_stage() -> None:
    """REPLAYABLE FROM THE NEXT STAGE: manually write checkpoints only
    through stage 5 (as if the process died right after), then resume and
    confirm it continues at stage 6 rather than re-running 1-5."""
    from command_os import checkpoint
    from command_os.mission import _STAGES, _ensure_mission_agent, reset_for_test, resume_mission

    mission_id = f"mission_test_{uuid.uuid4().hex[:8]}"
    _ensure_mission_agent()
    checkpoint.start_mission_record(mission_id, "test objective")
    ctx = {"mission_id": mission_id, "objective": "test objective", "auto_approve": True}
    for seq in range(1, 6):
        stage = _STAGES[seq - 1](ctx)
        checkpoint.write_checkpoint(
            mission_id=mission_id, seq=seq, stage=stage, ctx=dict(ctx), status="RUNNING"
        )

    result = resume_mission(mission_id)

    assert result.status == "COMPLETED"
    # 5 pre-existing + 6 newly-run (6 through 11) = 11 total, never duplicated
    assert [s.n for s in result.stages] == list(range(1, 12))
    reset_for_test(mission_id)


@requires_emulator
def test_missions_index_lists_recent_missions_most_recent_first() -> None:
    from command_os.checkpoint import list_missions
    from command_os.mission import reset_for_test, run_mission

    a = run_mission()
    b = run_mission()
    missions = list_missions(limit=5)
    ids = [m.mission_id for m in missions]
    assert ids.index(b.mission_id) < ids.index(a.mission_id)
    reset_for_test(a.mission_id)
    reset_for_test(b.mission_id)
