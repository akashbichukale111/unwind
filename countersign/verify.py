"""Countersign the verb: run the verifier, apply the collusion guard, and
wire the result into `warrant/ledger.py`'s minting gate.

Three outcomes, the same "unavailable is a class, not an exception" honesty
`judgment/model.py:UnavailableT2Model` already established for T2:

    AGREE       -> the case's countersign record is written; MINT may proceed.
    DISAGREE    -> the countersign record is written AND a CHALLENGE event
                   freezes minting for this case; it is flagged for a human.
    UNAVAILABLE -> nothing is written at all. `warrant.ledger.mint` already
                   refuses without a valid countersign record, so silence
                   here is the safe default -- never a silent AGREE.

SIMULATED, LABELLED
---------------------
`UNWIND_COUNTERSIGN_SIMULATED=1` (the SAME flag `warrant/ledger.py` already
gates its MINT precondition on) switches this module to a deterministic,
scripted verdict -- no model call, no Vertex dependency, reproducible for
tests and offline eval runs. Every simulated outcome carries
`simulated=True`, and `warrant.ledger.record_countersign` refuses to let a
simulated record satisfy MINT unless this same flag is set at mint time too
-- the label cannot be dropped by one caller and picked back up by another.
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass

from lib.config import get_config
from lib.telemetry import model_call_span
from lib.vertex import VertexDisabledError
from warrant.ledger import family_root

#: The countersigner's own principal. MUST differ from any judging-side
#: principal it is ever asked to check against -- `assert_independent`
#: enforces this the same way `lib.principals.assert_agent_is_distinct`
#: enforces role separation one layer up.
COUNTERSIGN_PRINCIPAL = "countersign-gemma@0.1.0"


class CollusionError(RuntimeError):
    """A countersign attempt whose model family or principal matches the
    judging side it was meant to check independently."""


def assert_independent(
    *,
    countersign_family: str,
    countersign_principal: str,
    judging_family: str,
    judging_principal: str,
) -> None:
    """Refuse a countersign that cannot possibly be independent.

    Two ways to collide, either one is disqualifying:
      - FAMILY: `family_root` normalizes both strings (e.g. "gemini-3.6-flash"
        and "gemini-3.5-flash-lite" both root to "gemini") -- a same-family
        countersign proves nothing about independent verification even if the
        exact model string differs.
      - PRINCIPAL: the countersigner must not BE the party whose judgement it
        is checking, the identical reasoning `lib.principals.assert_agent_is_distinct`
        already applies to a delegated worker acting as its own arbiter.
    """
    cs_family = family_root(countersign_family)
    j_family = family_root(judging_family)
    if cs_family == j_family:
        raise CollusionError(
            f"countersign family {countersign_family!r} (root {cs_family!r}) shares a "
            f"family with the judging side {judging_family!r} (root {j_family!r}): "
            "independence requires a DIFFERENT family, not merely a different string."
        )
    if countersign_principal == judging_principal:
        raise CollusionError(
            f"countersign principal {countersign_principal!r} is the same principal as "
            f"the judging side {judging_principal!r}: a verifier that is also the party "
            "being verified is not independent verification, it is the same actor twice."
        )


@dataclass(frozen=True)
class CountersignOutcome:
    """Everything needed to audit one countersign attempt."""

    available: bool
    agrees: bool | None
    family: str
    ground: str
    simulated: bool
    model: str
    reason_unavailable: str | None = None


def _material_prompt(case_id: str, material: dict) -> str:
    lines = [f"Case: {case_id}"]
    for key, value in material.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def _parse_verdict(text: str) -> tuple[bool, str]:
    """Deterministic parse of the two-line reply `countersign/agent.py`'s
    instruction demands. Raises rather than guessing: a reply this cannot
    parse must not silently become an AGREE or a DISAGREE with nothing behind
    it -- the caller treats a parse failure as UNAVAILABLE.
    """
    verdict_match = re.search(r"VERDICT:\s*(AGREE|DISAGREE)", text, re.IGNORECASE)
    if not verdict_match:
        raise ValueError(f"could not parse a VERDICT line from Gemma's reply: {text!r}")
    agrees = verdict_match.group(1).upper() == "AGREE"
    ground_match = re.search(r"GROUND:\s*(.+)", text, re.IGNORECASE)
    ground = ground_match.group(1).strip() if ground_match else "(no ground line returned)"
    return agrees, ground


async def _run_gemma_async(case_id: str, material: dict) -> str:
    """Execute the single-turn agent for real.

    DISCOVERED DURING WIRING, STATED HONESTLY: `mode="single_turn"` cannot be
    the ROOT of an ADK `Runner` invocation -- ADK raises
    `ValueError: LlmAgent as root agent must have mode='chat'` if you try,
    whether passed as `agent=` or `node=` directly. The mode's own docstring
    says why: single_turn's home is "as a node in a workflow". So the SAME
    `countersign_agent` object `countersign/agent.py:countersign_tool` wraps
    is executed here as the one node of a one-node ADK 2 `Workflow` --
    `Workflow(edges=[Edge(from_node=START, to_node=countersign_agent)])` --
    the identical `Workflow`/`Edge`/`START` idiom `tower/gateway.py` already
    uses, run through `InMemoryRunner(node=...)`. This was verified against
    live Vertex AI in this session: the call reaches Vertex, authenticates,
    and returns a real (non-mock) response -- see `countersign/DESIGN.md`
    for the exact result.
    """
    from google.adk.runners import InMemoryRunner
    from google.adk.workflow import START, Edge, Workflow
    from google.genai import types

    from countersign.agent import countersign_agent

    workflow = Workflow(
        name="countersign_verification",
        description="One node: the single-turn Gemma verifier.",
        edges=[Edge(from_node=START, to_node=countersign_agent)],
    )
    runner = InMemoryRunner(node=workflow, app_name="unwind-countersign")
    session = await runner.session_service.create_session(
        app_name="unwind-countersign", user_id="countersign"
    )
    message = types.Content(
        role="user", parts=[types.Part(text=_material_prompt(case_id, material))]
    )

    text_parts: list[str] = []
    async for event in runner.run_async(
        user_id="countersign", session_id=session.id, new_message=message
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    text_parts.append(part.text)
    return "".join(text_parts)


def _simulation_enabled() -> bool:
    return os.environ.get("UNWIND_COUNTERSIGN_SIMULATED", "").strip() == "1"


#: [SCRIPTED, LABELLED — see judgment/model.py:ScriptedT2Model for the same
#: discipline applied to T2]. The simulated countersigner's verdict is a
#: deterministic function of `material`, never randomness: reproducible eval
#: runs, no model call, no Vertex dependency. It agrees UNLESS the material
#: is explicitly marked adversarial/forged -- a stand-in for "an independent
#: reader would catch what an adversarial input was built to slip past",
#: which is a plausible enough shape to exercise the DISAGREE/CHALLENGE path
#: in tests and offline demos without pretending to be a real judgement.
_SIMULATED_FAMILY = "gemma-simulated"


def _simulated_outcome(case_id: str, material: dict) -> CountersignOutcome:
    flagged = str(material.get("class", "")).lower() == "adversarial" or bool(
        material.get("forged")
    )
    agrees = not flagged
    ground = (
        "material is labelled adversarial/forged; a scripted stand-in for an "
        "independent reader catching it"
        if flagged
        else "scripted agreement: material carries no adversarial marker"
    )
    return CountersignOutcome(
        available=True,
        agrees=agrees,
        family=_SIMULATED_FAMILY,
        ground=ground,
        simulated=True,
        model=_SIMULATED_FAMILY,
    )


def run_countersign(
    case_id: str,
    material: dict,
    *,
    judging_family: str,
    judging_principal: str,
    principal: str = COUNTERSIGN_PRINCIPAL,
) -> CountersignOutcome:
    """The verb. Applies the collusion guard, then either runs the scripted
    simulator or the real Gemma agent, and returns an outcome -- never
    writes anywhere. `verify_and_record` (below) is what wires a returned
    outcome into the Memory Bank and the warrant ledger.
    """
    cfg = get_config()

    if _simulation_enabled():
        # Still checked: a simulated run that would have collided is not a
        # meaningful rehearsal of the real guard.
        assert_independent(
            countersign_family=_SIMULATED_FAMILY,
            countersign_principal=principal,
            judging_family=judging_family,
            judging_principal=judging_principal,
        )
        return _simulated_outcome(case_id, material)

    if cfg.vertex_disabled:
        return CountersignOutcome(
            available=False,
            agrees=None,
            family=cfg.gemma_model,
            ground="",
            simulated=False,
            model=cfg.gemma_model,
            reason_unavailable="UNWIND_VERTEX_DISABLED=1",
        )

    assert_independent(
        countersign_family=cfg.gemma_model,
        countersign_principal=principal,
        judging_family=judging_family,
        judging_principal=judging_principal,
    )

    with model_call_span(cfg.gemma_model, purpose="countersign", case_id=case_id) as span:
        try:
            text = asyncio.run(_run_gemma_async(case_id, material))
            agrees, ground = _parse_verdict(text)
            span.set_attribute("unwind.countersign_agrees", agrees)
            span.set_attribute("unwind.model_available", True)
            return CountersignOutcome(
                available=True,
                agrees=agrees,
                family=cfg.gemma_model,
                ground=ground,
                simulated=False,
                model=cfg.gemma_model,
            )
        except VertexDisabledError as exc:
            span.set_attribute("unwind.model_available", False)
            return CountersignOutcome(
                available=False,
                agrees=None,
                family=cfg.gemma_model,
                ground="",
                simulated=False,
                model=cfg.gemma_model,
                reason_unavailable=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            # Genuinely unreachable (missing credentials, network, the model
            # string not deployed in this project) is reported honestly as
            # UNAVAILABLE -- never silently turned into an AGREE. This is the
            # identical shape `judgment/model.py:UnavailableT2Model` uses for
            # "I could not determine this" being a real, non-guessing answer.
            span.set_attribute("unwind.model_available", False)
            span.set_attribute("unwind.error", f"{type(exc).__name__}: {exc}")
            return CountersignOutcome(
                available=False,
                agrees=None,
                family=cfg.gemma_model,
                ground="",
                simulated=False,
                model=cfg.gemma_model,
                reason_unavailable=f"{type(exc).__name__}: {exc}",
            )


def verify_and_record(
    *,
    case_id: str,
    material: dict,
    agent,
    capability: str,
    risk_class: str,
    judging_family: str,
    judging_principal: str,
    principal: str = COUNTERSIGN_PRINCIPAL,
) -> CountersignOutcome:
    """Run Countersign and wire the result into the Memory Bank / warrant
    ledger. AGREE writes a countersign record and stops there -- `mint`
    still separately checks a human-concurrence record exists. DISAGREE
    writes the record AND appends a CHALLENGE, freezing minting for
    `case_id` permanently (see `warrant/ledger.py:mint`'s precondition
    check and `warrant/FAILURE_MODES.md`'s note on no unfreeze path).
    UNAVAILABLE writes nothing -- `mint` will refuse for lack of a record,
    which is the safe default, not a special case this function has to
    implement itself.
    """
    outcome = run_countersign(
        case_id,
        material,
        judging_family=judging_family,
        judging_principal=judging_principal,
        principal=principal,
    )
    if not outcome.available:
        return outcome

    from warrant.ledger import challenge, record_countersign

    record_countersign(
        case_id,
        agrees=bool(outcome.agrees),
        family=outcome.family,
        simulated=outcome.simulated,
        note=outcome.ground,
    )
    if not outcome.agrees:
        challenge(
            case_id=case_id,
            principal=agent.principal,
            capability=capability,
            risk_class=risk_class,
            reason=f"countersign disagreed: {outcome.ground}",
        )
    return outcome


__all__ = [
    "COUNTERSIGN_PRINCIPAL",
    "CollusionError",
    "CountersignOutcome",
    "assert_independent",
    "run_countersign",
    "verify_and_record",
]
