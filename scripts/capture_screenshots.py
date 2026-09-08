"""Capture interface screenshots for the thesis figures.

Drives the running server with a headless browser so the figures are
reproducible: re-seed the demo database, re-run this, and the same images come
out. Screenshots pasted in by hand drift away from the code they document.

Start the server first:

    python scripts/run_server.py --db data/demo.db --port 5055
    python scripts/capture_screenshots.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "docs" / "figures"
BASE_URL = "http://127.0.0.1:5055"
TOKEN = "devtoken"

DESKTOP = {"width": 900, "height": 1000}
MOBILE = {"width": 390, "height": 844}  # iPhone 14 logical resolution


def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()

        # -- desktop dashboard -------------------------------------------
        page = browser.new_page(viewport=DESKTOP, device_scale_factor=2)
        page.goto(BASE_URL)
        # The app reads its bearer token from localStorage, so seed it and
        # reload before anything tries to fetch.
        page.evaluate(f"localStorage.setItem('fk_token', '{TOKEN}')")
        page.goto(BASE_URL)
        page.wait_for_selector("article", timeout=15000)
        page.wait_for_timeout(1200)
        page.screenshot(path=FIGURES / "ui_dashboard.png", full_page=True)
        print("  ui_dashboard.png")

        # -- item detail with the freshness chart ------------------------
        page.click("article:has-text('Oranges')")
        page.wait_for_selector("canvas", timeout=15000)
        page.wait_for_timeout(1500)  # let Chart.js finish its entry animation
        page.screenshot(path=FIGURES / "ui_item_detail.png", full_page=True)
        print("  ui_item_detail.png")

        # -- statistics --------------------------------------------------
        page.goto(BASE_URL)
        page.wait_for_selector("article", timeout=15000)
        page.click("nav button:has-text('Stats')")
        page.wait_for_timeout(900)
        page.screenshot(path=FIGURES / "ui_stats.png", full_page=True)
        print("  ui_stats.png")
        page.close()

        # -- mobile dashboard --------------------------------------------
        mobile = browser.new_page(viewport=MOBILE, device_scale_factor=3,
                                  is_mobile=True, has_touch=True)
        mobile.goto(BASE_URL)
        mobile.evaluate(f"localStorage.setItem('fk_token', '{TOKEN}')")
        mobile.goto(BASE_URL)
        mobile.wait_for_selector("article", timeout=15000)
        mobile.wait_for_timeout(1200)
        mobile.screenshot(path=FIGURES / "ui_mobile.png", full_page=True)
        print("  ui_mobile.png")
        mobile.close()

        browser.close()

    print(f"\nScreenshots written to {FIGURES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
