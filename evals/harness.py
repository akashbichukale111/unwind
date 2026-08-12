"""Eval harness runner.

Scenarios are marked against `corpus/data/radius_truth.jsonl`. That file is the
MARKING SCHEME: the harness reads it, the cascade must never touch it.
`tests/test_ground_truth_isolation.py` enforces that, because a cascade that can
read its own answer key would score perfectly and prove nothing.

A run over zero scenarios is still a valid run and exits 0, but it writes a
results file that says in the file itself that nothing was evaluated.

Metric values are computed here from the cascade's output and the marking
scheme. Nothing is stated as measured that this file did not measure.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evals.metrics import METRICS, MetricResult, unavailable

REPO = Path(__file__).resolve().parents[1]

SCENARIO_CLASSES = ("clean", "ambiguous", "adversarial", "tool_failure", "multi_premise")


@dataclass
class ScenarioOutcome:
    scenario_class: str
    name: str
    status: str  # passed | failed | skipped
    reason: str | None = None
    metrics: list[MetricResult] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "class": self.scenario_class,
            "name": self.name,
            "status": self.status,
            "reason": self.reason,
            "metrics": [m.to_json() for m in self.metrics],
            "detail": self.detail,
        }


def discover(scenarios_dir: Path) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    for scenario_class in SCENARIO_CLASSES:
        class_dir = scenarios_dir / scenario_class
        if not class_dir.is_dir():
            continue
        for path in sorted(class_dir.glob("*/scenario.json")):
            found.append((scenario_class, path))
    return found


def _load_ground_truth(rel_path: str) -> dict[str, dict[str, Any]]:
    path = REPO / rel_path
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    return {row["conclusion_id"]: row for row in rows}


def _score(
    result: Any, truth: dict[str, dict[str, Any]], elapsed_s: float
) -> tuple[list[MetricResult], dict[str, Any]]:
    """Compute every metric from the cascade result against the marking scheme."""
    found = set(result.radius)
    expected = set(truth)
    hits = found & expected

    recall = len(hits) / len(expected) if expected else 0.0
    precision = len(hits) / len(found) if found else 0.0

    # Marked against `live_material`, not `material`. The marking scheme records
    # both: `material` is the buffer arithmetic alone, `live_material` also
    # requires the commitment to be open at the retraction. The second is the
    # operationally correct definition -- a delivery completed in March cannot be
    # harmed by a premise that moved in July -- so it is what the cascade is held
    # to. Marking against `material` would credit the cascade for alerting on
    # commitments that already discharged.
    scoreable = [c for c in hits if not truth[c]["unresolvable"]]
    agreed = 0
    disagreed: list[str] = []
    for conclusion_id in scoreable:
        verdict = result.radius[conclusion_id]
        if verdict.material is None:
            disagreed.append(conclusion_id)
            continue
        if verdict.material == truth[conclusion_id]["live_material"]:
            agreed += 1
        else:
            disagreed.append(conclusion_id)
    materiality_accuracy = agreed / len(scoreable) if scoreable else None

    escapement_agreed = sum(1 for c in hits if result.radius[c].escaped == truth[c]["escaped"])
    escapement_accuracy = escapement_agreed / len(hits) if hits else None

    unresolved = [c for c in found if result.radius[c].material is None]
    unresolved_rate = len(unresolved) / len(found) if found else 0.0

    # A false retraction is an unwind action against something the marking
    # scheme says was NOT materially harmed. In this task the only "action" a
    # cascade takes is landing a node in a MATERIAL regime, so that is what is
    # counted. Task 4 widens this to actual outbound corrections.
    acted_on = [c for c in hits if result.radius[c].material is True]
    false_actions = [c for c in acted_on if not truth[c]["live_material"]]
    false_retraction_rate = len(false_actions) / len(acted_on) if acted_on else 0.0
    if result.authority.allowed is False:
        # A refused retraction that still cascaded would be the worst failure
        # available; treat any radius at all as wholly false.
        false_retraction_rate = 1.0 if found else 0.0

    results = [
        MetricResult(
            "blast_radius_recall", recall, detail={"found": len(found), "expected": len(expected)}
        ),
        MetricResult("blast_radius_precision", precision, detail={"hits": len(hits)}),
        MetricResult(
            "materiality_accuracy",
            materiality_accuracy,
            unavailable_reason=None if scoreable else "no arithmetically scoreable nodes",
            detail={"scored": len(scoreable), "disagreements": sorted(disagreed)[:20]},
        ),
        MetricResult(
            "false_retraction_rate",
            false_retraction_rate,
            detail={"acted_on": len(acted_on), "false": sorted(false_actions)[:20]},
        ),
        MetricResult("escapement_accuracy", escapement_accuracy),
        MetricResult(
            "human_escalation_precision",
            None,
            unavailable_reason="No escalation path exists yet; ASK_HUMAN is Task 3.",
        ),
        MetricResult("unresolved_rate", unresolved_rate, detail={"unresolved": len(unresolved)}),
        MetricResult(
            "cost_per_cascade",
            0.0,
            detail={
                "model_calls": result.model_calls,
                "note": "Zero by construction: this cascade is T0+T1 and makes no model call.",
            },
        ),
        MetricResult(
            "time_to_obligation",
            None,
            unavailable_reason="Obligations are Task 4. Wall-clock for the cascade itself "
            f"was {elapsed_s:.3f}s.",
        ),
    ]
    detail = {
        "cascade_id": result.cascade_id,
        "authority": result.authority.to_json(),
        "tier_reached": result.tier_reached,
        "model_calls": result.model_calls,
        "elapsed_seconds": round(elapsed_s, 4),
        "regime_counts": result.regime_counts(),
        "radius_size": len(found),
        "ground_truth_size": len(expected),
    }
    return results, detail


def run_scenario(scenario_class: str, path: Path) -> ScenarioOutcome:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ScenarioOutcome(
            scenario_class, path.parent.name, "failed", f"could not read scenario: {exc}"
        )

    name = spec.get("name", path.parent.name)
    try:
        from spine.cascade import CorpusStore, run_cascade
    except ImportError as exc:
        return ScenarioOutcome(
            scenario_class,
            name,
            "failed",
            f"cascade is not implemented: {exc}",
            metrics=unavailable([m.key for m in METRICS], "cascade not implemented"),
        )

    retraction = spec["retraction"]
    truth = _load_ground_truth(spec["ground_truth"])
    triggered_at = (
        datetime.fromisoformat(retraction["triggered_at"].replace("Z", "+00:00"))
        if retraction.get("triggered_at")
        else None
    )

    started = time.perf_counter()
    try:
        result = run_cascade(
            store=CorpusStore.from_repo(REPO),
            claim_id=retraction["claim_id"],
            source_id=retraction["source_id"],
            new_value=retraction["new_value"],
            reason=retraction.get("reason", ""),
            triggered_at=triggered_at,
        )
    except Exception as exc:  # noqa: BLE001 - a crashed cascade is a failed scenario
        return ScenarioOutcome(
            scenario_class,
            name,
            "failed",
            f"cascade raised {type(exc).__name__}: {exc}",
            metrics=unavailable([m.key for m in METRICS], "cascade raised"),
        )
    elapsed = time.perf_counter() - started

    metrics, detail = _score(result, truth, elapsed)
    by_key = {m.key: m for m in metrics}

    failures: list[str] = []
    expect = spec.get("expect", {})
    if "authority" in expect:
        actual = "allow" if result.authority.allowed else "refuse"
        if actual != expect["authority"]:
            failures.append(f"authority: expected {expect['authority']}, got {actual}")
    if "model_calls" in expect and result.model_calls != expect["model_calls"]:
        failures.append(f"model_calls: expected {expect['model_calls']}, got {result.model_calls}")
    if "tier_reached" in expect and result.tier_reached != expect["tier_reached"]:
        failures.append(
            f"tier_reached: expected {expect['tier_reached']}, got {result.tier_reached}"
        )
    for key in (
        "blast_radius_recall",
        "blast_radius_precision",
        "materiality_accuracy",
        "false_retraction_rate",
    ):
        if key not in expect:
            continue
        value = by_key[key].value
        if value is None or abs(value - expect[key]) > 1e-9:
            failures.append(f"{key}: expected {expect[key]}, got {value}")

    return ScenarioOutcome(
        scenario_class,
        name,
        "failed" if failures else "passed",
        "; ".join(failures) if failures else None,
        metrics=metrics,
        detail=detail,
    )


def run(scenarios_dir: Path, out_dir: Path) -> dict[str, Any]:
    discovered = discover(scenarios_dir)
    outcomes = [run_scenario(cls, path) for cls, path in discovered]

    missing_classes = [c for c in SCENARIO_CLASSES if not (scenarios_dir / c).is_dir()]
    empty_classes = [
        c
        for c in SCENARIO_CLASSES
        if (scenarios_dir / c).is_dir() and not any((scenarios_dir / c).glob("*/scenario.json"))
    ]

    computed = sorted({m.key for o in outcomes for m in o.metrics if m.value is not None})
    report: dict[str, Any] = {
        "run_at": datetime.now(UTC).isoformat(),
        "stage": "task-2-deterministic-spine",
        "harness_version": "0.2.0",
        "python": platform.python_version(),
        "scenarios_discovered": len(discovered),
        "scenarios_passed": sum(1 for o in outcomes if o.status == "passed"),
        "scenarios_failed": sum(1 for o in outcomes if o.status == "failed"),
        "scenarios_skipped": sum(1 for o in outcomes if o.status == "skipped"),
        "empty_scenario_classes": empty_classes,
        "missing_scenario_classes": missing_classes,
        "metrics_defined": [m.key for m in METRICS],
        "metrics_computed": computed,
        "total_model_calls": sum(o.detail.get("model_calls", 0) for o in outcomes if o.detail),
        "note": (
            "NOTHING WAS EVALUATED. No scenarios were discovered."
            if not discovered
            else "Metric values below were computed by this harness from the cascade "
            "output and corpus/data/radius_truth.jsonl."
        ),
        "outcomes": [o.to_json() for o in outcomes],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # A second, DETERMINISTIC file. `latest.json` carries a run timestamp and a
    # wall-clock duration, so it changes on every run and cannot be diffed
    # against a committed copy. The summary strips exactly those fields, which
    # makes "the committed results still match the code" a check CI can enforce
    # rather than a claim in a README.
    (out_dir / "summary.json").write_text(
        json.dumps(_deterministic_summary(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _deterministic_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Everything in the report that is reproducible from the committed inputs."""
    return {
        "stage": report["stage"],
        "harness_version": report["harness_version"],
        "scenarios_discovered": report["scenarios_discovered"],
        "scenarios_passed": report["scenarios_passed"],
        "scenarios_failed": report["scenarios_failed"],
        "scenarios_skipped": report["scenarios_skipped"],
        "total_model_calls": report["total_model_calls"],
        "metrics_computed": report["metrics_computed"],
        "outcomes": [
            {
                "class": outcome["class"],
                "name": outcome["name"],
                "status": outcome["status"],
                "reason": outcome["reason"],
                "cascade_id": outcome["detail"].get("cascade_id"),
                "radius_size": outcome["detail"].get("radius_size"),
                "ground_truth_size": outcome["detail"].get("ground_truth_size"),
                "regime_counts": outcome["detail"].get("regime_counts"),
                "tier_reached": outcome["detail"].get("tier_reached"),
                "model_calls": outcome["detail"].get("model_calls"),
                "metrics": {
                    m["key"]: m["value"] for m in outcome["metrics"] if m["value"] is not None
                },
            }
            for outcome in report["outcomes"]
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the UNWIND eval harness.")
    parser.add_argument("--scenarios", type=Path, default=Path("evals/scenarios"))
    parser.add_argument("--out", type=Path, default=Path("evals/results"))
    parser.add_argument("--quiet", action="store_true", help="Print the summary only.")
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Export spans to the console. Off by default: this command's stdout "
        "is a JSON report, and span output would corrupt it.",
    )
    args = parser.parse_args(argv)

    # Must be set before the first span is opened, since telemetry configures
    # itself lazily on first use.
    os.environ["UNWIND_OTEL_CONSOLE"] = "1" if args.trace else "0"

    report = run(args.scenarios, args.out)
    if args.quiet:
        print(
            f"scenarios: {report['scenarios_passed']} passed, "
            f"{report['scenarios_failed']} failed, "
            f"{report['scenarios_skipped']} skipped; "
            f"model calls: {report['total_model_calls']}"
        )
    else:
        print(json.dumps(report, indent=2, sort_keys=True))

    if report["missing_scenario_classes"]:
        print(f"missing scenario classes: {report['missing_scenario_classes']}", file=sys.stderr)
        return 1
    return 1 if report["scenarios_failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
