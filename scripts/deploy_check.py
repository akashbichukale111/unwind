"""`make deploy-check` — everything that can be wrong BEFORE spending a deploy.

Runs with no credentials and no network. It exists because `infra/deploy.sh`
has never executed, and the cheapest way to find a broken deploy is to check its
preconditions rather than to watch it fail six minutes into a build.

It fails loudly and specifically. Every check names the file and the fix.

⚠ IT CANNOT PROVE THE DEPLOY WORKS. It proves the inputs are consistent. The
only thing that proves a deploy works is `make deploy-verify URL=...` against a
live service, which asserts the deployed thing COMPUTES and not merely renders.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FAIL: list[str] = []
WARN: list[str] = []


def fail(check: str, problem: str, fix: str) -> None:
    FAIL.append(f"{check}\n      problem: {problem}\n      fix:     {fix}")


def warn(check: str, note: str) -> None:
    WARN.append(f"{check}: {note}")


def ok(check: str, detail: str = "") -> None:
    print(f"  PASS  {check}" + (f"  ({detail})" if detail else ""))


def main() -> int:
    print("=" * 70)
    print("UNWIND — deploy preflight (no credentials required)")
    print("=" * 70)

    deploy = REPO / "infra" / "deploy.sh"
    script = deploy.read_text(encoding="utf-8") if deploy.is_file() else ""

    # ---- 1. the script exists and parses -------------------------------
    if not script:
        fail("deploy.sh present", "infra/deploy.sh is missing", "restore it from git")
    else:
        result = subprocess.run(
            ["bash", "-n", str(deploy)], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            fail("deploy.sh parses", result.stderr.strip(), "fix the shell syntax")
        else:
            ok("deploy.sh parses")

    # ---- 2. ⚠ region vs Vertex location --------------------------------
    # The defect this check exists for: `global` is a valid VERTEX location and
    # is NOT a valid Cloud Run region. Passing one where the other belongs is
    # the single most likely way the first real deploy dies.
    from lib.config import VERTEX_LOCATION

    run_region = os.environ.get("UNWIND_RUN_REGION", "us-central1")
    if run_region == "global":
        fail(
            "Cloud Run region is a real region",
            "UNWIND_RUN_REGION=global — Cloud Run has no 'global' region",
            "unset it or set a region such as us-central1; Vertex stays 'global'",
        )
    else:
        ok("Cloud Run region is a real region", run_region)

    if VERTEX_LOCATION != "global":
        warn(
            "Vertex location",
            f"lib/config.py pins {VERTEX_LOCATION!r}, but the verified live run used "
            "'global'. Confirm this is intended.",
        )
    else:
        ok("Vertex location matches the verified live run", VERTEX_LOCATION)

    if script and "--region" in script and "UNWIND_RUN_REGION" not in script:
        fail(
            "deploy.sh separates region from Vertex location",
            "deploy.sh derives --region from the Vertex location",
            "use UNWIND_RUN_REGION for Cloud Run and UNWIND_VERTEX_LOCATION for Vertex",
        )
    elif script:
        ok("deploy.sh separates region from Vertex location")

    # ---- 3. the deployed artifact is the FastAPI app, not the ADK UI ----
    # Match an INVOCATION, not a mention: deploy.sh explains in a comment why it
    # does not use `adk deploy`, and a plain substring check flagged that prose
    # as the very defect it was warning about. Look for a line that actually
    # runs it -- not indented under a comment marker.
    invokes_adk = any(
        line.strip().startswith("adk deploy")
        for line in script.splitlines()
        if not line.lstrip().startswith("#")
    )
    if invokes_adk:
        fail(
            "deploys the product surface",
            "deploy.sh uses `adk deploy`, which serves the ADK API server / dev UI "
            "and would not serve web/static at all",
            "use `gcloud run deploy --source .` against services/api/main.py",
        )
    elif script and "gcloud run deploy" in script:
        ok("deploys the product surface", "gcloud run deploy --source .")

    # ---- 4. buildpack entrypoint ---------------------------------------
    procfile = REPO / "Procfile"
    if not procfile.is_file():
        fail(
            "Procfile present",
            "gcloud run deploy --source . uses buildpacks and needs an entrypoint",
            "create a Procfile with: web: uvicorn services.api.main:app "
            "--host 0.0.0.0 --port ${PORT:-8080}",
        )
    else:
        body = procfile.read_text(encoding="utf-8")
        if "services.api.main:app" not in body:
            fail(
                "Procfile serves the right app",
                f"Procfile does not reference services.api.main:app: {body.strip()!r}",
                "point it at services.api.main:app",
            )
        elif "0.0.0.0" not in body:
            fail(
                "Procfile binds 0.0.0.0",
                "Cloud Run requires binding 0.0.0.0, not 127.0.0.1",
                "use --host 0.0.0.0",
            )
        elif "PORT" not in body:
            fail(
                "Procfile honours $PORT",
                "Cloud Run injects $PORT and the container must listen on it",
                "use --port ${PORT:-8080}",
            )
        else:
            ok("Procfile binds 0.0.0.0 and honours $PORT")

    # ---- 5. one origin: the UI is actually served by the API ------------
    api = (REPO / "services" / "api" / "main.py").read_text(encoding="utf-8")
    static_dir = REPO / "web" / "static"
    needed = ["index.html", "app.js", "style.css"]
    missing = [f for f in needed if not (static_dir / f).is_file()]
    if missing:
        fail("UI files present", f"missing from web/static: {missing}", "restore them")
    elif "StaticFiles" not in api or "FileResponse" not in api:
        fail(
            "API serves the UI from one origin",
            "services/api/main.py does not mount web/static",
            "mount StaticFiles and serve index.html at /",
        )
    else:
        ok("API serves the UI from one origin", "3 static files + FastAPI")

    if (REPO / "web" / "package.json").is_file() and "next" in (
        REPO / "web" / "package.json"
    ).read_text(encoding="utf-8"):
        # Not a failure: the skeleton is documented as dead. But a deploy that
        # accidentally invoked it would be a second build system.
        if not (REPO / ".dockerignore").is_file():
            fail(
                "the dead Next.js skeleton is excluded from the build",
                "web/app exists and there is no .dockerignore, so buildpacks may "
                "detect a Node app and build the wrong thing",
                "add .dockerignore excluding web/app/ and node_modules/",
            )
        else:
            ignore = (REPO / ".dockerignore").read_text(encoding="utf-8")
            if "web/app" not in ignore:
                fail(
                    "the dead Next.js skeleton is excluded from the build",
                    ".dockerignore does not exclude web/app/",
                    "add 'web/app/' to .dockerignore",
                )
            else:
                ok("the dead Next.js skeleton is excluded from the build")

    # ---- 6. required env vars are named, not assumed --------------------
    for var in ("UNWIND_PROJECT_ID",):
        if script and var not in script:
            fail(f"{var} handled", f"deploy.sh never reads {var}", "read and validate it")
    if script and "Refusing to guess a project" in script:
        ok("refuses to guess a project")

    # ---- 7. IAM roles are least-privilege and named ---------------------
    expected_roles = {"roles/aiplatform.user", "roles/datastore.user", "roles/pubsub.publisher"}
    found = set(re.findall(r"roles/[a-zA-Z.]+", script))
    if not expected_roles <= found:
        fail(
            "runtime roles listed",
            f"deploy.sh is missing {sorted(expected_roles - found)}",
            "bind exactly those three roles to the runtime service account",
        )
    else:
        ok("runtime roles listed", ", ".join(sorted(expected_roles)))
    over = {r for r in found if r in {"roles/owner", "roles/editor"}}
    if over:
        fail("no over-broad roles", f"deploy.sh grants {sorted(over)}", "remove them")
    else:
        ok("no over-broad roles (no Owner/Editor)")

    # ---- 8. API enablement -----------------------------------------------
    needed_apis = {
        "aiplatform.googleapis.com",
        "firestore.googleapis.com",
        "pubsub.googleapis.com",
        "run.googleapis.com",
        "cloudbuild.googleapis.com",
    }
    missing_apis = {a for a in needed_apis if a not in script}
    if missing_apis:
        fail(
            "APIs enabled",
            f"deploy.sh does not enable {sorted(missing_apis)}",
            "add them to the gcloud services enable list",
        )
    else:
        ok("APIs enabled", f"{len(needed_apis)} services")

    # ---- 9. Pub/Sub wire names match lib/pubsub.py ------------------------
    from lib.config import ALL_TOPICS

    wire = {t.replace(".", "-") for t in ALL_TOPICS}
    missing_topics = {t for t in wire if t not in script}
    if missing_topics:
        fail(
            "Pub/Sub topics match lib/config.py",
            f"deploy.sh does not create {sorted(missing_topics)}",
            "topic ids are the config names with dots replaced by hyphens",
        )
    else:
        ok("Pub/Sub topics match lib/config.py", f"{len(wire)} topics")

    # ---- 10. Firestore: gcloud cannot deploy rules or an index FILE -------
    # `gcloud firestore indexes create --index-file=` and `gcloud firestore
    # rules release` are not gcloud commands. infra/indexes.json is in Firebase
    # format, so the Firebase CLI is the correct tool.
    if "gcloud firestore rules" in script:
        fail(
            "Firestore rules use the right tool",
            "`gcloud firestore rules release` is not a gcloud command",
            "deploy rules with the Firebase CLI: firebase deploy --only firestore:rules",
        )
    else:
        ok("Firestore rules are not deployed by gcloud")

    if "gcloud firestore indexes create --index-file" in script.replace("\\\n", " "):
        fail(
            "Firestore indexes use the right tool",
            "`gcloud firestore indexes create --index-file=` is not a gcloud flag",
            "deploy indexes with: firebase deploy --only firestore:indexes",
        )
    else:
        ok("Firestore indexes are not deployed by gcloud")

    idx = REPO / "infra" / "indexes.json"
    if idx.is_file():
        import json

        try:
            parsed = json.loads(
                "\n".join(line for line in idx.read_text(encoding="utf-8").splitlines())
            )
        except json.JSONDecodeError as exc:
            fail("indexes.json parses", str(exc), "fix the JSON")
        else:
            if "indexes" not in parsed:
                fail("indexes.json shape", "no top-level 'indexes' key", "use Firebase format")
            else:
                ok("indexes.json parses", f"{len(parsed['indexes'])} composite indexes")

    # ---- 11. container builds locally, if Docker is available -------------
    if shutil.which("docker"):
        print("  ....  docker found; attempting a local build (this is slow)")
        build = subprocess.run(
            ["docker", "build", "-q", "-t", "unwind-preflight", "."],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        stderr = build.stderr.strip()
        daemon_down = (
            "docker.sock" in stderr
            or "Cannot connect to the Docker daemon" in stderr
            or "daemon is running" in stderr
        )
        if build.returncode != 0 and daemon_down:
            # The binary exists but nothing is listening. That is an environment
            # fact, not a defect in this repository, and failing on it would
            # train everyone to ignore the preflight.
            warn(
                "container build",
                "docker binary present but the daemon is not running, so the "
                "build was NOT tested. Cloud Build will be the first to try it.",
            )
        elif build.returncode != 0:
            fail(
                "container builds locally",
                stderr[-400:],
                "fix the build before spending a Cloud Build minute",
            )
        else:
            ok("container builds locally")
    else:
        warn(
            "container build",
            "docker not available here, so the build was NOT tested. Cloud Build "
            "will be the first thing to try it.",
        )

    # ---- 12. the app imports without credentials --------------------------
    env = {**os.environ, "UNWIND_VERTEX_DISABLED": "1", "UNWIND_OTEL_CONSOLE": "0"}
    imp = subprocess.run(
        [sys.executable, "-c", "import services.api.main; print('ok')"],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if imp.returncode != 0 or "ok" not in imp.stdout:
        fail(
            "the app imports with no credentials",
            imp.stderr.strip()[-400:],
            "the container starts before any credential exists; imports must not need one",
        )
    else:
        ok("the app imports with no credentials")

    # ---- report -----------------------------------------------------------
    print("")
    for note in WARN:
        print(f"  WARN  {note}")
    if FAIL:
        print("")
        print("=" * 70, file=sys.stderr)
        print(f"DEPLOY PREFLIGHT FAILED — {len(FAIL)} problem(s)", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        for problem in FAIL:
            print(f"  FAIL  {problem}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Nothing was deployed.", file=sys.stderr)
        return 1

    print("")
    print("Preflight passed. This checks INPUTS, not the deploy itself.")
    print("Deploy with ./infra/deploy.sh, then prove it computes:")
    print("    make deploy-verify URL=https://...")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(REPO))
    raise SystemExit(main())
