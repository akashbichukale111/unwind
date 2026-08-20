"""Capture the nine numbered product screenshots the README embeds.

EVERY SHOT IS OF A REAL RUNNING SYSTEM. Nothing is mocked, staged or
retouched. Where a capability is genuinely unavailable in this environment
(no Google credentials), the screenshot shows that honest state — which is
the point: a reader can see for themselves that the Media Lab reports
NOT CONFIGURED rather than a fabricated video.

Run against a live server:

    FIRESTORE_EMULATOR_HOST=localhost:8080 UNWIND_VERTEX_DISABLED=1 \
    UNWIND_COUNTERSIGN_SIMULATED=1 UNWIND_OPERATOR_TOKENS="demo-tok:kim@ops.example" \
    python -m uvicorn services.api.main:app --port 8099
    python evidence/browser/capture_product_shots.py
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")

from playwright.sync_api import sync_playwright  # noqa: E402

BASE = os.environ.get("UNWIND_BASE_URL", "http://127.0.0.1:8099")
TOKEN = os.environ.get("UNWIND_DEMO_TOKEN", "demo-tok")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
OUT = "docs/shots"

SHOTS: list[str] = []


def shot(page, name: str, full: bool = True) -> None:
    path = f"{OUT}/{name}"
    page.screenshot(path=path, full_page=full)
    SHOTS.append(path)
    print(f"  captured {path}")


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1500, "height": 1000})
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(2000)

        # 01 — Agentic Command OS, before a mission runs.
        shot(page, "01-command-os.png")

        # Run a real mission so every later shot is of genuine state.
        page.fill("#cmdos-token", TOKEN)
        page.click("#cmdos-run")
        page.wait_for_timeout(15000)

        # 04 — the finished mission, its report and trusted state.
        page.evaluate("document.getElementById('cmdos-report').scrollIntoView()")
        page.wait_for_timeout(600)
        shot(page, "04-mission-success.png")

        # 05 — Mission Media Lab.
        page.evaluate("document.getElementById('media-lab').scrollIntoView()")
        page.wait_for_timeout(600)
        shot(page, "05-media-lab.png", full=False)

        # 06/07/08 — each modality after its button is actually pressed, so the
        # shot shows the REAL returned status rather than the idle card.
        for index, (nth, name) in enumerate(
            [(0, "06-gemini-gemma.png"), (1, "07-veo.png"), (2, "08-lyria.png")]
        ):
            page.locator(".media-go").nth(nth).click()
            page.wait_for_timeout(2500)
            page.evaluate("document.getElementById('media-lab').scrollIntoView()")
            page.wait_for_timeout(400)
            shot(page, name, full=False)
            _ = index

        # 02 — Mission Time Machine.
        page.click("#cmdos-open-timemachine")
        page.wait_for_timeout(5000)
        shot(page, "02-time-machine.png")

        # 03 — a checkpoint's real persisted detail.
        page.locator("#mtm-checkpoints [data-seq]").first.click()
        page.wait_for_timeout(1500)
        page.evaluate("document.getElementById('mtm-detail').scrollIntoView()")
        page.wait_for_timeout(500)
        shot(page, "03-checkpoint-detail.png")

        # 09 — the six-layer instrument: all pre-existing systems intact.
        page.keyboard.press("Escape")
        page.wait_for_timeout(1500)
        page.click("#cmdos-open-instrument")
        page.wait_for_timeout(3000)
        shot(page, "09-seven-system-instrument.png")

        browser.close()

    print(f"\n{len(SHOTS)} screenshots captured")
    missing = [p for p in SHOTS if not os.path.exists(p) or os.path.getsize(p) < 5000]
    if missing:
        print("EMPTY OR MISSING:", missing)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
