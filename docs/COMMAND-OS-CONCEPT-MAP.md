# The 15-name concept map

These 15 names appear in the hackathon integration brief this project worked
from. **A repository-wide search finds zero hits for any of them** -- none
existed in this codebase before this document, as code, as a UI card, or as
a prior doc mention. There is therefore nothing to "integrate" under these
names; the only honest move is a mapping from each buzzword to the real
module that already provides that functional purpose, each with its own
truthful status.

Single source of truth: `command_os/concept_map.py` (this table is generated
from it, not maintained by hand in two places). Served live at
`GET /api/command-os/concept-map`.

| Name | Maps to | Real module | Status |
| --- | --- | --- | --- |
| FleetGuard | Governance + AgentOps | `tower/gateway.py (the one choke point), hyperion/guard.py` | LIVE |
| AutoAudit | Continuous Audit | `hyperion/immune_memory.py, singularity/mesh_memory.py (append-only logs + aggregates)` | LIVE |
| Self-Repairing Fleet | Self-Healing Engine | `command_os/mission.py stage 9 (re-negotiated genome + real re-mint via warrant/ledger.py)` | LIVE |
| Cross-Department Orchestrator | Master Orchestrator | `command_os/mission.py` | LIVE (orchestration) / DESIGNED (department-level routing) |
| Overlord AI | Supervisor / Policy Engine | `tower/gateway.py:evaluate_gateway` | LIVE |
| Phoenix | Repair + Recovery | `command_os/mission.py stages 9-10` | LIVE |
| ShadowAudit | Continuous Compliance / Audit | `hyperion/immune_memory.py, singularity/mesh_memory.py` | LIVE |
| OmniFleet | Cross-Department Fleet | `singularity/fleet.py (7-role reference topology)` | REFERENCE -- static topology, not a running fleet |
| Chronos-9 | Dynamic Agent Factory | `singularity/fleet.py:full_fleet()` | SIMULATED -- static roster, no live agent spawning |
| Aegis-Neuro | Distributed Defense | `hyperion/guard.py, hyperion/risk.py` | LIVE |
| Chronos-Void | Digital Twin / Simulation | `none` | DESIGNED -- not built, no simulation/forecasting engine exists |
| Pandora | Autonomous Red Team / Chaos Testing | `command_os/mission.py stage 4 (scripted adversarial observation)` | SIMULATED -- one scripted scenario per run, no autonomous red agent |
| Vigilante AI | Rogue Agent Detection | `singularity/behavior.py:detect_drift` | LIVE |
| Nexus Command | Command Center / Executive Control | `web/static (Agentic Command OS screen) + command_os/mission.py's report` | LIVE |
| Nebula OS | Autonomous DevOps Fleet | `infra/deploy.sh, Makefile deploy targets` | DESIGNED -- deploy is scripted, not agent-driven |

## Why fifteen cards were not built

A UI card with no function behind it is worse than no card: it is a claim
a judge cannot verify by clicking on it. The six cards that already existed
(UNWIND, WARRANT, CONTROL TOWER, COUNTERSIGN, HYPERION-ZERO, SINGULARITY-MESH)
stay exactly as they are -- see `docs/architecture.md` for how the Agentic
Command OS mission sequences real calls into several of the modules this
table names.
