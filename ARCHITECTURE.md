# UNWIND — architecture

One justifying sentence per component. A component without one gets deleted.

## The shape of the problem, in one line

A blast radius is a **graph traversal** (thousands of nodes, no model), the
survivors are an **arithmetic filter** (dozens of nodes, no model), and only what
survives both is worth a **model call**. Every choice below follows from that
ordering.

## Tiers

| Tier | What runs there | Model? | Why it is a tier and not a convention |
| --- | --- | --- | --- |
| T0 | Blast-radius traversal over the reverse index | No | A cascade over 2,004 dependents must not cost 2,004 model calls, and must still run when Vertex is down. |
| T1 | Arithmetic materiality on numeric/temporal claims | No | `shock > slack` is subtraction; asking a model to do subtraction is how you get a confidently wrong unwind. |
| T2 | Ambiguous materiality, arbitration, drafting | Yes | Judgement, argument and prose are the only places a model earns its latency. |

`UNWIND_VERTEX_DISABLED=1` closes the single door to a model
(`lib/vertex.py`), so "T0/T1 survive a Vertex outage" is testable rather than
asserted. Task 2 runs the full cascade with it set.

## Components

### `lib/config.py`
Holds the only Gemini model string and the only pinned region in the repository,
so a second model can never enter the system by accident (enforced by
`tests/test_config_singleton.py`, which greps the tree).

### `lib/schema.py`
Types every collection before any logic exists, because Temporal Truth
(`valid_from` / `invalidated_at` / `invalidation_reason`) and retraction
authority (`authority_scope`) are impossible to retrofit once thousands of
documents are written without them.

### `lib/firestore.py`
Gives the reverse index exactly one implementation to be correct in, and makes
the emulator a first-class target so the deterministic tier runs with no GCP
account.

### `lib/pubsub.py`
Carries the cascade fan-out, and wraps every consumer in `IdempotentConsumer`
because Pub/Sub is at-least-once and raising the same correction obligation
twice means apologising to a real customer twice.

### `lib/vertex.py`
Concentrates model access into one constructible object so the outage guarantee
has a single door to close — and pins the backend to Vertex AI, without which
ADK silently falls through to the developer Gemini API.

### `lib/telemetry.py`
Stamps `unwind.tier` on every span, so a T2 model call that leaked into a
supposedly model-free cascade shows up in a trace instead of in the bill.

### `agents/smoke/`
Proves ADK 2 + Vertex + `lib.config` are wired to each other, and is marked
delete-ready so it cannot quietly become load-bearing.

### `services/api/`
Serves the blast radius over SSE because a radius is discovered incrementally and
an operator needs to watch it fill in rather than wait for a total.

### `corpus/`
Is a deliverable, not a fixture: the die-back is **measured** off a stated model
of commercial behaviour, so the demo's central number is computed rather than
stipulated.

### `evals/`
Defines the metrics before any scenario exists, because a metric invented after
seeing results is a metric chosen to flatter them.

### `web/`
Reserves the operator surface and pins Next.js 15; Task 1 builds no UI and the
one page in it says so.

### `infra/`
Holds the composite index the reverse-index traversal cannot run without, the
rules that keep every write behind the service identity, and a deploy script that
wraps `adk deploy` rather than hand-rolling a container the framework already
builds.

## Google Cloud services

Four, each justified in one sentence. Nothing else is used.

| Service | One sentence |
| --- | --- |
| **Firestore** | Document-shaped decisions with a subcollection reverse index, and a local emulator so the deterministic tier needs no cloud account. |
| **Pub/Sub** | The cascade is a fan-out from one dead claim to thousands of independent re-derivations, which is exactly what a topic is for. |
| **Cloud Run** | `adk deploy cloud_run` is the framework's own path, and a cascade is bursty work that should scale to zero between retractions. |
| **Vertex AI** | The only T2 dependency: ambiguous materiality, the repair court, and drafting the correction that goes to a counterparty. |

Deliberately **NOT USED**: GKE (Cloud Run already runs the container, and
`adk deploy gke` would add a cluster nobody needs), Cloud SQL and Spanner
(the data is documents with a subcollection index, not relations), BigQuery
(2,004 rows per cascade is not an analytics workload), Dataflow (Pub/Sub plus
Cloud Run is the whole pipeline), Redis and Memorystore (Firestore holds the
idempotency keys, and a second datastore is a second thing to be inconsistent).

## ADK 2 features, and what each one is for here

Verified present in `google-adk` 2.6.3 (`google.adk.workflow`, `google.adk.tools`).

| ADK 2 feature | Where UNWIND needs it |
| --- | --- |
| `FunctionNode` | T0 traversal and T1 materiality: deterministic nodes with no model call. |
| `Workflow` + `Edge` / `DEFAULT_ROUTE` | The four-regime split is a **router**, not a prompt — the core novelty must not be able to hallucinate. |
| `AgentTool` (agent-as-tool) | The repair court: a parent runs a subset of sub-agents in parallel and keeps control. |
| Dynamic node scheduling | The repair team is composed at runtime from a blast radius that did not exist a second earlier. |
| `LongRunningFunctionTool` | Durable pause/resume: a human may sign a correction obligation on Tuesday. |

## The write path

UNWIND's output is **corrections that leave the building** — a re-issued quote, a
compensation, a signed apology. The reverse index, the authority gate and the
traces exist to make that write path safe; they are not the product.
