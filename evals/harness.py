"""Eval harness runner.

Task 1 ships the runner and the metric contract. There are ZERO scenarios; the
five class directories exist and are empty. A run over zero scenarios is a valid
run and exits 0 — but it writes a results file that says, in the file itself,
that nothing was evaluated. A harness that prints "all passed" over an empty set
is how a project convinces itself it is finished.

A scenario is a directory containing `scenario.json`:

    {
      "name": "hub-retraction-clean",
      "claim_id": "clm_000000",
      "new_value": 20,
      "expect": {"radius": 2004, "material": 94}
    }

Scenario execution requires the cascade, which is Task 2. Until then any
scenario file found is reported as SKIPPED with that reason, never as passed.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evals.metrics import METRICS, MetricResult, unavailable

SCENARIO_CLASSES = ("clean", "ambiguous", "adversarial", "tool_failure", "multi_premise")

CASCADE_NOT_BUILT = (
    "Cascade not built. Scenario execution needs the T0 traversal and the T1 "
    "materiality scorer, which are Task 2. Reported as SKIPPED, never as passed."
)


@dataclass
class ScenarioOutcome:
    scenario_class: str
    name: str
    status: str  # passed | failed | skipped
    reason: str | None = None
    metrics: list[MetricResult] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "class": self.scenario_class,
            "name": self.name,
            "status": self.status,
            "reason": self.reason,
            "metrics": [m.to_json() for m in self.metrics],
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


def run_scenario(scenario_class: str, path: Path) -> ScenarioOutcome:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ScenarioOutcome(
            scenario_class=scenario_class,
            name=path.parent.name,
            status="failed",
            reason=f"could not read scenario: {exc}",
        )
    return ScenarioOutcome(
        scenario_class=scenario_class,
        name=spec.get("name", path.parent.name),
        status="skipped",
        reason=CASCADE_NOT_BUILT,
        metrics=unavailable([m.key for m in METRICS], CASCADE_NOT_BUILT),
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

    report: dict[str, Any] = {
        "run_at": datetime.now(UTC).isoformat(),
        "stage": "task-1-scaffolding",
        "harness_version": "0.1.0",
        "python": platform.python_version(),
        "scenarios_discovered": len(discovered),
        "scenarios_passed": sum(1 for o in outcomes if o.status == "passed"),
        "scenarios_failed": sum(1 for o in outcomes if o.status == "failed"),
        "scenarios_skipped": sum(1 for o in outcomes if o.status == "skipped"),
        "empty_scenario_classes": empty_classes,
        "missing_scenario_classes": missing_classes,
        "metrics_defined": [m.key for m in METRICS],
        "metrics_computed": [],
        "note": (
            "NOTHING WAS EVALUATED. Task 1 defines the metrics and ships the runner; "
            "the scenarios and the cascade they exercise are Task 2 onward. No metric "
            "value in this repository has been measured."
            if not discovered
            else "Scenarios were discovered but not executed; see per-scenario reason."
        ),
        "outcomes": [o.to_json() for o in outcomes],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the UNWIND eval harness.")
    parser.add_argument("--scenarios", type=Path, default=Path("evals/scenarios"))
    parser.add_argument("--out", type=Path, default=Path("evals/results"))
    args = parser.parse_args(argv)

    report = run(args.scenarios, args.out)
    print(json.dumps(report, indent=2, sort_keys=True))

    if report["missing_scenario_classes"]:
        print(
            f"missing scenario classes: {report['missing_scenario_classes']}",
            file=sys.stderr,
        )
        return 1
    # Zero scenarios is a valid run. A failed scenario is not.
    return 1 if report["scenarios_failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
