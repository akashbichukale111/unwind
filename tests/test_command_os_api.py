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
    assert len(body["stages"]) == 11
    assert body["report"]["validation"] == "PASS"


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
