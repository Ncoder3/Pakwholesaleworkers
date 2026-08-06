# ==========================================================
# AL BARAKA TRADERS
# CATALOG VALIDATOR
# ==========================================================

import os
import pandas as pd


def validate_catalog(df, image_folder, safe_filename):

    print("\n" + "=" * 55)
    print("AL BARAKA TRADERS")
    print("CATALOG VALIDATOR")
    print("=" * 55)

    errors = 0
    warnings = 0

    # ======================================================
    # PRODUCT NAME
    # ======================================================

    print("\nChecking Product Names...")

    empty_names = df["Product Name"].isna().sum()

    if empty_names == 0:
        print("✓ Product names are valid.")
    else:
        print(f"✗ {empty_names} product names are empty.")
        errors += empty_names

    # ======================================================
    # PRODUCT CODE
    # ======================================================

    print("\nChecking Product Codes...")

    empty_codes = df["Product Code"].isna().sum()

    if empty_codes == 0:
        print("✓ Product Codes are valid.")
    else:
        print(f"⚠ {empty_codes} Product Codes are empty.")
        warnings += empty_codes

    # ======================================================
    # DUPLICATE PRODUCT CODE
    # ======================================================

    print("\nChecking Duplicate Product Codes...")

    duplicates = df[df["Product Code"].duplicated()]

    if len(duplicates) == 0:
        print("✓ No duplicate Product Codes.")
    else:
        print(f"✗ {len(duplicates)} duplicate Product Codes found.")
        errors += len(duplicates)

    # ======================================================
    # PRICE
    # ======================================================

    print("\nChecking Prices...")

    invalid_price = df["Price per Piece (Rs)"].isna().sum()

    if invalid_price == 0:
        print("✓ Prices look good.")
    else:
        print(f"✗ {invalid_price} products have no selling price.")
        errors += invalid_price

    # ======================================================
    # IMAGES
    # ======================================================

    print("\nChecking Images...")

    found = 0
    missing = 0

    extensions = [".jpg", ".png", ".jpeg", ".webp"]

    for _, row in df.iterrows():

        base = safe_filename(row["Product Name"])

        exists = False

        for ext in extensions:

            if os.path.exists(os.path.join(image_folder, base + ext)):
                exists = True
                break

        if exists:
            found += 1
        else:
            missing += 1
            print(f"⚠ Missing Image : {row['Product Name']}")

    print(f"\n✓ Images Found   : {found}")
    print(f"⚠ Images Missing : {missing}")

    print("\n" + "=" * 55)

    if errors == 0:
        print("✓ VALIDATION PASSED")
    else:
        print(f"✗ VALIDATION FOUND {errors} ERROR(S)")

    print("=" * 55)

    return errors