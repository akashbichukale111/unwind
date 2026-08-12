"""The model string must appear in exactly one file, and banned services in none.

These are the two rules that rot silently. A second model string somewhere means
half the system quietly runs a different model; a stray BigQuery import means the
architecture grew a component nobody justified. Both are cheap to test and
expensive to discover late.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    ".venv",
    ".cache",
    "node_modules",
    ".next",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}


def _tracked_text_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=False)
    if out.returncode == 0 and out.stdout.strip():
        paths = [REPO / line for line in out.stdout.splitlines() if line]
    else:
        paths = [p for p in REPO.rglob("*") if p.is_file()]
    result = []
    for path in paths:
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix in {".jsonl", ".sha256", ".eml"}:
            continue
        result.append(path)
    return result


def test_gemini_model_string_appears_only_in_config() -> None:
    pattern = re.compile(r"gemini-\d")
    offenders: list[str] = []
    for path in _tracked_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not pattern.search(text):
            continue
        rel = path.relative_to(REPO).as_posix()
        # lib/config.py owns it. README and this test name it to document and to
        # enforce the rule respectively; nothing else may.
        if rel in {"lib/config.py", "README.md", "tests/test_config_singleton.py"}:
            continue
        offenders.append(rel)
    assert not offenders, f"gemini model string found outside lib/config.py: {offenders}"


def test_model_string_is_gemini_3_5_or_newer() -> None:
    from lib.config import GEMINI_MODEL

    match = re.match(r"gemini-(\d+)(?:\.(\d+))?", GEMINI_MODEL)
    assert match, f"unparseable model string: {GEMINI_MODEL}"
    major = int(match.group(1))
    minor = int(match.group(2) or 0)
    assert (major, minor) >= (3, 5), f"{GEMINI_MODEL} is older than gemini-3.5"


def test_no_banned_services_anywhere() -> None:
    """Approved services only: Firestore, Pub/Sub, Cloud Run, Vertex AI."""
    banned = {
        "gke": re.compile(r"\bgke\b|container\.googleapis|kubernetes", re.I),
        "cloud_sql": re.compile(r"cloudsql|cloud[_ -]sql|sqladmin\.googleapis", re.I),
        "bigquery": re.compile(r"bigquery", re.I),
        "spanner": re.compile(r"\bspanner\b", re.I),
        "dataflow": re.compile(r"\bdataflow\b", re.I),
        "redis": re.compile(r"\bredis\b|memorystore", re.I),
    }
    offenders: list[str] = []
    for path in _tracked_text_files():
        rel = path.relative_to(REPO).as_posix()
        if rel == "tests/test_config_singleton.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for name, pattern in banned.items():
            for match in pattern.finditer(text):
                # ARCHITECTURE.md names the banned services once, in a paragraph
                # recording that each is deliberately not used. Exempt a mention
                # only when that disclaimer is nearby -- checking the same line
                # is too brittle, since the formatter rewraps prose.
                window = text[max(0, match.start() - 500) : match.end() + 500]
                if "NOT USED" in window:
                    continue
                line_start = text.rfind("\n", 0, match.start()) + 1
                line_end = text.find("\n", match.start())
                line = text[line_start : line_end if line_end != -1 else len(text)]
                offenders.append(f"{rel}: {name}: {line.strip()[:100]}")
    assert not offenders, "banned service referenced:\n" + "\n".join(offenders)
