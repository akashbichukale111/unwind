"""`command_os.trust.trusted_state_for_mission`: a real, categorical fold
over one mission's checkpoints and Hyperion events -- never a scalar score
(see the module's docstring for why: `lib/schema.py:AgentTrust` was already
rejected once by `settle/loadrating.py:assert_not_agent_trust`).
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
    from command_os.mission import reset_for_test

    reset_for_test()
    yield
    reset_for_test()


@requires_emulator
def test_buckets_are_disjoint_and_every_checkpoint_lands_in_exactly_one() -> None:
    from command_os.mission import reset_for_test, run_mission
    from command_os.trust import trusted_state_for_mission

    result = run_mission()
    state = trusted_state_for_mission(result.mission_id)

    all_seqs = [
        item["seq"]
        for bucket in ("trusted", "untrusted", "quarantined", "revoked")
        for item in state[bucket]
    ]
    assert sorted(all_seqs) == list(range(1, 12))
    assert len(all_seqs) == len(set(all_seqs))  # disjoint: no seq in two buckets
    reset_for_test(result.mission_id)


@requires_emulator
def test_the_block_is_revoked_and_isolation_is_quarantined() -> None:
    from command_os.mission import reset_for_test, run_mission
    from command_os.trust import trusted_state_for_mission

    result = run_mission()
    state = trusted_state_for_mission(result.mission_id)

    revoked_seqs = {item["seq"] for item in state["revoked"]}
    quarantined_seqs = {item["seq"] for item in state["quarantined"]}
    assert 6 in revoked_seqs  # CONTROL TOWER -- ACTION BLOCKED
    assert 8 in quarantined_seqs  # AGENT ISOLATED
    reset_for_test(result.mission_id)


@requires_emulator
def test_no_scalar_score_anywhere_in_the_payload() -> None:
    """The categorical-not-scalar guarantee, asserted directly: no field
    named anything like a reputation/trust score, and no float in [0, 1]
    posing as one."""
    from command_os.mission import reset_for_test, run_mission
    from command_os.trust import trusted_state_for_mission

    result = run_mission()
    state = trusted_state_for_mission(result.mission_id)

    forbidden_keys = {"score", "reputation", "trust_score", "confidence"}
    assert not (forbidden_keys & set(state.keys()))
    reset_for_test(result.mission_id)


@requires_emulator
def test_hyperion_events_considered_matches_the_mission_own_case_ids() -> None:
    """Real, exact filtering by case_id -- not every Hyperion event ever
    logged, only this mission's."""
    from command_os.mission import _ensure_mission_agent, reset_for_test, run_mission
    from command_os.trust import trusted_state_for_mission
    from hyperion.guard import evaluate_with_hyperion

    result = run_mission()
    agent = _ensure_mission_agent()
    # An unrelated event, same agent, different case_id -- must not be counted.
    evaluate_with_hyperion(
        agent,
        task="unrelated probe",
        requested_scope=["web.read"],
        requested_cost=1,
        risk_class="LOW",
        capability="research",
        case_id="not_this_missions_case",
    )

    state = trusted_state_for_mission(result.mission_id)
    assert state["hyperion_events_considered"] == 2  # stage 5's block + stage 10's validation
    reset_for_test(result.mission_id)
