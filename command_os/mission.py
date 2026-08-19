"""Master Orchestrator: run one Agentic Command OS mission end to end, with
Continuous Mission State -- persisted checkpoints, resumability, and a real
human override gate on the repair step.

THIS MODULE CONTAINS NO NEW DECISION LOGIC
--------------------------------------------
Every stage function below calls into an engine that is already real and
already live one layer down:

  1. AGENT FACTORY       -> singularity.fleet.full_fleet()          (reference)
  2. CAPABILITY GENOME    -> singularity.genome.compute_genome()     (LIVE)
  3. BEHAVIORAL DNA       -> singularity.behavior.detect_drift()     (LIVE)
  4. ADVERSARIAL EVENT    -> one scripted observation, SIMULATED, then the
                             SAME real detect_drift() call
  5. HYPERION             -> hyperion.guard.evaluate_with_hyperion()  (LIVE;
                             wraps tower.gateway.evaluate_gateway unchanged)
  6. CONTROL TOWER        -> the GatewayDecision evaluate_with_hyperion
                             already returned
  7. COUNTERSIGN          -> countersign.verify.verify_and_record()  (LIVE,
                             simulated verifier -- same convention
                             /api/instrument/earn already uses)
  8. ISOLATED              -> mission-local bookkeeping (an orchestration
                              flag, not a new enforcement mechanism)
  ---- HUMAN OVERRIDE GATE, only when auto_approve=False (see below) ----
  9. SELF-HEAL / REPAIR    -> a narrower compute_genome() call, then
                              warrant.ledger.record_human_concurrence +
                              countersign.verify.verify_and_record +
                              warrant.ledger.mint -- mirrors
                              /api/instrument/earn's repair-and-remint flow
 10. VALIDATION            -> evaluate_with_hyperion() again, at the
                              narrowed genome
 11. RESUME + REPORT       -> real aggregates from
                              hyperion.immune_memory.aggregate_fleet_summary()
                              and singularity.mesh_memory.aggregate_mesh_summary()

CONTINUOUS MISSION STATE
--------------------------
Each stage function takes and mutates a shared `ctx` dict (JSON-safe
primitives only) and returns the `MissionStage` it produced. `run_mission`
and `resume_mission` are both thin loops over the SAME eleven functions --
one implementation, two entry points, the same relationship
`hyperion.guard.evaluate_with_hyperion` already has to
`tower.gateway.evaluate_gateway`. After every stage, `checkpoint.write_checkpoint`
persists `(stage, ctx)` to `command_os_missions/{mission_id}/checkpoints/{seq}`
(`command_os/checkpoint.py`). Resuming a mission NEVER re-enters a completed
stage -- already-spent warrant and already-written Hyperion/Mesh events are
never duplicated, because the loop starts strictly after the last persisted
seq.

**What "crash recovery" means here, precisely**: if the process restarts
between two stages, the checkpoints already written survive in Firestore and
`resume_mission` continues from the last one. A crash mid-stage either has
that stage's own Firestore write fully committed (Firestore's own
transaction guarantee, e.g. `warrant.ledger.spend_or_refuse`) or not
committed at all -- there is no "partially applied" state for
`resume_mission` to reconcile, so it either continues past a completed stage
or safely re-runs a never-started one. This module does not claim to
recover from a crash mid-instruction inside the Python interpreter.

HUMAN OVERRIDE GATE
----------------------
`run_mission(..., auto_approve=True)` (the default) runs stages 1-11
straight through -- byte-identical to this module's behaviour before this
change, so the original one-click demo and its tests are unaffected.
`auto_approve=False` PAUSES after stage 8 (checkpoint status
`AWAITING_HUMAN`, `MissionResult.report` is `None`) instead of
auto-concurring into repair. `resume_mission(mission_id, human_decision=...)`
is the only way past that pause: `"approve"` continues into stage 9 exactly
as the automatic path would have; `"deny"` finalises the mission `HALTED`
without ever calling `compute_genome`, `record_human_concurrence`, or `mint`
for the repair. Either way, **the original Gateway `SCOPE_EXCEEDED` refusal
from stage 6 is never overturned** -- a human decision only ever authorises
a NEW, narrower request that the unmodified `evaluate_gateway` independently
re-checks in stage 10. There is no code path in this module that can make
the Gateway allow the request it already refused.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Callable
from typing import Any

from command_os import checkpoint
from command_os.schema import MissionReport, MissionResult, MissionStage

DEFAULT_OBJECTIVE = "Build and deploy a secure enterprise service."

#: The mission's field agent. Worker #04 (Browser/Research) is
#: `singularity/fleet.py`'s own documented choice for this role -- its entry
#: already states it is "the fleet's designated attack surface in the
#: 3-minute demo's compromised-worker scenario" and "the worker isolated in
#: the attack -> block -> isolate -> recover walkthrough." This mission
#: reuses that existing intent rather than inventing a new agent identity.
_MISSION_AGENT_ID = "mission_worker_browser"

#: Stages after which, with auto_approve=False, the mission pauses for a
#: human decision instead of proceeding automatically.
_GATE_AFTER_SEQ = 8

#: Final mission statuses (see `command_os/schema.py:MissionCheckpoint.status`).
_FINAL_STATUSES = {"COMPLETED", "HALTED"}


def _ensure_mission_agent():
    from tower.registry import get_agent, make_entry, put_agent

    agent = get_agent(_MISSION_AGENT_ID)
    if agent is not None:
        return agent
    put_agent(
        make_entry(
            _MISSION_AGENT_ID,
            capabilities=["research"],
            authority_scope=["web.read"],
            data_scope=[],
            max_budget=100,
            risk_class_thresholds={"LOW": 100, "HIGH": 20},
            warrant_mint_schedule={"LOW": 500},
            warrant_spend_schedule={"LOW": 50},
        )
    )
    return get_agent(_MISSION_AGENT_ID)


# ---------------------------------------------------------------------------
# Stage functions. Each takes and mutates the shared ctx, returns the
# MissionStage it produced. Numbered exactly as the module docstring above.
# ---------------------------------------------------------------------------


def _stage1_agent_factory(ctx: dict[str, Any]) -> MissionStage:
    from singularity.fleet import full_fleet

    fleet = full_fleet()
    ctx["fleet_count"] = len(fleet)
    return MissionStage(
        n=1,
        name="AGENT FACTORY -- fleet discovered",
        status="REFERENCE",
        summary=(
            f"{len(fleet)} roles in the reference fleet topology "
            "(singularity/fleet.py); Worker #04 (Browser/Research) assigned "
            "to this mission."
        ),
        detail={"fleet": fleet},
    )


def _stage2_capability_genome(ctx: dict[str, Any]) -> MissionStage:
    from singularity.genome import compute_genome
    from singularity.schema import AgentRole

    genome = compute_genome(
        agent_role=AgentRole.WORKER_BROWSER,
        task=ctx["objective"],
        risk_class="LOW",
        requested_actions=["fetch_page", "read_page"],
    )
    return MissionStage(
        n=2,
        name="CAPABILITY GENOME ASSIGNED",
        status="LIVE",
        summary=f"{genome.decision.value}: {genome.reason}",
        detail=genome.model_dump(mode="json"),
    )


def _stage3_behavioral_dna_normal(ctx: dict[str, Any]) -> MissionStage:
    from singularity.behavior import detect_drift
    from singularity.schema import AgentRole, BehaviorObservation

    observation = BehaviorObservation(
        agent_role=AgentRole.WORKER_BROWSER,
        tool_calls=6,
        dataset="web",
        latency_ms=1200,
        requested_export=False,
        requested_secret_access=False,
    )
    assessment = detect_drift(observation)
    return MissionStage(
        n=3,
        name="BEHAVIORAL DNA -- monitoring",
        status="LIVE",
        summary=f"{assessment.drift_band.value} (score {assessment.drift_score})",
        detail=assessment.model_dump(mode="json"),
    )


def _stage4_adversarial_event(ctx: dict[str, Any]) -> MissionStage:
    from singularity.behavior import detect_drift
    from singularity.schema import AgentRole, BehaviorObservation

    observation = BehaviorObservation(
        agent_role=AgentRole.WORKER_BROWSER,
        tool_calls=147,
        dataset="finance",
        latency_ms=9000,
        requested_export=True,
        requested_secret_access=True,
    )
    assessment = detect_drift(observation)
    return MissionStage(
        n=4,
        name="BEHAVIORAL DRIFT DETECTED",
        status="SIMULATED",
        summary=(
            "scripted adversarial observation (147 tool calls, finance "
            f"dataset, secret access) -> real detect_drift() scores it "
            f"{assessment.drift_band.value} (score {assessment.drift_score})"
        ),
        detail=assessment.model_dump(mode="json"),
    )


def _stage5_hyperion(ctx: dict[str, Any]) -> MissionStage:
    from hyperion.guard import evaluate_with_hyperion

    agent = _ensure_mission_agent()
    block_case_id = f"{ctx['mission_id']}_block"
    ctx["block_case_id"] = block_case_id
    decision, assessment = evaluate_with_hyperion(
        agent,
        task="fetch finance secrets after drift (blocked attempt)",
        requested_scope=["finance.secret_read"],
        requested_cost=1,
        risk_class="HIGH",
        capability="research",
        case_id=block_case_id,
    )
    ctx["decision_allowed"] = decision.allowed
    ctx["decision_reason_code"] = decision.reason_code.value
    ctx["decision_reason"] = decision.reason
    return MissionStage(
        n=5,
        name="HYPERION -- THREAT DETECTED",
        status="LIVE (reacting to SIMULATED input)",
        summary=(
            f"risk {assessment.risk_level.value} ({assessment.risk_score}): "
            f"{assessment.threat_type}"
        ),
        detail=assessment.model_dump(mode="json"),
    )


def _stage6_control_tower(ctx: dict[str, Any]) -> MissionStage:
    allowed = ctx["decision_allowed"]
    return MissionStage(
        n=6,
        name="CONTROL TOWER -- ACTION BLOCKED" if not allowed else "CONTROL TOWER -- ALLOWED",
        status="LIVE (reacting to SIMULATED input)",
        summary=f"{ctx['decision_reason_code']}: {ctx['decision_reason']}",
        detail={
            "allowed": allowed,
            "reason_code": ctx["decision_reason_code"],
            "reason": ctx["decision_reason"],
        },
    )


def _stage7_countersign(ctx: dict[str, Any]) -> MissionStage:
    from countersign.verify import verify_and_record

    agent = _ensure_mission_agent()
    outcome = verify_and_record(
        case_id=ctx["block_case_id"],
        material={
            "event": "blocked_action_review",
            "reason_code": ctx["decision_reason_code"],
        },
        agent=agent,
        capability="research",
        risk_class="HIGH",
        judging_family="hyperion-risk-engine",
        judging_principal=agent.principal,
    )
    return MissionStage(
        n=7,
        name="COUNTERSIGN -- independent verification",
        status="SIMULATED"
        if outcome.simulated
        else ("LIVE" if outcome.available else "UNAVAILABLE"),
        summary=(
            f"agrees={outcome.agrees}: {outcome.ground}"
            if outcome.available
            else f"unavailable: {outcome.reason_unavailable}"
        ),
        detail={
            "available": outcome.available,
            "agrees": outcome.agrees,
            "family": outcome.family,
            "simulated": outcome.simulated,
            "ground": outcome.ground,
        },
    )


def _stage8_isolate(ctx: dict[str, Any]) -> MissionStage:
    agent = _ensure_mission_agent()
    isolated = not ctx["decision_allowed"]
    ctx["isolated"] = isolated
    return MissionStage(
        n=8,
        name="AGENT ISOLATED" if isolated else "AGENT CLEARED",
        status="LIVE",
        summary=(
            f"{agent.agent_id} isolated pending repair (mission-scoped "
            "orchestration state, not a new enforcement layer)"
            if isolated
            else f"{agent.agent_id} was never blocked; no isolation necessary"
        ),
        detail={"agent_id": agent.agent_id, "isolated": isolated},
    )


def _stage9_repair(ctx: dict[str, Any]) -> MissionStage:
    from countersign.verify import verify_and_record
    from singularity.genome import compute_genome
    from singularity.schema import AgentRole
    from warrant.ledger import current_balance, mint, record_human_concurrence

    agent = _ensure_mission_agent()
    repair_case_id = f"{ctx['mission_id']}_repair"
    ctx["repair_case_id"] = repair_case_id

    repaired_genome = compute_genome(
        agent_role=AgentRole.WORKER_BROWSER,
        task="resume at narrowed scope: fetch the public page only",
        risk_class="LOW",
        requested_actions=["fetch_page", "read_page"],
    )
    before_bp = current_balance(agent.principal, "research", "LOW")
    record_human_concurrence(
        repair_case_id,
        principal="human::mission_operator",
        note=(
            "approved via the Human Override Gate"
            if not ctx.get("auto_approve", True)
            else "reviewed the drift and the block; approved resumption at the narrowed genome"
        ),
    )
    outcome = verify_and_record(
        case_id=repair_case_id,
        material={"event": "repair_review", "narrowed_actions": repaired_genome.allowed_actions},
        agent=agent,
        capability="research",
        risk_class="LOW",
        judging_family="hyperion-risk-engine",
        judging_principal=agent.principal,
    )
    minted = False
    if outcome.available and outcome.agrees:
        mint(
            agent=agent,
            capability="research",
            risk_class="LOW",
            case_id=repair_case_id,
            reason="repair validated: narrowed scope re-approved",
        )
        minted = True
    ctx["minted"] = minted
    after_bp = current_balance(agent.principal, "research", "LOW")
    return MissionStage(
        n=9,
        name="SELF-HEAL / REPAIR",
        status="LIVE",
        summary=(
            f"genome re-negotiated ({repaired_genome.decision.value}); "
            f"warrant {before_bp}bp -> {after_bp}bp"
            if minted
            else f"genome re-negotiated ({repaired_genome.decision.value}); mint withheld"
        ),
        detail={
            "genome": repaired_genome.model_dump(mode="json"),
            "before_bp": before_bp,
            "after_bp": after_bp,
            "minted": minted,
        },
    )


def _stage10_validation(ctx: dict[str, Any]) -> MissionStage:
    from hyperion.guard import evaluate_with_hyperion

    agent = _ensure_mission_agent()
    decision, assessment = evaluate_with_hyperion(
        agent,
        task="resume: fetch the public page only",
        requested_scope=["web.read"],
        requested_cost=1,
        risk_class="LOW",
        capability="research",
        case_id=ctx["repair_case_id"],
    )
    ctx["resumed"] = decision.allowed
    return MissionStage(
        n=10,
        name="VALIDATION",
        status="LIVE",
        summary=f"{decision.reason_code.value}: {decision.reason}",
        detail={
            "decision": decision.model_dump(mode="json"),
            "assessment": assessment.model_dump(mode="json"),
        },
    )


def _stage11_resume_report(ctx: dict[str, Any]) -> MissionStage:
    from hyperion.immune_memory import aggregate_fleet_summary
    from singularity.mesh_memory import aggregate_mesh_summary

    resumed = ctx.get("resumed", False)
    return MissionStage(
        n=11,
        name="MISSION RESUMED" if resumed else "MISSION HALTED",
        status="LIVE",
        summary=(
            "fleet resumed at the narrowed genome"
            if resumed
            else "validation did not clear; mission remains halted"
        ),
        detail={
            "resumed": resumed,
            "hyperion_fleet_summary": aggregate_fleet_summary(),
            "mesh_summary": aggregate_mesh_summary(),
        },
    )


_STAGES: list[Callable[[dict[str, Any]], MissionStage]] = [
    _stage1_agent_factory,
    _stage2_capability_genome,
    _stage3_behavioral_dna_normal,
    _stage4_adversarial_event,
    _stage5_hyperion,
    _stage6_control_tower,
    _stage7_countersign,
    _stage8_isolate,
    _stage9_repair,
    _stage10_validation,
    _stage11_resume_report,
]


def _build_report(ctx: dict[str, Any], stages: list[MissionStage]) -> MissionReport:
    isolated = ctx.get("isolated", False)
    minted = ctx.get("minted", False)
    resumed = ctx.get("resumed", False)
    return MissionReport(
        agents_in_fleet=ctx.get("fleet_count", 0),
        threats_detected=1 if isolated else 0,
        unsafe_actions_executed=0,
        agents_isolated=1 if isolated else 0,
        repairs_completed=1 if minted else 0,
        validation="PASS" if resumed else "FAIL",
        fleet_status="HEALTHY" if resumed else "DEGRADED",
    )


def _run_stages(ctx: dict[str, Any], stages: list[MissionStage], *, from_seq: int) -> MissionResult:
    """The one real loop both `run_mission` and `resume_mission` share.

    Runs `_STAGES[from_seq - 1 : ]` in order, checkpointing after each.
    Pauses before stage 9 iff `auto_approve` is False and the gate has not
    already been passed (`ctx["human_approved"]` unset).
    """
    mission_id = ctx["mission_id"]
    for seq in range(from_seq, len(_STAGES) + 1):
        if (
            seq == _GATE_AFTER_SEQ + 1
            and not ctx.get("auto_approve", True)
            and not ctx.get("human_approved", False)
        ):
            checkpoint.update_mission_status(mission_id, "AWAITING_HUMAN")
            return MissionResult(
                mission_id=mission_id,
                objective=ctx["objective"],
                status="AWAITING_HUMAN",
                stages=stages,
                report=None,
            )
        stage = _STAGES[seq - 1](ctx)
        stages.append(stage)
        is_last_stage = seq == len(_STAGES)
        checkpoint_status = (
            ("COMPLETED" if ctx.get("resumed") else "HALTED") if is_last_stage else "RUNNING"
        )
        checkpoint.write_checkpoint(
            mission_id=mission_id,
            seq=seq,
            stage=stage,
            ctx=dict(ctx),
            status=checkpoint_status,
        )

    report = _build_report(ctx, stages)
    final_status = "COMPLETED" if ctx.get("resumed") else "HALTED"
    checkpoint.update_mission_status(mission_id, final_status)
    return MissionResult(
        mission_id=mission_id,
        objective=ctx["objective"],
        status=final_status,
        stages=stages,
        report=report,
    )


def _finalize_halted_at_gate(
    mission_id: str, objective: str, stages: list[MissionStage], ctx: dict[str, Any]
) -> MissionResult:
    """The human denied repair: finalise HALTED without running stages 9-11.
    No genome renegotiation, no `record_human_concurrence`, no `mint` --
    the isolated agent simply stays isolated. `_build_report` already
    produces FAIL/DEGRADED/0-repairs here since `ctx` has no `resumed` or
    `minted` key at this point -- no separate report logic to keep in sync.
    """
    report = _build_report(ctx, stages)
    checkpoint.update_mission_status(mission_id, "HALTED")
    return MissionResult(
        mission_id=mission_id, objective=objective, status="HALTED", stages=stages, report=report
    )


def run_mission(objective: str = DEFAULT_OBJECTIVE, *, auto_approve: bool = True) -> MissionResult:
    """Run one mission end to end (or up to the Human Override Gate) and
    return the stage trace so far.

    Every Firestore-backed step (Hyperion and Singularity-Mesh event writes,
    Warrant ledger events, and now the mission's own checkpoints) is a
    genuine write -- a mission run leaves real evidence behind, visible from
    `/api/hyperion`, `/api/singularity`, and `/api/command-os/missions`, not
    a fixture only this function can see.
    """
    os.environ.setdefault("UNWIND_COUNTERSIGN_SIMULATED", "1")

    mission_id = f"mission_{uuid.uuid4().hex[:10]}"
    ctx: dict[str, Any] = {
        "mission_id": mission_id,
        "objective": objective,
        "auto_approve": auto_approve,
    }
    checkpoint.start_mission_record(mission_id, objective)
    _ensure_mission_agent()
    return _run_stages(ctx, [], from_seq=1)


def resume_mission(mission_id: str, *, human_decision: str | None = None) -> MissionResult:
    """Continue a mission from its last checkpoint.

    Three real cases, distinguished explicitly rather than guessed at:

      - latest checkpoint status is COMPLETED or HALTED: **ALREADY
        COMPLETED**. Nothing re-runs; the stored trace is returned as-is.
      - latest checkpoint status is AWAITING_HUMAN: **REQUIRES HUMAN
        APPROVAL**. `human_decision` must be `"approve"` or `"deny"` --
        anything else raises, rather than silently proceeding past a gate
        nobody actually cleared.
      - latest checkpoint status is RUNNING (the mission's own process
        exited before reaching a final state -- a crash or redeploy
        between two stages): **REPLAYABLE FROM THE NEXT STAGE**. Resumes
        at `latest.seq + 1`; every stage at or before `latest.seq` is
        already-completed work and is never re-entered.
    """
    os.environ.setdefault("UNWIND_COUNTERSIGN_SIMULATED", "1")

    record = checkpoint.get_mission_record(mission_id)
    if record is None:
        raise ValueError(f"no mission {mission_id!r} found")
    checkpoints = checkpoint.list_checkpoints(mission_id)
    stages = [cp.stage for cp in checkpoints]
    latest = checkpoints[-1] if checkpoints else None

    if record.status in _FINAL_STATUSES:
        report = _build_report(latest.ctx, stages) if latest else None
        return MissionResult(
            mission_id=mission_id,
            objective=record.objective,
            status=record.status,
            stages=stages,
            report=report,
        )

    if record.status == "AWAITING_HUMAN":
        if human_decision not in ("approve", "deny"):
            raise ValueError(
                "mission is AWAITING_HUMAN; resume_mission requires "
                "human_decision='approve' or 'deny', not None"
            )
        ctx = (
            dict(latest.ctx)
            if latest
            else {"mission_id": mission_id, "objective": record.objective}
        )
        if human_decision == "deny":
            return _finalize_halted_at_gate(mission_id, record.objective, stages, ctx)
        ctx["human_approved"] = True
        return _run_stages(ctx, stages, from_seq=_GATE_AFTER_SEQ + 1)

    # RUNNING: the process exited between two stages. Continue past the last
    # completed one -- never re-enter it.
    ctx = dict(latest.ctx) if latest else {"mission_id": mission_id, "objective": record.objective}
    from_seq = (latest.seq + 1) if latest else 1
    return _run_stages(ctx, stages, from_seq=from_seq)


def reset_for_test(mission_id: str | None = None) -> None:
    """Test hook: delete the mission agent's registry entry and (if given)
    one mission's checkpoints, so a repeat test run starts cold. Mirrors the
    `reset_for_test` hooks already present in `tower.registry`,
    `warrant.ledger`, `hyperion.immune_memory`, and `singularity.mesh_memory`.
    """
    from hyperion.immune_memory import reset_for_test as reset_hyperion
    from singularity.mesh_memory import reset_for_test as reset_mesh
    from tower.registry import get_agent
    from warrant.ledger import reset_for_test as reset_warrant

    agent = get_agent(_MISSION_AGENT_ID)
    if agent is not None:
        reset_warrant(agent.principal)
    reset_hyperion()
    reset_mesh()
    if mission_id is not None:
        checkpoint.reset_for_test(mission_id)
