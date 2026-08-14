"""The deploy preflight must fire on a broken deploy, not just pass on a good one.

`infra/deploy.sh` has never executed, so the preflight is the only thing standing
between a bad input and a failed Cloud Build six minutes in. R8 applies: every
guard ships with a vacuity test.

These tests exercise the two guards that already caught real defects during
Task 6 -- the region/location conflation and the wrong-artifact deploy -- plus
the over-broad-match bug the preflight itself had (it flagged a COMMENT
explaining why `adk deploy` is not used).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = (REPO / "infra" / "deploy.sh").read_text(encoding="utf-8")


def _invokes_adk(script: str) -> bool:
    """The same rule the preflight uses: an invocation, not a mention."""
    return any(
        line.strip().startswith("adk deploy")
        for line in script.splitlines()
        if not line.lstrip().startswith("#")
    )


# ---------------------------------------------------------------------------
# the wrong-artifact guard
# ---------------------------------------------------------------------------


def test_the_real_script_does_not_invoke_adk_deploy() -> None:
    """`adk deploy` serves the ADK dev UI, not web/static. It must not be used."""
    assert not _invokes_adk(SCRIPT)


def test_the_adk_guard_is_not_vacuous() -> None:
    """VACUITY: a script that really invokes it must be caught."""
    broken = "#!/usr/bin/env bash\nadk deploy cloud_run --project x agents\n"
    assert _invokes_adk(broken)


def test_the_adk_guard_does_not_fire_on_a_comment() -> None:
    """The complement, and the bug this check actually had.

    deploy.sh explains in a comment why it does NOT use `adk deploy`. A plain
    substring match flagged that prose as the defect it was warning about --
    a guard that cries wolf trains everyone to ignore it.
    """
    commented = (
        "#!/usr/bin/env bash\n# NOT `adk deploy cloud_run` -- see below\ngcloud run deploy x\n"
    )
    assert not _invokes_adk(commented)


# ---------------------------------------------------------------------------
# ⚠ the region / Vertex-location guard — the defect most likely to kill run #1
# ---------------------------------------------------------------------------


def test_cloud_run_region_is_never_derived_from_the_vertex_location() -> None:
    """`global` is a valid Vertex location and NOT a valid Cloud Run region.

    The previous script read `--region "${UNWIND_VERTEX_LOCATION:-us-central1}"`.
    Since the verified live run exports UNWIND_VERTEX_LOCATION=global, the first
    real deploy would have passed `--region global` and failed.
    """
    assert "UNWIND_RUN_REGION" in SCRIPT, "Cloud Run region has no variable of its own"
    # The --region flag must be fed by RUN_REGION, never by the Vertex location.
    region_lines = [ln for ln in SCRIPT.splitlines() if "--region" in ln]
    assert region_lines
    for line in region_lines:
        assert "VERTEX_LOCATION" not in line, f"region derived from Vertex location: {line}"


def test_the_script_refuses_a_global_cloud_run_region() -> None:
    assert 'RUN_REGION}" == "global"' in SCRIPT or "RUN_REGION == global" in SCRIPT, (
        "deploy.sh does not explicitly reject region=global"
    )


def test_vertex_location_is_still_passed_to_the_service() -> None:
    """Rejecting `global` as a REGION must not drop it as the Vertex LOCATION."""
    assert "UNWIND_VERTEX_LOCATION=${VERTEX_LOCATION}" in SCRIPT


# ---------------------------------------------------------------------------
# least privilege
# ---------------------------------------------------------------------------


def test_runtime_roles_are_least_privilege() -> None:
    roles = set(re.findall(r"roles/[a-zA-Z.]+", SCRIPT))
    assert {"roles/aiplatform.user", "roles/datastore.user", "roles/pubsub.publisher"} <= roles
    assert not ({"roles/owner", "roles/editor"} & roles), "over-broad role granted"


# ---------------------------------------------------------------------------
# the container entrypoint Cloud Run requires
# ---------------------------------------------------------------------------


def test_procfile_is_cloud_run_shaped() -> None:
    body = (REPO / "Procfile").read_text(encoding="utf-8")
    assert "services.api.main:app" in body, "the Procfile serves the wrong app"
    assert "0.0.0.0" in body, "Cloud Run requires binding 0.0.0.0"
    assert "PORT" in body, "Cloud Run injects $PORT and the container must honour it"


def test_the_dead_nextjs_skeleton_is_excluded_from_the_build() -> None:
    ignore = (REPO / ".dockerignore").read_text(encoding="utf-8")
    assert "web/app" in ignore, "buildpacks could detect a Node app and build the wrong thing"


# ---------------------------------------------------------------------------
# Firestore: gcloud cannot do either of these
# ---------------------------------------------------------------------------


def test_gcloud_is_not_asked_to_deploy_rules_or_an_index_file() -> None:
    """Neither command exists. `infra/indexes.json` is Firebase-format."""
    assert "gcloud firestore rules" not in SCRIPT
    assert "gcloud firestore indexes create --index-file" not in SCRIPT.replace("\\\n", " ")
