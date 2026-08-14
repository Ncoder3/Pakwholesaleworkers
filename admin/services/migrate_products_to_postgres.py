"""
==========================================================
AL BARAKA TRADERS
PRODUCT INVENTORY MIGRATION
Excel -> PostgreSQL
==========================================================

One-time migration script.

Source:
    data/products.xlsx

Destination:
    PostgreSQL products table
"""

from pathlib import Path
import sys
import pandas as pd
import psycopg2
import os


# ==========================================================
# PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXCEL_FILE = PROJECT_ROOT / "data" / "products.xlsx"


# ==========================================================
# DATABASE
# ==========================================================

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL is not configured.")
    sys.exit(1)


# ==========================================================
# EXCEL COLUMNS
# ==========================================================

REQUIRED_COLUMNS = [
    "Product Code",
    "Category",
    "Product Name",
    "Pack / Unit Type",
    "Pieces per Pack",
    "Wholesale Price per Pack (Rs)",
    "Price per Piece (Rs)",
    "Suggested Retail Price per Piece (Rs)",
    "Stock Available (Packs)",
    "Notes",
    "Image File",
]


# ==========================================================
# LOAD EXCEL
# ==========================================================

print("=" * 60)
print("AL BARAKA TRADERS")
print("PRODUCT INVENTORY MIGRATION")
print("=" * 60)

print(f"\nExcel file: {EXCEL_FILE}")

if not EXCEL_FILE.exists():
    print("❌ products.xlsx was not found.")
    sys.exit(1)


df = pd.read_excel(
    EXCEL_FILE,
    engine="openpyxl"
)

print(f"✓ Excel products loaded: {len(df)}")


# ==========================================================
# CHECK COLUMNS
# ==========================================================

missing_columns = [
    col for col in REQUIRED_COLUMNS
    if col not in df.columns
]

if missing_columns:
    print("\n❌ Missing Excel columns:")

    for col in missing_columns:
        print(f"   - {col}")

    sys.exit(1)


# ==========================================================
# CLEAN DATA
# ==========================================================

df = df.fillna("")


def clean_text(value):
    return str(value).strip()


def clean_int(value):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def clean_decimal(value):
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.0


# ==========================================================
# CONNECT DATABASE
# ==========================================================

print("\nConnecting to PostgreSQL...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("✓ PostgreSQL connection successful.")

except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)


# ==========================================================
# INSERT PRODUCTS
# ==========================================================

insert_sql = """
INSERT INTO products (
    product_code,
    category,
    product_name,
    pack_unit_type,
    pieces_per_pack,
    wholesale_price_per_pack,
    price_per_piece,
    suggested_retail_price_per_piece,
    stock_available_packs,
    notes,
    image_file
)
VALUES (
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s
)
ON CONFLICT (product_code)
DO UPDATE SET
    category = EXCLUDED.category,
    product_name = EXCLUDED.product_name,
    pack_unit_type = EXCLUDED.pack_unit_type,
    pieces_per_pack = EXCLUDED.pieces_per_pack,
    wholesale_price_per_pack = EXCLUDED.wholesale_price_per_pack,
    price_per_piece = EXCLUDED.price_per_piece,
    suggested_retail_price_per_piece = EXCLUDED.suggested_retail_price_per_piece,
    stock_available_packs = EXCLUDED.stock_available_packs,
    notes = EXCLUDED.notes,
    image_file = EXCLUDED.image_file,
    updated_at = CURRENT_TIMESTAMP;
"""


inserted = 0
failed = 0


for index, row in df.iterrows():

    try:

        product_code = clean_text(row["Product Code"])
        category = clean_text(row["Category"])
        product_name = clean_text(row["Product Name"])
        pack_unit_type = clean_text(row["Pack / Unit Type"])

        pieces_per_pack = clean_int(
            row["Pieces per Pack"]
        )

        wholesale_price = clean_decimal(
            row["Wholesale Price per Pack (Rs)"]
        )

        price_per_piece = clean_decimal(
            row["Price per Piece (Rs)"]
        )

        suggested_retail_price = clean_decimal(
            row["Suggested Retail Price per Piece (Rs)"]
        )

        stock = clean_int(
            row["Stock Available (Packs)"]
        )

        notes = clean_text(
            row["Notes"]
        )

        image_file = clean_text(
            row["Image File"]
        )

        # ----------------------------------------------
        # Basic validation
        # ----------------------------------------------

        if not product_code:
            print(
                f"⚠ Row {index + 2}: missing product code. Skipped."
            )
            failed += 1
            continue

        if not product_name:
            print(
                f"⚠ {product_code}: missing product name. Skipped."
            )
            failed += 1
            continue

        cur.execute(
            insert_sql,
            (
                product_code,
                category,
                product_name,
                pack_unit_type,
                pieces_per_pack,
                wholesale_price,
                price_per_piece,
                suggested_retail_price,
                stock,
                notes,
                image_file,
            )
        )

        inserted += 1

        print(
            f"✓ {product_code} → {product_name}"
        )

    except Exception as e:

        failed += 1

        print(
            f"❌ Row {index + 2} failed: {e}"
        )


# ==========================================================
# COMMIT
# ==========================================================

try:

    conn.commit()

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)

    print(f"✓ Processed: {len(df)}")
    print(f"✓ Inserted/Updated: {inserted}")
    print(f"⚠ Failed: {failed}")

except Exception as e:

    conn.rollback()

    print(
        f"\n❌ Migration transaction failed: {e}"
    )

    cur.close()
    conn.close()

    sys.exit(1)


# ==========================================================
# VERIFY
# ==========================================================

try:

    cur.execute(
        "SELECT COUNT(*) FROM products;"
    )

    count = cur.fetchone()[0]

    print(
        f"\n✓ PostgreSQL products count: {count}"
    )

    cur.execute(
        """
        SELECT
            product_code,
            product_name,
            stock_available_packs
        FROM products
        ORDER BY id
        LIMIT 10;
        """
    )

    rows = cur.fetchall()

    print("\nFirst products:")

    for row in rows:
        print(
            f"  {row[0]} | {row[1]} | Stock: {row[2]}"
        )

finally:

    cur.close()
    conn.close()


print("\n✓ Migration script finished.")