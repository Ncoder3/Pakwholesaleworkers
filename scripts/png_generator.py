# ==========================================================
# AL BARAKA TRADERS
# PNG GENERATOR
# Version 1.0
# ==========================================================

import os
from pathlib import Path
from playwright.sync_api import sync_playwright

# ==========================================================
# FOLDERS
# ==========================================================

HTML_FOLDER = Path("output/html")

PNG_FOLDER = Path("output/png")

PNG_FOLDER.mkdir(parents=True, exist_ok=True)

# ==========================================================
# START
# ==========================================================

print("=" * 50)
print("AL BARAKA TRADERS")
print("PNG GENERATOR")
print("=" * 50)

# ==========================================================
# GET HTML FILES
# ==========================================================

html_files = list(HTML_FOLDER.glob("*.html"))

print(f"\nHTML Files Found : {len(html_files)}")

if len(html_files) == 0:

    print("No HTML files found.")

    exit()

# ==========================================================
# PLAYWRIGHT
# ==========================================================

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page(
        viewport={
            "width":900,
            "height":1200
        }
    )

    # =====================================
    # LOOP THROUGH HTML FILES
    # =====================================

    for html in html_files:

        print(f"\nOpening : {html.name}")

        file_url = html.resolve().as_uri()

        page.goto(file_url)

        # Wait for everything to load
        page.wait_for_timeout(1500)

        output_png = PNG_FOLDER / (html.stem + ".png")

        page.screenshot(

            path=str(output_png),

            full_page=True

        )

        print(f"✓ Saved : {output_png.name}")

    browser.close()

print("\n")
print("=" * 50)
print("PNG GENERATION COMPLETED")
print("=" * 50)