"""FastAPI surface for UNWIND. Serves the operator field and the real cascade.

The one endpoint that matters is `/api/cascade/stream`. A blast radius is
discovered incrementally -- depth 1 arrives long before the traversal finishes --
and the operator watching it needs to see the radius fill in rather than wait for
a total. That is a server-push stream, so SSE.

⚠ EVERY NUMBER THIS API SERVES COMES FROM A REAL CASCADE OVER THE COMMITTED
CORPUS. Nothing here is a fixture, a mock, or a hardcoded total. The one thing
that is not real is the *pacing* of the stream -- the cascade computes in well
under a second and a human needs about twenty to read it -- so the stream is
paced, `paced_ms` is reported in the `begin` event, and the UI says so on screen.
Real events, disclosed pacing.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from lib.config import ALL_TOPICS, get_config
from lib.telemetry import configure_telemetry

BUILD_STAGE = "task-5-interface"
REPO = Path(__file__).resolve().parents[2]
STATIC = REPO / "web" / "static"

#: The instant the committed corpus is built around. Using it keeps the demo
#: reproducible; "already closed out" is a time-dependent verdict, so a
#: wall-clock default would make two runs of the demo disagree.
CORPUS_AT = datetime(2026, 7, 6, 9, 0, tzinfo=UTC)

_CACHE: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    application.state.telemetry_exporter = configure_telemetry()
    yield


app = FastAPI(
    title="UNWIND",
    version="0.5.0",
    description="Cache invalidation for decisions.",
    lifespan=lifespan,
)


def _store():
    if "store" not in _CACHE:
        from spine.cascade import CorpusStore

        _CACHE["store"] = CorpusStore.from_repo(REPO)
    return _CACHE["store"]


def _stats() -> dict:
    if "stats" not in _CACHE:
        _CACHE["stats"] = json.loads(
            (REPO / "corpus" / "data" / "stats.json").read_text(encoding="utf-8")
        )
    return _CACHE["stats"]


@app.get("/api/healthz")
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


# ---------------------------------------------------------------------------
# THE FIELD
# ---------------------------------------------------------------------------


@app.get("/api/field")
async def field() -> dict[str, Any]:
    """Every live decision, plus the premise stones and the load on each.

    The depth coordinate is TIME: `age_days` is how long before the corpus
    instant the decision was made, so older decisions sit further back. That is
    not decoration -- the whole point of the product is that decisions keep
    operating long after the premise under them died, and the field should show
    the age of what is at risk.
    """
    if "field" in _CACHE:
        return _CACHE["field"]

    store = _store()
    stats = _stats()

    nodes: list[dict[str, Any]] = []
    for index, (cid, conclusion) in enumerate(sorted(store.conclusions.items())):
        age = (CORPUS_AT - conclusion.decided_at).days
        nodes.append(
            {
                "i": index,
                "id": cid,
                "age": age,
                "esc": 1 if conclusion.external_effects else 0,
                "k": conclusion.kind.value,
                # Premise count drives how tightly a node is tethered.
                "p": len(conclusion.premise_ids),
            }
        )

    # Load-bearing stones: a claim, and the number of decisions resting on it.
    # Thickness in the UI is a function of this number and nothing else.
    stones: list[dict[str, Any]] = []
    for claim_id, edges in store.dependents.items():
        claim = store.get_claim(claim_id)
        if claim is None or not edges:
            continue
        stones.append(
            {
                "id": claim_id,
                "canonical": claim.canonical,
                "direct": len(edges),
                "source": claim.source_id,
                "value": claim.value,
            }
        )
    stones.sort(key=lambda s: (-s["direct"], s["id"]))

    payload = {
        "generated_at": CORPUS_AT.isoformat(),
        "counts": stats["counts"],
        "hub": stats["hub_claim"],
        "stones": stones[:60],
        "nodes": nodes,
        "debt": _debt_figure(),
        "timing": stats["timing"],
    }
    _CACHE["field"] = payload
    return payload


def _debt_figure() -> dict[str, Any]:
    """Causal debt: standing consequence on a normal day. Computed, not stated."""
    if "debt" in _CACHE:
        return _CACHE["debt"]
    from spine.debt import score_causal_debt

    store = _store()
    report = score_causal_debt(
        claims=list(store.claims.values()),
        conclusions=list(store.conclusions.values()),
        as_of=CORPUS_AT,
    )
    score = report.score
    payload = {
        "total": round(score.total, 2),
        "conclusions_scored": score.conclusions_scored,
        "claims_implicated": score.claims_implicated,
        "by_factor": {k: round(v, 2) for k, v in score.by_factor.items()},
        # Every contribution names its premise. A debt figure nobody can
        # attribute is a number on a dashboard, not a measure.
        "top_claims": score.top_claims[:5],
    }
    _CACHE["debt"] = payload
    return payload


# ---------------------------------------------------------------------------
# THE CASCADE, STREAMED
# ---------------------------------------------------------------------------


def _run(claim_id: str, source_id: str, new_value: float):
    """One real cascade. Cached per (claim, source, value) so a replay is cheap."""
    key = f"cascade::{claim_id}::{source_id}::{new_value}"
    if key not in _CACHE:
        from spine.cascade import run_cascade

        _CACHE[key] = run_cascade(
            store=_store(),
            claim_id=claim_id,
            source_id=source_id,
            new_value=new_value,
            reason="operator retraction",
            triggered_at=CORPUS_AT,
        )
    return _CACHE[key]


@app.get("/api/echo")
async def echo(
    claim: str = Query("clm_000000"),
    source: str = Query("src_supplier_K"),
    new_value: float = Query(20),
) -> dict[str, Any]:
    """The parse echo: what the system understood, BEFORE it acts.

    Served as its own endpoint rather than folded into the stream, because the
    whole point is that a human sees it and can say "not what I meant". A
    misparse must arrive as a question, never as a correction somebody receives.
    """
    result = _run(claim, source, new_value)
    store = _store()
    target = store.get_claim(claim)
    return {
        "read_as": {
            "canonical": target.canonical if target else claim,
            "from": target.value if target else None,
            "to": new_value,
        },
        "source": source,
        "affects_claim": claim,
        "carrying": len(result.radius),
        "authority": {
            "allowed": result.authority.allowed,
            "reason_code": result.authority.reason_code.value,
            "why": result.authority.reason,
        },
        "decision": {
            "state": result.decision_state,
            "why": (result.decision.why if result.decision else ""),
        },
    }


@app.get("/api/cascade/stream")
async def cascade_stream(
    claim: str = Query("clm_000000"),
    source: str = Query("src_supplier_K"),
    new_value: float = Query(20),
    pace_ms: float = Query(6.0, ge=0.0, le=200.0),
    batch: int = Query(12, ge=1, le=200),
) -> StreamingResponse:
    """The real traversal and scoring, streamed node by node.

    Each `node` event carries one conclusion's ACTUAL verdict from the cascade:
    its regime, depth, and the arithmetic that produced it. The client's counter
    decrements on arrival -- it is not a tween toward a known total, which is
    why the count on screen can never disagree with the events that produced it.

    `pace_ms` spaces the batches so a human can read the die-back. The pacing is
    reported in the `open` event and displayed by the UI; the DATA is untouched.
    """
    result = _run(claim, source, new_value)

    async def _events() -> AsyncIterator[str]:
        opening = {
            "claim_id": claim,
            "source_id": source,
            "new_value": new_value,
            "radius": len(result.radius),
            "authority_allowed": result.authority.allowed,
            "authority_reason": result.authority.reason_code.value,
            "decision_state": result.decision_state,
            "status": result.status.value,
            "model_calls": result.model_calls,
            "tier_reached": result.tier_reached,
            "paced_ms": pace_ms,
            "paced_note": (
                "Events are real cascade verdicts. Delivery is paced for legibility; "
                "the cascade itself completes in well under a second."
            ),
        }
        # Named `begin`, not `open`: EventSource fires a NATIVE `open` event when
        # the connection establishes, and a server-sent event of the same name
        # would land in the same listener with a different payload shape.
        yield _sse("begin", opening)

        if not result.authority.allowed:
            # A refusal has no radius to walk. Say why, and stop.
            yield _sse(
                "refused",
                {
                    "reason_code": result.authority.reason_code.value,
                    "why": result.authority.reason,
                    "decision_state": result.decision_state,
                },
            )
            yield _sse("done", {"radius": 0, "regimes": {}, "model_calls": 0})
            return

        # Depth order, so the wave reads as traversal rather than as a shuffle.
        ordered = sorted(result.radius.values(), key=lambda v: (v.depth, v.conclusion_id))
        sent = 0
        for start in range(0, len(ordered), batch):
            chunk = ordered[start : start + batch]
            yield _sse(
                "nodes",
                {
                    "n": [
                        {
                            "id": v.conclusion_id,
                            "d": v.depth,
                            "r": v.regime.value,
                            "esc": bool(v.escaped),
                            "slack": v.slack_days,
                            "shock": v.shock_days,
                        }
                        for v in chunk
                    ],
                    "sent": sent + len(chunk),
                },
            )
            sent += len(chunk)
            if pace_ms:
                await asyncio.sleep(pace_ms / 1000.0)

        counts = result.regime_counts()
        material = counts.get("material_escaped", 0) + counts.get("material_contained", 0)
        immaterial = counts.get("immaterial_escaped", 0) + counts.get("immaterial_contained", 0)
        yield _sse(
            "done",
            {
                "radius": len(result.radius),
                "regimes": counts,
                "material": material,
                "immaterial": immaterial,
                "closed_out": counts.get("closed_out", 0),
                "unresolved": counts.get("unresolved", 0),
                "model_calls": result.model_calls,
                "decision_state": result.decision_state,
                "status": result.status.value,
                "sent": sent,
            },
        )

    return StreamingResponse(
        _events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


# ---------------------------------------------------------------------------
# THE SPLIT AND THE OBLIGATION
# ---------------------------------------------------------------------------


@app.get("/api/survivors")
async def survivors(
    claim: str = Query("clm_000000"),
    source: str = Query("src_supplier_K"),
    new_value: float = Query(20),
) -> dict[str, Any]:
    """The two columns: correctable in place, versus already out of the building."""
    result = _run(claim, source, new_value)
    store = _store()

    reversible: list[dict] = []
    escaped: list[dict] = []
    for verdict in result.radius.values():
        if verdict.regime.value not in {"material_escaped", "material_contained"}:
            continue
        conclusion = store.get_conclusion(verdict.conclusion_id)
        if conclusion is None:
            continue
        row = {
            "id": verdict.conclusion_id,
            "kind": conclusion.kind.value,
            "decided_at": conclusion.decided_at.date().isoformat(),
            "age_days": (CORPUS_AT - conclusion.decided_at).days,
            "lead": conclusion.committed_lead_days,
            "shock": verdict.shock_days,
            "slack": verdict.slack_days,
        }
        if verdict.escaped:
            effect = conclusion.external_effects[0]
            row["sent_at"] = effect.occurred_at.date().isoformat()
            row["connector"] = effect.connector
            escaped.append(row)
        else:
            reversible.append(row)

    escaped.sort(key=lambda r: -r["age_days"])
    reversible.sort(key=lambda r: -r["age_days"])
    old = [r for r in escaped if r["age_days"] >= 120]
    return {
        "reversible": reversible,
        "escaped": escaped,
        "counts": {
            "reversible": len(reversible),
            "escaped": len(escaped),
            "escaped_120d_or_older": len(old),
        },
        "oldest_escaped_days": escaped[0]["age_days"] if escaped else 0,
    }


def _settlement(claim: str, source: str, new_value: float):
    key = f"settle::{claim}::{source}::{new_value}"
    if key not in _CACHE:
        from judgment.model import get_model
        from settle.pipeline import settle

        _CACHE[key] = settle(
            results=[_run(claim, source, new_value)],
            store=_store(),
            model=get_model(),
            now=CORPUS_AT,
            repair_id="rep_field",
        )
    return _CACHE[key]


@app.get("/api/obligation")
async def obligation(
    conclusion: str = Query("cnc_001211"),
    claim: str = Query("clm_000000"),
    source: str = Query("src_supplier_K"),
    new_value: float = Query(20),
) -> dict[str, Any]:
    """The real Task 4 object. Not a mock, not a template -- the same builder."""
    result = _settlement(claim, source, new_value)
    chosen = None
    for drafted in result.obligations:
        if drafted.conclusion_id == conclusion:
            chosen = drafted
            break
    if chosen is None and result.obligations:
        chosen = result.obligations[0]
    if chosen is None:
        raise HTTPException(404, "no obligation was raised for this cascade")

    ob = chosen.obligation
    exposure = ob.residual_exposure
    request = next((r for r in result.requests if r.obligation_id == ob.obligation_id), None)
    return {
        "obligation_id": ob.obligation_id,
        "conclusion_id": ob.conclusion_id,
        "status": ob.status.value,
        "approver": ob.approver,
        "ruling_id": ob.ruling_id,
        "counterparties": ob.counterparties,
        "tellings": [
            {
                "counterparty": t.counterparty,
                "told": t.told,
                "told_at": t.told_at.isoformat(),
                "connector": t.connector,
                "ref": t.effect_ref,
                "now": t.must_now_be_told,
            }
            for t in chosen.counterparty_map.tellings
        ],
        "reversible_actions": ob.reversible_actions,
        "unrecoverable": chosen.unrecoverable,
        "exposure": {
            "low": exposure.low,
            "high": exposure.high,
            "currency": exposure.currency,
            "assumptions": exposure.assumptions,
            "unpriced_effects": exposure.unpriced_effects,
        },
        "correction_text": chosen.correction_text,
        # The tag stays visible when true. A correction drafted without a model
        # is still a correction, and hiding that would be the lie.
        "drafted_without_model": "[drafted without a model" in chosen.correction_text,
        "signature_request": request.render() if request else None,
        "available": [d.conclusion_id for d in result.obligations],
    }


@app.get("/api/court")
async def court(
    claim: str = Query("clm_000000"),
    source: str = Query("src_supplier_K"),
    new_value: float = Query(20),
) -> dict[str, Any]:
    """Pleas, the ruling, and the dissent. Dissent is never dropped."""
    result = _settlement(claim, source, new_value)
    proceedings = result.proceedings
    if proceedings is None or proceedings.outcome is None:
        return {"convened": False, "why": "nothing in the radius was both material and escaped"}
    outcome = proceedings.outcome
    return {
        "convened": True,
        "repair_id": proceedings.repair.repair_id,
        "team_eligible": result.team.eligible,
        "team_seated": result.team.seated,
        "team_dissolved": result.team.dissolved,
        "turns_used": proceedings.turns_used,
        "converged": proceedings.converged,
        "budget": {
            "spent": proceedings.ledger.spent,
            "allowance": proceedings.ledger.allowance,
        },
        "pleas": [
            {
                "owner": p.member_owner_id,
                "conclusion": p.conclusion_id,
                "stance": p.stance.value,
                "evidence": p.evidence,
                "argument": p.argument,
            }
            for p in proceedings.repair.pleas
        ],
        "challenges": [
            {
                "from": c.challenger_owner_id,
                "to": c.target_owner_id,
                "resource": c.contested_resource,
            }
            for c in proceedings.repair.challenges
        ],
        "ruling": {
            "arbiter": outcome.ruling.arbiter_id,
            "decision": outcome.ruling.decision,
            "rationale": outcome.ruling.rationale,
            "advisory": outcome.ruling.advisory,
            "converged": outcome.ruling.converged,
        },
        "dissent": outcome.dissent,
        "obligations": len(result.obligations),
    }


@app.get("/api/loadrating")
async def loadrating(source: str = Query("src_supplier_K")) -> dict[str, Any]:
    """The compounding mechanism: a source that was wrong carries less next time."""
    from settle.loadrating import ledger_for

    record = _store().get_source(source)
    if record is None:
        raise HTTPException(404, f"unknown source {source}")
    ledger = ledger_for(record, at=CORPUS_AT)
    before = ledger.rating
    version = ledger.falsified(
        at=CORPUS_AT,
        claim_id="clm_000000",
        reason="the lead time this source asserted was superseded",
    )
    return {
        "source_id": source,
        "name": record.name,
        "before": before,
        "after": version.rating,
        "version": version.version,
        "falsifications": len(record.falsification_history) + 1,
        "reversible": True,
        "note": (
            "Source standing, not agent reputation. An agent can extract perfectly "
            "from a source that lies constantly; merging the two punishes the wrong "
            "party."
        ),
    }


# ---------------------------------------------------------------------------
# THE HONESTY PANEL
# ---------------------------------------------------------------------------


@app.get("/api/honesty")
async def honesty() -> dict[str, Any]:
    """Coverage including where it is bad, what is built, and the credentials gap."""
    from judgment.cli import _artifacts
    from judgment.coverage import audit

    cfg = get_config()
    report = audit(_artifacts(), as_of=CORPUS_AT)
    worst = report.worst_class

    # File EXISTENCE is not evidence: docs/LIVE-VERIFICATION.md ships as a
    # placeholder that documents the gap. Only a run of `make verify-live`
    # removes the marker, so the marker is what the panel reads.
    live_doc = REPO / "docs" / "LIVE-VERIFICATION.md"
    live_verified = (
        live_doc.is_file() and "NOT YET RUN" not in live_doc.read_text(encoding="utf-8")[:400]
    )
    return {
        "coverage": {
            "overall_recall": report.overall_recall,
            "artifacts_audited": report.artifacts_audited,
            "worst_class": worst.label if worst else None,
            "worst_recall": worst.recall if worst else None,
            "by_class": [
                {
                    "label": cov.label,
                    "gold": cov.gold,
                    "correct": cov.correct,
                    "wrong_value": cov.wrong_value,
                    "missed": cov.missed,
                    "recall": cov.recall,
                }
                for cov in sorted(report.by_class.values(), key=lambda c: c.label)
                if cov.gold
            ],
        },
        "credentials": {
            "vertex_disabled": cfg.vertex_disabled,
            "project": cfg.project_id,
            "location": cfg.vertex_location,
            "model_fast": cfg.model_fast,
            "model_deep": cfg.model_deep,
            "live_verification_present": live_verified,
            "note": (
                "No model call has been made from this repository. The Vertex smoke "
                "test was run and reported by the maintainer on their own machine. "
                "Every T2 number here came from a scripted stub and is labelled."
            ),
        },
        "built": [
            "Blast-radius traversal (T0, no model)",
            "Arithmetic materiality (T1, no model)",
            "Four-regime router + CLOSED-OUT",
            "Five-state decision router",
            "Authority gate + adversarial refusal",
            "Deterministic extractors + coverage auditor",
            "Blind re-deriver + separate assessor",
            "Repair court: owners, arbiter, four-turn protocol",
            "Correction obligations + approval broker",
            "Load rating (versioned, reversible)",
        ],
        "designed": [
            "Vertex T2 path (written, never executed here)",
            "Model Armor on the extraction path",
            "Compensation-path synthesis (deliberately refuses)",
            "Firestore rules + composite indexes (never deployed)",
            "infra/deploy.sh -> Cloud Run (never run)",
        ],
        "evidence": {
            "tests": "make test",
            "scenarios": "make eval",
            "vertex_off": "UNWIND_VERTEX_DISABLED=1 make eval",
        },
    }


# ---------------------------------------------------------------------------
# STATIC UI -- mounted last so it cannot shadow an API route
# ---------------------------------------------------------------------------

if STATIC.is_dir():

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
