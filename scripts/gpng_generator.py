# ==========================================================
# AL BARAKA TRADERS
# PNG GENERATOR
# Version 2.0 (High Resolution & Auto-Cropped)
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
print("PNG GENERATOR - HD ULTRA")
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
# PLAYWRIGHT GENERATION
# ==========================================================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    # Create browser context with High DPI scale factor
    context = browser.new_context(
        viewport={"width": 1200, "height": 1600},
        device_scale_factor=3  # 3x pixel density for crisp HD output
    )

    page = context.new_page()

    # =====================================
    # LOOP THROUGH HTML FILES
    # =====================================

    for html in html_files:

        print(f"\nOpening : {html.name}")

        file_url = html.resolve().as_uri()

        page.goto(file_url, wait_until="networkidle")

        # Wait briefly for web fonts and image assets to render cleanly
        page.wait_for_timeout(1000)

        output_png = PNG_FOLDER / (html.stem + ".png")

        # Target the .card element directly to crop out extra grey margins
        card_element = page.query_selector(".card")

        if card_element:
            card_element.screenshot(
                path=str(output_png),
                omit_background=True  # Transparent background around rounded corners
            )
            print(f"✓ Saved (Cropped & HD) : {output_png.name}")
        else:
            # Fallback if .card class is not found
            page.screenshot(path=str(output_png), full_page=True)
            print(f"⚠ Saved (Full Page Fallback) : {output_png.name}")

    browser.close()

print("\n")
print("=" * 50)
print("PNG GENERATION COMPLETED")
print("=" * 50)