"""API-level tests for the Agentic Command OS surface
(`/api/command-os/*`), independent of the six existing cards' endpoints,
which this suite never touches or breaks.
"""

from __future__ import annotations

import os
import socket

import pytest
from fastapi.testclient import TestClient

from services.api.main import app


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


def test_status_serves_the_system_reality_table_even_offline() -> None:
    """No Firestore dependency -- `system_reality()` is static composition
    over already-in-memory constants, the same offline-safe discipline
    `/api/singularity`'s reference content already follows."""
    with TestClient(app) as client:
        body = client.get("/api/command-os/status").json()
    areas = {row["area"] for row in body["rows"]}
    assert areas == {"Singularity-Mesh", "Hyperion-Zero", "Agentic Command OS"}
    statuses = {row["status"] for row in body["rows"]}
    assert statuses <= {"LIVE", "REFERENCE", "ARCHITECTURE", "SIMULATED", "DESIGNED"}


def test_concept_map_maps_all_fifteen_names() -> None:
    with TestClient(app) as client:
        body = client.get("/api/command-os/concept-map").json()
    assert len(body["rows"]) == 15
    names = {row["name"] for row in body["rows"]}
    assert "Chronos-9" in names
    assert "Pandora" in names
    assert all(row["status"] for row in body["rows"])


@requires_emulator
def test_mission_endpoint_runs_end_to_end() -> None:
    with TestClient(app) as client:
        resp = client.post("/api/command-os/mission")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert len(body["stages"]) == 11
    assert body["report"]["validation"] == "PASS"


@requires_emulator
def test_gate_pause_approve_deny_and_resume_via_http() -> None:
    from command_os.mission import reset_for_test

    with TestClient(app) as client:
        paused = client.post("/api/command-os/mission?auto_approve=false").json()
        assert paused["status"] == "AWAITING_HUMAN"
        assert paused["report"] is None
        mission_id = paused["mission_id"]

        # the crash-recovery endpoint refuses a gated mission
        refused = client.post(f"/api/command-os/mission/{mission_id}/resume")
        assert refused.status_code == 409

        # an invalid decision is rejected before touching the mission
        bad = client.post(f"/api/command-os/mission/{mission_id}/gate?decision=maybe")
        assert bad.status_code == 422

        approved = client.post(f"/api/command-os/mission/{mission_id}/gate?decision=approve").json()
        assert approved["status"] == "COMPLETED"

        checkpoints = client.get(f"/api/command-os/mission/{mission_id}/checkpoints").json()
        assert len(checkpoints["checkpoints"]) == 11
    reset_for_test(mission_id)


@requires_emulator
def test_trust_and_context_firewall_endpoints_are_wired() -> None:
    from command_os.mission import reset_for_test

    with TestClient(app) as client:
        result = client.post("/api/command-os/mission").json()
        mission_id = result["mission_id"]

        trust = client.get(f"/api/command-os/mission/{mission_id}/trust").json()
        assert trust["mission_status"] == "COMPLETED"

        firewall = client.get(f"/api/command-os/mission/{mission_id}/context-firewall").json()
        assert len(firewall["decisions"]) == 11

        missions = client.get("/api/command-os/missions").json()
        assert missions["available"] is True
        assert mission_id in {m["mission_id"] for m in missions["missions"]}
    reset_for_test(mission_id)


def test_checkpoints_for_an_unknown_mission_is_404() -> None:
    if not _emulator_up():
        pytest.skip("needs the emulator to reach Firestore at all")
    with TestClient(app) as client:
        resp = client.get("/api/command-os/mission/mission_does_not_exist/checkpoints")
    assert resp.status_code == 404


def test_mission_endpoint_without_emulator_reports_unavailable_not_a_crash() -> None:
    """When Firestore is unreachable, the mission endpoint must fail the
    same honest way `/api/instrument/burn` and `/api/instrument/earn`
    already do -- a 503, never a 500 or a fabricated trace."""
    if _emulator_up():
        pytest.skip("this test asserts the no-emulator path specifically")
    with TestClient(app) as client:
        resp = client.post("/api/command-os/mission")
    assert resp.status_code == 503


def test_existing_six_card_endpoints_still_respond() -> None:
    """Regression guard: adding the Command OS layer must not disturb
    Cards 0-5's endpoints."""
    with TestClient(app) as client:
        assert client.get("/api/instrument").status_code == 200
        assert client.get("/api/hyperion").status_code == 200
        assert client.get("/api/singularity").status_code == 200
