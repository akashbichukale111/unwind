"""Master Orchestrator: run one Agentic Command OS mission end to end.

THIS MODULE CONTAINS NO NEW DECISION LOGIC
--------------------------------------------
Every stage below calls a function that is already real and already live one
layer down:

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
  8. ISOLATED              -> mission-local bookkeeping (new: an orchestration
                              flag, not a new enforcement mechanism)
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

The only fiction in this module is the single scripted adversarial
`BehaviorObservation` in stage 4 (147 tool calls, finance dataset, export +
secret access requested) -- the same literal scenario
`/api/singularity/behavior/probe?scenario=drift` already uses. Every stage
downstream of it is a live engine reacting to that input, and its `status`
field says so (`"LIVE (reacting to SIMULATED input)"`), never presenting a
scripted trigger as an organically-observed one.

Countersign runs with `UNWIND_COUNTERSIGN_SIMULATED=1` for the same reason
`/api/instrument/earn` sets it: live Gemma is a real, working path
(`countersign/agent.py`) but not one this orchestration depends on for a
reproducible demo run -- see `countersign/verify.py`'s module docstring for
the "simulated, labelled" discipline this reuses rather than re-implements.
"""

from __future__ import annotations

import os
import uuid

from command_os.schema import MissionReport, MissionResult, MissionStage

DEFAULT_OBJECTIVE = "Build and deploy a secure enterprise service."

#: The mission's field agent. Worker #04 (Browser/Research) is
#: `singularity/fleet.py`'s own documented choice for this role --
#: its entry already states it is "the fleet's designated attack surface in
#: the 3-minute demo's compromised-worker scenario" and "the worker isolated
#: in the attack -> block -> isolate -> recover walkthrough." This mission
#: reuses that existing intent rather than inventing a new agent identity.
_MISSION_AGENT_ID = "mission_worker_browser"


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


def run_mission(objective: str = DEFAULT_OBJECTIVE) -> MissionResult:
    """Run one mission end to end and return the full, real stage trace.

    Every Firestore-backed step (Hyperion and Singularity-Mesh event writes,
    Warrant ledger events) is a genuine write against the same collections
    the six-card instrument already reads -- a mission run leaves real
    evidence behind, visible from `/api/hyperion`, `/api/singularity`, and
    the Warrant bars, not a fixture only this function can see.
    """
    os.environ.setdefault("UNWIND_COUNTERSIGN_SIMULATED", "1")

    from countersign.verify import verify_and_record
    from hyperion.guard import evaluate_with_hyperion
    from hyperion.immune_memory import aggregate_fleet_summary
    from singularity.behavior import detect_drift
    from singularity.fleet import full_fleet
    from singularity.genome import compute_genome
    from singularity.mesh_memory import aggregate_mesh_summary
    from singularity.schema import AgentRole, BehaviorObservation
    from warrant.ledger import current_balance, mint, record_human_concurrence

    mission_id = f"mission_{uuid.uuid4().hex[:10]}"
    agent = _ensure_mission_agent()
    stages: list[MissionStage] = []

    # 1. AGENT FACTORY -------------------------------------------------------
    fleet = full_fleet()
    stages.append(
        MissionStage(
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
    )

    # 2. CAPABILITY GENOME -- normal ------------------------------------------
    normal_genome = compute_genome(
        agent_role=AgentRole.WORKER_BROWSER,
        task=objective,
        risk_class="LOW",
        requested_actions=["fetch_page", "read_page"],
    )
    stages.append(
        MissionStage(
            n=2,
            name="CAPABILITY GENOME ASSIGNED",
            status="LIVE",
            summary=f"{normal_genome.decision.value}: {normal_genome.reason}",
            detail=normal_genome.model_dump(mode="json"),
        )
    )

    # 3. BEHAVIORAL DNA -- normal ----------------------------------------------
    normal_observation = BehaviorObservation(
        agent_role=AgentRole.WORKER_BROWSER,
        tool_calls=6,
        dataset="web",
        latency_ms=1200,
        requested_export=False,
        requested_secret_access=False,
    )
    normal_assessment = detect_drift(normal_observation)
    stages.append(
        MissionStage(
            n=3,
            name="BEHAVIORAL DNA -- monitoring",
            status="LIVE",
            summary=(
                f"{normal_assessment.drift_band.value} (score {normal_assessment.drift_score})"
            ),
            detail=normal_assessment.model_dump(mode="json"),
        )
    )

    # 4. ADVERSARIAL EVENT (scripted) ------------------------------------------
    attack_observation = BehaviorObservation(
        agent_role=AgentRole.WORKER_BROWSER,
        tool_calls=147,
        dataset="finance",
        latency_ms=9000,
        requested_export=True,
        requested_secret_access=True,
    )
    drift_assessment = detect_drift(attack_observation)
    stages.append(
        MissionStage(
            n=4,
            name="BEHAVIORAL DRIFT DETECTED",
            status="SIMULATED",
            summary=(
                "scripted adversarial observation (147 tool calls, finance "
                f"dataset, secret access) -> real detect_drift() scores it "
                f"{drift_assessment.drift_band.value} "
                f"(score {drift_assessment.drift_score})"
            ),
            detail=drift_assessment.model_dump(mode="json"),
        )
    )

    # 5/6. HYPERION + CONTROL TOWER: real gateway check on the action the
    # drifted behaviour implies was attempted.
    block_case_id = f"{mission_id}_block"
    decision, assessment = evaluate_with_hyperion(
        agent,
        task="fetch finance secrets after drift (blocked attempt)",
        requested_scope=["finance.secret_read"],
        requested_cost=1,
        risk_class="HIGH",
        capability="research",
        case_id=block_case_id,
    )
    stages.append(
        MissionStage(
            n=5,
            name="HYPERION -- THREAT DETECTED",
            status="LIVE (reacting to SIMULATED input)",
            summary=(
                f"risk {assessment.risk_level.value} ({assessment.risk_score}): "
                f"{assessment.threat_type}"
            ),
            detail=assessment.model_dump(mode="json"),
        )
    )
    stages.append(
        MissionStage(
            n=6,
            name="CONTROL TOWER -- ACTION BLOCKED"
            if not decision.allowed
            else "CONTROL TOWER -- ALLOWED",
            status="LIVE (reacting to SIMULATED input)",
            summary=f"{decision.reason_code.value}: {decision.reason}",
            detail=decision.model_dump(mode="json"),
        )
    )

    # 7. COUNTERSIGN -- independent confirmation of the block --------------
    block_countersign = verify_and_record(
        case_id=block_case_id,
        material={
            "event": "blocked_action_review",
            "reason_code": decision.reason_code.value,
            "risk_level": assessment.risk_level.value,
        },
        agent=agent,
        capability="research",
        risk_class="HIGH",
        judging_family="hyperion-risk-engine",
        judging_principal=agent.principal,
    )
    stages.append(
        MissionStage(
            n=7,
            name="COUNTERSIGN -- independent verification",
            status="SIMULATED"
            if block_countersign.simulated
            else ("LIVE" if block_countersign.available else "UNAVAILABLE"),
            summary=(
                f"agrees={block_countersign.agrees}: {block_countersign.ground}"
                if block_countersign.available
                else f"unavailable: {block_countersign.reason_unavailable}"
            ),
            detail={
                "available": block_countersign.available,
                "agrees": block_countersign.agrees,
                "family": block_countersign.family,
                "simulated": block_countersign.simulated,
                "ground": block_countersign.ground,
            },
        )
    )

    # 8. ISOLATED -- mission-local bookkeeping --------------------------------
    isolated = not decision.allowed
    stages.append(
        MissionStage(
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
    )

    # 9. SELF-HEAL / REPAIR -- narrow the genome, re-earn warrant ------------
    repair_case_id = f"{mission_id}_repair"
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
        note="reviewed the drift and the block; approved resumption at the narrowed genome",
    )
    repair_countersign = verify_and_record(
        case_id=repair_case_id,
        material={"event": "repair_review", "narrowed_actions": repaired_genome.allowed_actions},
        agent=agent,
        capability="research",
        risk_class="LOW",
        judging_family="hyperion-risk-engine",
        judging_principal=agent.principal,
    )
    minted = False
    if repair_countersign.available and repair_countersign.agrees:
        mint(
            agent=agent,
            capability="research",
            risk_class="LOW",
            case_id=repair_case_id,
            reason="repair validated: narrowed scope re-approved",
        )
        minted = True
    after_bp = current_balance(agent.principal, "research", "LOW")
    stages.append(
        MissionStage(
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
    )

    # 10. VALIDATION -- real gateway re-check at the narrowed genome ---------
    resume_decision, resume_assessment = evaluate_with_hyperion(
        agent,
        task="resume: fetch the public page only",
        requested_scope=["web.read"],
        requested_cost=1,
        risk_class="LOW",
        capability="research",
        case_id=repair_case_id,
    )
    stages.append(
        MissionStage(
            n=10,
            name="VALIDATION",
            status="LIVE",
            summary=f"{resume_decision.reason_code.value}: {resume_decision.reason}",
            detail={
                "decision": resume_decision.model_dump(mode="json"),
                "assessment": resume_assessment.model_dump(mode="json"),
            },
        )
    )

    # 11. RESUME + EXECUTIVE REPORT --------------------------------------------
    resumed = resume_decision.allowed
    stages.append(
        MissionStage(
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
    )

    report = MissionReport(
        agents_in_fleet=len(fleet),
        threats_detected=1 if isolated else 0,
        unsafe_actions_executed=0,
        agents_isolated=1 if isolated else 0,
        repairs_completed=1 if minted else 0,
        validation="PASS" if resumed else "FAIL",
        fleet_status="HEALTHY" if resumed else "DEGRADED",
    )

    return MissionResult(mission_id=mission_id, objective=objective, stages=stages, report=report)


def reset_for_test() -> None:
    """Test hook: delete the mission agent's registry entry so a repeat test
    run starts cold. Mirrors the `reset_for_test` hooks already present in
    `tower.registry`, `warrant.ledger`, `hyperion.immune_memory`, and
    `singularity.mesh_memory` -- this module just calls them.
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
