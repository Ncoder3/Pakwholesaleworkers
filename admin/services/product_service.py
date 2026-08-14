"""
==========================================================
AL BARAKA TRADERS - PRODUCT SERVICE
==========================================================

PostgreSQL-based product and inventory service.

Stage 2:
    - PostgreSQL becomes the primary product database.
    - Handles product CRUD.
    - Handles stock/inventory.
    - Generates product codes.
    - Keeps the existing Excel structure compatible.

Stage 3:
    - Catalog generator can read products through this service.
"""

import re
from decimal import Decimal
from pathlib import Path

import pandas as pd

from services.database import get_db_connection
from services.excel_service import (
    EXCEL_FILE,
    ALL_COLUMNS,
    calculate_price_per_piece,
    load_products as load_products_excel,
)


# ==========================================================
# PRODUCT DATABASE COLUMNS
# ==========================================================

PRODUCT_COLUMNS = [
    "product_code",
    "category",
    "product_name",
    "pack_unit_type",
    "pieces_per_pack",
    "wholesale_price_per_pack",
    "price_per_piece",
    "suggested_retail_price_per_piece",
    "stock_available_packs",
    "notes",
    "image_file",
    "created_at",
    "updated_at",
]


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def ensure_products_table():
    """
    Creates the PostgreSQL products table if it does not exist.

    Safe to call repeatedly.
    """

    conn = get_db_connection()

    if not conn:
        print("[PRODUCT DB] DATABASE_URL not available.")
        return False

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,

                    product_code VARCHAR(50) UNIQUE NOT NULL,

                    category VARCHAR(255),
                    product_name VARCHAR(255) NOT NULL,
                    pack_unit_type VARCHAR(255),

                    pieces_per_pack NUMERIC(12, 2) DEFAULT 0,

                    wholesale_price_per_pack NUMERIC(12, 2) DEFAULT 0,
                    price_per_piece NUMERIC(12, 2) DEFAULT 0,
                    suggested_retail_price_per_piece NUMERIC(12, 2) DEFAULT 0,

                    stock_available_packs INTEGER DEFAULT 0,

                    notes TEXT,
                    image_file VARCHAR(500),

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Helpful indexes
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_products_category
                ON products(category);
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_products_name
                ON products(product_name);
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_products_stock
                ON products(stock_available_packs);
                """
            )

        conn.commit()

        print("[PRODUCT DB] Products table ready.")
        return True

    except Exception as e:
        conn.rollback()
        print(f"[PRODUCT DB ERROR] Failed to initialize products table: {e}")
        return False

    finally:
        conn.close()


# ==========================================================
# HELPERS
# ==========================================================

def _clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def _to_float(value):
    try:
        if value is None or value == "":
            return 0.0

        return float(value)

    except (ValueError, TypeError):
        return 0.0


def _to_int(value):
    try:
        if value is None or value == "":
            return 0

        return int(float(value))

    except (ValueError, TypeError):
        return 0


def _row_to_product(row):
    """
    Converts PostgreSQL RealDictCursor row into the same
    naming convention used by the existing application.
    """

    if not row:
        return None

    return {
        "id": row.get("id"),

        "Product Code": _clean_text(row.get("product_code")),
        "Category": _clean_text(row.get("category")),
        "Product Name": _clean_text(row.get("product_name")),
        "Pack / Unit Type": _clean_text(row.get("pack_unit_type")),

        "Pieces per Pack": _to_float(
            row.get("pieces_per_pack")
        ),

        "Wholesale Price per Pack (Rs)": _to_float(
            row.get("wholesale_price_per_pack")
        ),

        "Price per Piece (Rs)": _to_float(
            row.get("price_per_piece")
        ),

        "Suggested Retail Price per Piece (Rs)": _to_float(
            row.get("suggested_retail_price_per_piece")
        ),

        "Stock Available (Packs)": _to_int(
            row.get("stock_available_packs")
        ),

        "Notes": _clean_text(row.get("notes")),
        "Image File": _clean_text(row.get("image_file")),

        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _product_to_db_values(product):
    """
    Converts the existing application product format into
    PostgreSQL column values.
    """

    wholesale = _to_float(
        product.get("Wholesale Price per Pack (Rs)")
    )

    pieces = _to_float(
        product.get("Pieces per Pack")
    )

    calculated_price = calculate_price_per_piece(
        wholesale,
        pieces
    )

    return {
        "product_code": _clean_text(
            product.get("Product Code")
        ),

        "category": _clean_text(
            product.get("Category")
        ),

        "product_name": _clean_text(
            product.get("Product Name")
        ),

        "pack_unit_type": _clean_text(
            product.get("Pack / Unit Type")
        ),

        "pieces_per_pack": pieces,

        "wholesale_price_per_pack": wholesale,

        "price_per_piece": calculated_price,

        "suggested_retail_price_per_piece": _to_float(
            product.get(
                "Suggested Retail Price per Piece (Rs)"
            )
        ),

        "stock_available_packs": _to_int(
            product.get("Stock Available (Packs)")
        ),

        "notes": _clean_text(
            product.get("Notes")
        ),

        "image_file": _clean_text(
            product.get("Image File")
        ),
    }


# ==========================================================
# LOAD PRODUCTS
# ==========================================================

def get_products():
    """
    Returns all products from PostgreSQL.

    This is the main function the admin application should use.
    """

    ensure_products_table()

    conn = get_db_connection()

    if not conn:
        print("[PRODUCT DB] Falling back to Excel.")
        return load_products_excel().to_dict(
            orient="records"
        )

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
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
                    image_file,
                    created_at,
                    updated_at
                FROM products
                ORDER BY id ASC;
                """
            )

            rows = cur.fetchall()

            return [
                _row_to_product(row)
                for row in rows
            ]

    except Exception as e:
        print(f"[PRODUCT DB ERROR] Failed to load products: {e}")

        return []

    finally:
        conn.close()


def load_products():
    """
    Returns products as a pandas DataFrame.

    This makes PostgreSQL compatible with the existing
    catalog generator and analytics code.
    """

    products = get_products()

    if not products:
        return pd.DataFrame(
            columns=ALL_COLUMNS
        )

    df = pd.DataFrame(products)

    # Convert PostgreSQL naming back to existing Excel naming.
    required = ALL_COLUMNS

    for column in required:
        if column not in df.columns:
            df[column] = ""

    return df[required]


# ==========================================================
# GET SINGLE PRODUCT
# ==========================================================

def get_product(product_code):
    """
    Returns one product by Product Code.
    """

    ensure_products_table()

    conn = get_db_connection()

    if not conn:
        return None

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
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
                    image_file,
                    created_at,
                    updated_at
                FROM products
                WHERE product_code = %s
                LIMIT 1;
                """,
                (_clean_text(product_code),)
            )

            row = cur.fetchone()

            return _row_to_product(row)

    except Exception as e:
        print(
            f"[PRODUCT DB ERROR] Failed to load product "
            f"{product_code}: {e}"
        )
        return None

    finally:
        conn.close()


# ==========================================================
# PRODUCT CODE
# ==========================================================

def get_next_product_code(prefix="ABT-"):
    """
    Generates the next product code from PostgreSQL.

    Example:
        ABT-041
        ABT-042
    """

    ensure_products_table()

    conn = get_db_connection()

    if not conn:
        return f"{prefix}001"

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT product_code
                FROM products
                WHERE product_code LIKE %s;
                """,
                (f"{prefix}%",)
            )

            rows = cur.fetchall()

            highest = 0

            for row in rows:
                code = _clean_text(
                    row.get("product_code")
                )

                match = re.search(
                    rf"^{re.escape(prefix)}(\d+)$",
                    code
                )

                if match:
                    highest = max(
                        highest,
                        int(match.group(1))
                    )

            return f"{prefix}{highest + 1:03d}"

    except Exception as e:
        print(
            f"[PRODUCT DB ERROR] Failed to generate "
            f"product code: {e}"
        )

        return f"{prefix}001"

    finally:
        conn.close()


# ==========================================================
# ADD PRODUCT
# ==========================================================

def add_product(product_data):
    """
    Adds a new product to PostgreSQL.

    Image uploading remains handled by the existing
    Excel/image service. This function stores the image filename.
    """

    ensure_products_table()

    conn = get_db_connection()

    if not conn:
        return False, "PostgreSQL database is not available."

    values = _product_to_db_values(product_data)

    if not values["product_code"]:
        values["product_code"] = get_next_product_code()

    if not values["product_name"]:
        return False, "Product Name is required."

    try:
        with conn.cursor() as cur:

            # Check duplicate code
            cur.execute(
                """
                SELECT id
                FROM products
                WHERE product_code = %s
                LIMIT 1;
                """,
                (values["product_code"],)
            )

            if cur.fetchone():
                return (
                    False,
                    "Product Code already exists."
                )

            cur.execute(
                """
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
                    %(product_code)s,
                    %(category)s,
                    %(product_name)s,
                    %(pack_unit_type)s,
                    %(pieces_per_pack)s,
                    %(wholesale_price_per_pack)s,
                    %(price_per_piece)s,
                    %(suggested_retail_price_per_piece)s,
                    %(stock_available_packs)s,
                    %(notes)s,
                    %(image_file)s
                );
                """,
                values
            )

        conn.commit()

        return (
            True,
            "Product added successfully."
        )

    except Exception as e:
        conn.rollback()

        print(
            f"[PRODUCT DB ERROR] Failed to add product: {e}"
        )

        return (
            False,
            f"Failed to add product: {e}"
        )

    finally:
        conn.close()


# ==========================================================
# UPDATE PRODUCT
# ==========================================================

def update_product(product_data):
    """
    Updates an existing PostgreSQL product.
    """

    ensure_products_table()

    conn = get_db_connection()

    if not conn:
        return False, "PostgreSQL database is not available."

    original_code = _clean_text(
        product_data.get("original_code")
        or product_data.get("Product Code")
    )

    new_code = _clean_text(
        product_data.get("Product Code")
    )

    if not original_code:
        return False, "Original Product Code is required."

    if not new_code:
        return False, "Product Code is required."

    values = _product_to_db_values(
        product_data
    )

    values["product_code"] = new_code

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM products
                WHERE product_code = %s
                LIMIT 1;
                """,
                (original_code,)
            )

            existing = cur.fetchone()

            if not existing:
                return (
                    False,
                    f"Product with code "
                    f"'{original_code}' not found."
                )

            # Prevent changing to another existing code.
            if new_code != original_code:

                cur.execute(
                    """
                    SELECT id
                    FROM products
                    WHERE product_code = %s
                    AND product_code <> %s
                    LIMIT 1;
                    """,
                    (
                        new_code,
                        original_code
                    )
                )

                if cur.fetchone():
                    return (
                        False,
                        "Product Code already exists."
                    )

            cur.execute(
                """
                UPDATE products
                SET
                    product_code = %(product_code)s,
                    category = %(category)s,
                    product_name = %(product_name)s,
                    pack_unit_type = %(pack_unit_type)s,
                    pieces_per_pack = %(pieces_per_pack)s,
                    wholesale_price_per_pack = %(wholesale_price_per_pack)s,
                    price_per_piece = %(price_per_piece)s,
                    suggested_retail_price_per_piece =
                        %(suggested_retail_price_per_piece)s,
                    stock_available_packs =
                        %(stock_available_packs)s,
                    notes = %(notes)s,
                    image_file = %(image_file)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE product_code = %(original_code)s;
                """,
                {
                    **values,
                    "original_code": original_code
                }
            )

        conn.commit()

        return (
            True,
            "Product updated successfully."
        )

    except Exception as e:
        conn.rollback()

        print(
            f"[PRODUCT DB ERROR] Failed to update "
            f"product: {e}"
        )

        return (
            False,
            f"Failed to update product: {e}"
        )

    finally:
        conn.close()


# ==========================================================
# DELETE PRODUCT
# ==========================================================

def delete_product(product_code):
    """
    Deletes a product from PostgreSQL.
    """

    ensure_products_table()

    conn = get_db_connection()

    if not conn:
        return False, "PostgreSQL database is not available."

    product_code = _clean_text(product_code)

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                DELETE FROM products
                WHERE product_code = %s
                RETURNING id;
                """,
                (product_code,)
            )

            deleted = cur.fetchone()

            if not deleted:
                return (
                    False,
                    "Product not found."
                )

        conn.commit()

        return (
            True,
            "Product deleted successfully."
        )

    except Exception as e:
        conn.rollback()

        print(
            f"[PRODUCT DB ERROR] Failed to delete "
            f"product: {e}"
        )

        return (
            False,
            f"Failed to delete product: {e}"
        )

    finally:
        conn.close()


# ==========================================================
# INVENTORY / STOCK
# ==========================================================

def get_stock(product_code):
    """
    Returns current stock for one product.
    """

    product = get_product(product_code)

    if not product:
        return None

    return product.get(
        "Stock Available (Packs)",
        0
    )


def update_stock(product_code, new_stock):
    """
    Directly sets product stock.
    """

    ensure_products_table()

    conn = get_db_connection()

    if not conn:
        return False, "PostgreSQL database is not available."

    product_code = _clean_text(product_code)
    new_stock = max(0, _to_int(new_stock))

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE products
                SET
                    stock_available_packs = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE product_code = %s
                RETURNING id;
                """,
                (
                    new_stock,
                    product_code
                )
            )

            result = cur.fetchone()

            if not result:
                return (
                    False,
                    "Product not found."
                )

        conn.commit()

        return (
            True,
            "Stock updated successfully."
        )

    except Exception as e:
        conn.rollback()

        print(
            f"[PRODUCT DB ERROR] Failed to update "
            f"stock: {e}"
        )

        return (
            False,
            f"Failed to update stock: {e}"
        )

    finally:
        conn.close()


def decrease_stock(product_code, quantity):
    """
    Atomically decreases stock.

    Stock will never go below zero.
    """

    ensure_products_table()

    conn = get_db_connection()

    if not conn:
        return False, "PostgreSQL database is not available."

    product_code = _clean_text(product_code)
    quantity = _to_int(quantity)

    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE products
                SET
                    stock_available_packs =
                        GREATEST(
                            0,
                            stock_available_packs - %s
                        ),
                    updated_at = CURRENT_TIMESTAMP
                WHERE product_code = %s
                RETURNING stock_available_packs;
                """,
                (
                    quantity,
                    product_code
                )
            )

            result = cur.fetchone()

            if not result:
                return (
                    False,
                    "Product not found."
                )

            new_stock = result[
                "stock_available_packs"
            ]

        conn.commit()

        return (
            True,
            f"Stock updated successfully. "
            f"Remaining stock: {new_stock}"
        )

    except Exception as e:
        conn.rollback()

        print(
            f"[PRODUCT DB ERROR] Failed to decrease "
            f"stock: {e}"
        )

        return (
            False,
            f"Failed to decrease stock: {e}"
        )

    finally:
        conn.close()


# ==========================================================
# CATEGORIES
# ==========================================================

def get_existing_categories():
    """
    Returns unique product categories from PostgreSQL.
    """

    ensure_products_table()

    conn = get_db_connection()

    if not conn:
        return []

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT DISTINCT category
                FROM products
                WHERE category IS NOT NULL
                AND TRIM(category) <> ''
                ORDER BY category;
                """
            )

            rows = cur.fetchall()

            return [
                _clean_text(row["category"])
                for row in rows
            ]

    except Exception as e:
        print(
            f"[PRODUCT DB ERROR] Failed to load "
            f"categories: {e}"
        )
        return []

    finally:
        conn.close()


# ==========================================================
# DASHBOARD INVENTORY STATISTICS
# ==========================================================

def dashboard_stats():
    """
    Returns dashboard inventory statistics from PostgreSQL.
    """

    ensure_products_table()

    conn = get_db_connection()

    if not conn:
        return {
            "total_products": 0,
            "total_categories": 0,
            "total_stock": 0,
        }

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_products,
                    COUNT(
                        DISTINCT NULLIF(
                            TRIM(category),
                            ''
                        )
                    ) AS total_categories,
                    COALESCE(
                        SUM(stock_available_packs),
                        0
                    ) AS total_stock
                FROM products;
                """
            )

            row = cur.fetchone()

            return {
                "total_products": int(
                    row["total_products"] or 0
                ),

                "total_categories": int(
                    row["total_categories"] or 0
                ),

                "total_stock": int(
                    row["total_stock"] or 0
                ),
            }

    except Exception as e:
        print(
            f"[PRODUCT DB ERROR] Failed to calculate "
            f"dashboard stats: {e}"
        )

        return {
            "total_products": 0,
            "total_categories": 0,
            "total_stock": 0,
        }

    finally:
        conn.close()


# ==========================================================
# EXCEL → POSTGRESQL MIGRATION
# ==========================================================

def migrate_products_from_excel():
    """
    One-time migration:

        data/products.xlsx
                ↓
        PostgreSQL products table

    Existing PostgreSQL products are NOT duplicated.

    Products with an existing Product Code are updated.
    Products with new Product Codes are inserted.
    """

    ensure_products_table()

    if not EXCEL_FILE.exists():
        return (
            False,
            f"Excel file not found: {EXCEL_FILE}"
        )

    try:
        df = pd.read_excel(
            EXCEL_FILE,
            engine="openpyxl"
        )

        if df.empty:
            return (
                False,
                "Excel product file is empty."
            )

        # Ensure expected columns exist.
        for column in ALL_COLUMNS:
            if column not in df.columns:
                df[column] = ""

        df = df[ALL_COLUMNS].fillna("")

    except Exception as e:
        return (
            False,
            f"Failed to read Excel file: {e}"
        )

    conn = get_db_connection()

    if not conn:
        return (
            False,
            "PostgreSQL database is not available."
        )

    inserted = 0
    updated = 0

    try:
        with conn.cursor() as cur:

            for _, row in df.iterrows():

                product = row.to_dict()
                values = _product_to_db_values(
                    product
                )

                if not values["product_code"]:
                    continue

                if not values["product_name"]:
                    continue

                cur.execute(
                    """
                    SELECT id
                    FROM products
                    WHERE product_code = %s
                    LIMIT 1;
                    """,
                    (
                        values["product_code"],
                    )
                )

                existing = cur.fetchone()

                if existing:

                    cur.execute(
                        """
                        UPDATE products
                        SET
                            category = %(category)s,
                            product_name = %(product_name)s,
                            pack_unit_type = %(pack_unit_type)s,
                            pieces_per_pack = %(pieces_per_pack)s,
                            wholesale_price_per_pack =
                                %(wholesale_price_per_pack)s,
                            price_per_piece =
                                %(price_per_piece)s,
                            suggested_retail_price_per_piece =
                                %(suggested_retail_price_per_piece)s,
                            stock_available_packs =
                                %(stock_available_packs)s,
                            notes = %(notes)s,
                            image_file = %(image_file)s,
                            updated_at =
                                CURRENT_TIMESTAMP
                        WHERE product_code =
                            %(product_code)s;
                        """,
                        values
                    )

                    updated += 1

                else:

                    cur.execute(
                        """
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
                            %(product_code)s,
                            %(category)s,
                            %(product_name)s,
                            %(pack_unit_type)s,
                            %(pieces_per_pack)s,
                            %(wholesale_price_per_pack)s,
                            %(price_per_piece)s,
                            %(suggested_retail_price_per_piece)s,
                            %(stock_available_packs)s,
                            %(notes)s,
                            %(image_file)s
                        );
                        """,
                        values
                    )

                    inserted += 1

        conn.commit()

        return (
            True,
            f"Product migration completed. "
            f"Inserted: {inserted}, "
            f"Updated: {updated}."
        )

    except Exception as e:
        conn.rollback()

        print(
            f"[PRODUCT DB ERROR] Migration failed: {e}"
        )

        return (
            False,
            f"Product migration failed: {e}"
        )

    finally:
        conn.close()


# ==========================================================
# POSTGRESQL → EXCEL EXPORT
# ==========================================================

def export_products_to_excel():
    """
    Creates/updates products.xlsx from PostgreSQL.

    PostgreSQL remains the source of truth.
    """

    df = load_products()

    try:
        EXCEL_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_excel(
            EXCEL_FILE,
            index=False,
            engine="openpyxl"
        )

        return (
            True,
            "Products exported to Excel successfully."
        )

    except Exception as e:

        return (
            False,
            f"Failed to export products to Excel: {e}"
        )