"""
Capture Streamlit screenshots for the README.

Boots the running Streamlit instance at $MADS_URL (default
http://localhost:8765), waits for the React shell to settle, and
writes high-DPI PNGs into docs/assets/.

Usage:
    python scripts/capture_screenshots.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

URL = os.environ.get("MADS_URL", "http://localhost:8765")

# Pages to capture: (route, output filename, after-load delay seconds)
PAGES = [
    ("/", "home_preview.png", 4.5),
    ("/Interactive_Chat", "chat_preview.png", 4.5),
    ("/Experiment_Runner", "runner_preview.png", 4.5),
    ("/Results_Dashboard", "dashboard_preview.png", 4.5),
]


def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 920},
            device_scale_factor=2,  # Retina-quality output
            color_scheme="dark",
        )
        page = context.new_page()

        for route, fname, delay in PAGES:
            target = URL.rstrip("/") + route
            print(f"-> {target}")
            try:
                page.goto(target, wait_until="networkidle", timeout=30_000)
            except Exception as exc:
                print(f"   warn: networkidle timeout ({exc}); continuing")
            # Streamlit needs a beat after networkidle to finish rendering markup.
            page.wait_for_timeout(int(delay * 1000))
            out = ASSETS / fname
            page.screenshot(path=str(out), full_page=False)
            print(f"   saved {out.relative_to(ROOT)}")

        browser.close()
    print("done")


if __name__ == "__main__":
    sys.exit(capture() or 0)
