"""Typed models for Control Tower's Firestore collections (Card 2).

Mirrors `lib/schema.py`'s discipline: every field that matters is typed before
any logic exists, because retrofitting a schema under live registry data is
worse than retrofitting one under live claims. Two things here are load-
bearing the same way Temporal Truth and authority_scope were in Task 1:

1. `WarrantSlot` exists now, empty, with a `provenance` field that can only be
   EARNED or SYNTHETIC. Card 0 mints into it in a later prompt. The field
   exists NOW so that "a demo balance is never mistaken for an earned one" is
   a schema constraint from the first document written, not a UI convention
   bolted on after the fact.
2. `balances` is `dict[str, int]` keyed by risk class, never a single int.
   File B §2: never a single global trust number. An agent that is highly
   warranted for LOW-risk delegation and has zero HIGH-risk warrant cannot be
   collapsed into one number without losing the fact that matters.

Nothing in this module makes a model call or touches the network.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    def to_firestore(self) -> dict[str, Any]:
        """Plain dict for the Firestore client. Enums flatten to their values."""
        return self.model_dump(mode="json", exclude_none=False)


# ===========================================================================
# agents/{agent_id} -- the executable registry
# ===========================================================================


class RegistryStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class WarrantProvenance(str, Enum):
    """Where a balance came from. Card 0 (a later prompt) is the only writer
    of EARNED; anything this prompt or a demo script produces is SYNTHETIC,
    and that label travels with the balance rather than living in a comment.
    """

    EARNED = "EARNED"
    SYNTHETIC = "SYNTHETIC"


class WarrantSlot(_Base):
    """Empty now. Card 0 mints, burns and decays this in a later prompt.

    This prompt builds the SLOT, not the arithmetic: `balances` starts empty,
    `provenance` starts SYNTHETIC, and nothing in Card 2 writes a nonzero
    value here. The gateway's WARRANT_INSUFFICIENT check therefore always
    passes today (there is nothing to be insufficient yet) -- see
    `tower/gateway.py:check_warrant`.
    """

    balances: dict[str, int] = Field(default_factory=dict)
    provenance: WarrantProvenance = WarrantProvenance.SYNTHETIC


class AgentRegistryEntry(_Base):
    """One row of the executable registry.

    `principal` binds this entry to `lib.principals` identity. Convention:
    `f"agent::{agent_id}"` -- `settle/broker.py` already treats the
    `"agent::"` prefix as an agent marker, so this reuses a vocabulary the
    repository already has rather than inventing a second one.
    """

    agent_id: str
    version: str
    capabilities: list[str] = Field(default_factory=list)
    authority_scope: list[str] = Field(default_factory=list)
    data_scope: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    max_budget: int
    #: Per risk-class thresholds, e.g. {"LOW": 100, "HIGH": 5}. Never a single
    #: global ceiling -- the same "never one number" discipline as warrant.
    risk_class_thresholds: dict[str, int] = Field(default_factory=dict)
    status: RegistryStatus = RegistryStatus.ACTIVE
    principal: str
    warrant: WarrantSlot = Field(default_factory=WarrantSlot)
    registered_at: datetime

    @property
    def is_eligible(self) -> bool:
        return self.status is RegistryStatus.ACTIVE


# ===========================================================================
# The Gateway's closed vocabulary of reason codes (Card 2's router)
# ===========================================================================


class GatewayReasonCode(str, Enum):
    """Checked in this exact order in `tower/gateway.py`. A closed vocabulary,
    the same discipline as `lib.schema.AuthorityReason` one level up: a
    refusal is a routed branch with a name, never a free-text message.
    """

    PRINCIPAL_VIOLATION = "PRINCIPAL_VIOLATION"
    SCOPE_EXCEEDED = "SCOPE_EXCEEDED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    WARRANT_INSUFFICIENT = "WARRANT_INSUFFICIENT"
    #: The failure-tolerant-routing branch (rubric-quoted): a worker that
    #: loops past its step ceiling or returns unparseable output is routed
    #: here, never retried silently.
    WORKER_FAULT = "WORKER_FAULT"
    ALLOWED = "ALLOWED"


class GatewayDecision(_Base):
    allowed: bool
    reason_code: GatewayReasonCode
    reason: str
    agent_id: str
    task: str
    checked_at: datetime


# ===========================================================================
# decision_memory/{entry_id} -- the append-only chain
# ===========================================================================


class MemoryEntryKind(str, Enum):
    CASE = "case"
    PREMISE = "premise"
    DECISION = "decision"
    AGENT_ACTION = "agent_action"
    HUMAN_DECISION = "human_decision"
    OUTCOME = "outcome"
    CONSEQUENCE = "consequence"


class MemoryEntry(_Base):
    """One link in the chain. `parent_id` is the entry that CAUSED this one to
    exist, so "what happened because of X" is a query over `parent_id`, not
    an embedding-similarity search -- there are no embeddings anywhere in
    this module, deliberately (locked decision: decision memory, not a
    vector store).
    """

    entry_id: str
    case_id: str
    kind: MemoryEntryKind
    payload: dict[str, Any] = Field(default_factory=dict)
    #: None only for the CASE entry that opens a chain.
    parent_id: str | None = None
    seq: int
    created_at: datetime


# ===========================================================================
# cases/{case_id} -- long-running durable runtime state
# ===========================================================================


class CaseStatus(str, Enum):
    OPEN = "open"
    PAUSED = "paused"
    AWAITING_HUMAN = "awaiting_human"
    RESUMED = "resumed"
    CLOSED = "closed"


class CaseRecord(_Base):
    """Persisted case state. `current_step` plus `step_state` is what lets a
    process restart resume from exactly where it left off rather than from
    the top of the case.
    """

    case_id: str
    status: CaseStatus
    current_step: str
    step_state: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime
    paused_at: datetime | None = None
    resumed_at: datetime | None = None
