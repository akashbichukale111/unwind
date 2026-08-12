"""FastAPI surface for UNWIND. Task 1 ships the transport, not the product.

The one endpoint that matters is `/cascade/{claim_id}/stream`. A blast radius is
discovered incrementally -- depth 1 arrives long before the traversal finishes --
and the operator watching it needs to see the radius fill in rather than wait for
a total. That is a server-push stream, so SSE.

Everything under /cascade is a STUB. It says so in its own response body, not
only in the README, because a stub that looks like a result is the one thing that
loses the room.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from lib.config import ALL_TOPICS, get_config
from lib.telemetry import configure_telemetry

BUILD_STAGE = "task-1-scaffolding"


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    application.state.telemetry_exporter = configure_telemetry()
    yield


app = FastAPI(
    title="UNWIND",
    version="0.1.0",
    description=(
        "Cache invalidation for decisions. Task 1 scaffolding: transport only, "
        "no cascade, no scoring, no obligations."
    ),
    lifespan=lifespan,
)


@app.get("/healthz")
async def healthz() -> dict[str, object]:
    cfg = get_config()
    return {
        "status": "ok",
        "stage": BUILD_STAGE,
        "model": cfg.gemini_model,
        "vertex_location": cfg.vertex_location,
        "vertex_disabled": cfg.vertex_disabled,
        "firestore": "emulator" if cfg.uses_emulator else "cloud",
        "pubsub": "local-shim" if cfg.pubsub_local else "cloud",
        "topics": list(ALL_TOPICS),
        "telemetry_exporter": getattr(app.state, "telemetry_exporter", "not-configured"),
    }


@app.get("/cascade/{claim_id}/stream")
async def cascade_stream(claim_id: str) -> StreamingResponse:
    """SSE stub for blast-radius traversal.

    NOT IMPLEMENTED. Emits one `stub` event saying so and closes. Task 2 replaces
    the generator body with the real T0 traversal; the wire format below is the
    contract that traversal must fill.
    """

    async def _events() -> AsyncIterator[str]:
        payload = {
            "event": "stub",
            "claim_id": claim_id,
            "built": False,
            "message": (
                "Blast-radius traversal is NOT BUILT. Task 1 ships the stream "
                "transport only; the T0 traversal lands in Task 2."
            ),
            "planned_events": [
                "radius.node   one dependent found, with depth and weight",
                "radius.scored one dependent scored into a regime",
                "radius.done   totals, plus the unresolved count",
            ],
            "at": datetime.now(UTC).isoformat(),
        }
        yield f"event: stub\ndata: {json.dumps(payload)}\n\n"
        await asyncio.sleep(0)

    return StreamingResponse(
        _events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Unwind-Stage": BUILD_STAGE},
    )
