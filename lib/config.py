"""Single source of configuration truth for UNWIND.

The Gemini model string appears HERE AND NOWHERE ELSE in this repository.
`make lint` is not what enforces that -- tests/test_config_singleton.py does,
by grepping the tree. If you need a model name somewhere else, import it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache

# ---------------------------------------------------------------------------
# Model + region. The ONLY model string in the repo.
# ---------------------------------------------------------------------------
# Verified 2026-08-12 against Google Cloud / Google AI model documentation:
# gemini-3.6-flash reached general availability on Vertex AI on 2026-07-21.
# The brief asked for "Gemini 3.5 or newer"; 3.6 Flash is the current GA Flash
# model and supersedes 3.5 Flash. See README "Model + version verification".
GEMINI_MODEL = "gemini-3.6-flash"

# Vertex AI region. Pinned, not inferred from ambient environment, so a cascade
# cannot silently move jurisdictions between runs.
VERTEX_LOCATION = "us-central1"


class Tier(str, Enum):
    """Tiered degradation (locked decision 1.2).

    T0 and T1 must survive a total Vertex outage. Membership is a property of
    the code path, declared here, so the guarantee is structural rather than a
    convention someone remembers.
    """

    T0 = "T0"  # blast-radius traversal over the reverse index. No model.
    T1 = "T1"  # arithmetic materiality on numeric/temporal claims. No model.
    T2 = "T2"  # ambiguous materiality, arbitration, drafting. Model required.


#: Tiers that are forbidden from making a model call, ever.
MODEL_FREE_TIERS: frozenset[Tier] = frozenset({Tier.T0, Tier.T1})


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    """Resolved runtime configuration."""

    project_id: str
    vertex_location: str
    gemini_model: str

    firestore_emulator_host: str | None
    firestore_database: str

    # When true, no Vertex client may be constructed. This is how the T0/T1
    # degradation guarantee gets *tested* in Task 2 rather than asserted.
    vertex_disabled: bool

    # When true, Pub/Sub uses the in-process shim instead of the real service.
    pubsub_local: bool

    pubsub_topics: tuple[str, ...] = field(default=())

    otel_service_name: str = "unwind"
    otel_console_export: bool = True

    @property
    def uses_emulator(self) -> bool:
        return self.firestore_emulator_host is not None

    @property
    def has_gcp_credentials(self) -> bool:
        """Best-effort: a real deployment sets one of these. Never assumed true."""
        return bool(
            os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            or os.environ.get("GOOGLE_CLOUD_PROJECT")
            and not self.uses_emulator
        )


# ---------------------------------------------------------------------------
# Pub/Sub topic names (locked list, brief 4.4)
# ---------------------------------------------------------------------------
TOPIC_CLAIM_RETRACTED = "claim.retracted"
TOPIC_NODE_REDERIVE = "node.rederive"
TOPIC_NODE_SCORED = "node.scored"
TOPIC_REPAIR_CONVENED = "repair.convened"
TOPIC_OBLIGATION_RAISED = "obligation.raised"
TOPIC_UNWIND_EXECUTED = "unwind.executed"

ALL_TOPICS: tuple[str, ...] = (
    TOPIC_CLAIM_RETRACTED,
    TOPIC_NODE_REDERIVE,
    TOPIC_NODE_SCORED,
    TOPIC_REPAIR_CONVENED,
    TOPIC_OBLIGATION_RAISED,
    TOPIC_UNWIND_EXECUTED,
)

# ---------------------------------------------------------------------------
# Firestore collection names
# ---------------------------------------------------------------------------
COLLECTION_CLAIMS = "claims"
COLLECTION_CONCLUSIONS = "conclusions"
COLLECTION_REVERSE_INDEX = "reverse_index"
COLLECTION_OBLIGATIONS = "obligations"
COLLECTION_REPAIRS = "repairs"
COLLECTION_SOURCES = "sources"
COLLECTION_AGENT_TRUST = "agent_trust"

#: Subcollection under reverse_index/{claim_id}
SUBCOLLECTION_DEPENDENTS = "dependents"

ALL_COLLECTIONS: tuple[str, ...] = (
    COLLECTION_CLAIMS,
    COLLECTION_CONCLUSIONS,
    COLLECTION_REVERSE_INDEX,
    COLLECTION_OBLIGATIONS,
    COLLECTION_REPAIRS,
    COLLECTION_SOURCES,
    COLLECTION_AGENT_TRUST,
)


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Resolve configuration once per process.

    Defaults are chosen so that a cold clone with no GCP account runs: emulator
    Firestore, in-process Pub/Sub, console telemetry.
    """
    emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST") or None
    project_id = (
        os.environ.get("UNWIND_PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or "unwind-local"
    )
    return Config(
        project_id=project_id,
        vertex_location=os.environ.get("UNWIND_VERTEX_LOCATION", VERTEX_LOCATION),
        gemini_model=GEMINI_MODEL,
        firestore_emulator_host=emulator_host,
        firestore_database=os.environ.get("UNWIND_FIRESTORE_DATABASE", "(default)"),
        vertex_disabled=_env_flag("UNWIND_VERTEX_DISABLED", default=False),
        pubsub_local=_env_flag("UNWIND_PUBSUB_LOCAL", default=emulator_host is not None),
        pubsub_topics=ALL_TOPICS,
        otel_service_name=os.environ.get("UNWIND_OTEL_SERVICE", "unwind"),
        otel_console_export=_env_flag("UNWIND_OTEL_CONSOLE", default=True),
    )


def reset_config_cache() -> None:
    """Test hook. Configuration is otherwise resolved once."""
    get_config.cache_clear()
