"""The API transport works, and the unbuilt parts say so in their own response.

A stub that returns a plausible-looking result is the single most damaging thing
this repository could contain. The SSE endpoint is therefore tested for saying
"NOT BUILT", not merely for returning 200.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from services.api.main import app


def test_healthz_reports_the_real_configuration() -> None:
    with TestClient(app) as client:
        body = client.get("/healthz").json()
    assert body["status"] == "ok"
    assert body["stage"] == "task-1-scaffolding"
    assert len(body["topics"]) == 6
    assert body["pubsub"] in {"local-shim", "cloud"}
    assert body["firestore"] in {"emulator", "cloud"}


def test_cascade_stream_declares_itself_unbuilt() -> None:
    with TestClient(app) as client:
        response = client.get("/cascade/clm_000000/stream")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        raw = response.text

    assert raw.startswith("event: stub\n")
    payload = json.loads(raw.split("data: ", 1)[1].split("\n\n", 1)[0])
    assert payload["built"] is False
    assert "NOT BUILT" in payload["message"]
    assert payload["claim_id"] == "clm_000000"
