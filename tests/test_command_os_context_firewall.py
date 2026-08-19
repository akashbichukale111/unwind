"""`command_os.context_firewall.filter_context`: three deterministic
signals (freshness, trust, relevance) folded into one INCLUDE/SUMMARIZE/
REJECT/QUARANTINE decision per checkpoint.
"""

from __future__ import annotations

import os
import socket
from datetime import UTC, datetime, timedelta

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
def test_every_checkpoint_gets_exactly_one_decision() -> None:
    from command_os.context_firewall import filter_context
    from command_os.mission import reset_for_test, run_mission

    result = run_mission()
    decisions = filter_context(result.mission_id)
    assert [d["seq"] for d in decisions] == list(range(1, 12))
    assert all(d["decision"] in ("INCLUDE", "SUMMARIZE", "REJECT", "QUARANTINE") for d in decisions)
    reset_for_test(result.mission_id)


@requires_emulator
def test_the_revoked_block_is_rejected_and_isolation_is_quarantined() -> None:
    from command_os.context_firewall import filter_context
    from command_os.mission import reset_for_test, run_mission

    result = run_mission()
    decisions = {d["seq"]: d for d in filter_context(result.mission_id)}
    assert decisions[6]["decision"] == "REJECT"
    assert decisions[6]["signals"]["trust"] == "REVOKED"
    assert decisions[8]["decision"] == "QUARANTINE"
    reset_for_test(result.mission_id)


@requires_emulator
def test_early_setup_stages_are_summarized_not_included() -> None:
    """Stages 1-3 establish the fleet/baseline once and are never read
    again by a later stage function -- low relevance, not low trust."""
    from command_os.context_firewall import filter_context
    from command_os.mission import reset_for_test, run_mission

    result = run_mission()
    decisions = {d["seq"]: d for d in filter_context(result.mission_id)}
    for seq in (1, 2, 3):
        assert decisions[seq]["decision"] == "SUMMARIZE"
        assert decisions[seq]["signals"]["relevance"] == "LOW"
    reset_for_test(result.mission_id)


@requires_emulator
def test_stale_checkpoints_are_rejected_regardless_of_trust() -> None:
    """Freshness overrides an otherwise-trusted, otherwise-relevant item --
    passing `as_of` far in the future is the deterministic way to exercise
    this without an hour-long sleep."""
    from command_os.context_firewall import filter_context
    from command_os.mission import reset_for_test, run_mission

    result = run_mission()
    far_future = datetime.now(UTC) + timedelta(days=1)
    decisions = {d["seq"]: d for d in filter_context(result.mission_id, as_of=far_future)}

    # seq 4 (the drift event) would otherwise be INCLUDE -- confirm staleness
    # alone is enough to reject it, and that the reason says so.
    assert decisions[4]["decision"] == "REJECT"
    assert "stale" in decisions[4]["reason"]
    reset_for_test(result.mission_id)
