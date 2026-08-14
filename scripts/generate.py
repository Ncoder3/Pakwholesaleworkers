"""
==========================================================
AL BARAKA TRADERS - PRODUCT CARD & INDEX GENERATOR
==========================================================
Main execution script for reading Excel product data, generating 
individual HTML product cards, rendering index.html, and copying 
static assets to the output directory.
"""

from pathlib import Path
import os
import shutil
import urllib.parse
from datetime import datetime
import pandas as pd
import qrcode
from jinja2 import Environment, FileSystemLoader

import config
from validator import validate_catalog
from helpers import (
    safe_filename,
    find_product_image,
    format_price,
    stock_status,
    copy_file,
    copy_folder,
    print_section,
    print_success,
    print_warning,
    print_error,
    create_product
)

import psycopg2
from psycopg2.extras import RealDictCursor

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ==========================================================
# PATH & DIRECTORY SETUP
# ==========================================================

DATA_FOLDER = PROJECT_ROOT / "data"
TEMPLATE_FOLDER = PROJECT_ROOT / "templates"
IMAGE_FOLDER = PROJECT_ROOT / "images"
ASSETS_FOLDER = PROJECT_ROOT / "assets"
OUTPUT_FOLDER = PROJECT_ROOT / "output"
QR_FOLDER = OUTPUT_FOLDER / "qr"

EXCEL_FILE = DATA_FOLDER / "products.xlsx"

PRODUCT_TEMPLATE = "product/gproduct_card.html"
INDEX_TEMPLATE = "index/index.html"

PRODUCT_CSS = TEMPLATE_FOLDER / "product" / "gproduct_card.css"
INDEX_CSS = TEMPLATE_FOLDER / "index" / "index.css"
INDEX_JS = TEMPLATE_FOLDER / "index" / "index.js"

# Create Output and QR Directories
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
QR_FOLDER.mkdir(parents=True, exist_ok=True)
print_success("Output and QR folders initialized.")


# PostgreSQL connection
DATABASE_URL = os.environ.get("DATABASE_URL")


def load_products_from_postgres():
    """Load catalog products directly from Railway PostgreSQL."""

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )

    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    product_code AS "Product Code",
                    category AS "Category",
                    product_name AS "Product Name",
                    pack_unit_type AS "Pack / Unit Type",
                    pieces_per_pack AS "Pieces per Pack",
                    wholesale_price_per_pack AS "Wholesale Price per Pack (Rs)",
                    price_per_piece AS "Price per Piece (Rs)",
                    suggested_retail_price_per_piece AS "Suggested Retail Price per Piece (Rs)",
                    stock_available_packs AS "Stock Available (Packs)",
                    notes AS "Notes",
                    image_file AS "Image File"
                FROM products
                ORDER BY id;
            """)

            rows = cur.fetchall()

        return pd.DataFrame(rows)

    finally:
        conn.close()

# ==========================================================
# QR GENERATOR HELPER FUNCTIONS
# ==========================================================
def generate_whatsapp_link(product):
    """Create a WhatsApp URL with a pre-filled message."""
    whatsapp_num = getattr(config, 'WHATSAPP', '923231551535')
    code = product.get('product_code', '')
    name = product.get('product_name', '')
    
    message = f"""
Hello Al Baraka Traders,

I am interested in the following product.

Product Code : {code}
Product Name : {name}

Please share the wholesale price and availability.

Thank you.
"""
    encoded = urllib.parse.quote(message.strip())
    return f"https://wa.me/{whatsapp_num}?text={encoded}"


def generate_qr(product):
    """Generate a QR code PNG for a product inside output/qr/ and return relative path."""
    url = generate_whatsapp_link(product)

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")

    filename = f"{product.get('product_code', 'default')}.png"
    filepath = QR_FOLDER / filename
    image.save(filepath)

    return f"qr/{filename}"


# ==========================================================
# 1. LOAD DATA & AUTO-GENERATE MISSING PRODUCT CODES
# ==========================================================
print_section("Loading Product Dataset")

# Excel data Loading
# if not EXCEL_FILE.exists():
#     print_error(f"Target Excel file missing: {EXCEL_FILE}")
#     exit(1)

# df = pd.read_excel(EXCEL_FILE, header=0)
# print(f"Total Products Read: {len(df)}")

# Postrgre Data Loading
print_section("Loading Product Dataset")

try:
    df = load_products_from_postgres()
except Exception as e:
    print_error(
        f"Failed to load products from PostgreSQL: {e}"
    )
    exit(1)

if df.empty:
    print_error(
        "PostgreSQL products table is empty."
    )
    exit(1)

print(
    f"Total Products Read From PostgreSQL: {len(df)}"
)

# Calculate highest existing numeric product code
# highest_code = 0
# prefix = f"{config.PRODUCT_PREFIX}-"

# for code in df.get("Product Code", []):
#     if pd.notna(code):
#         code_str = str(code).strip()
#         if code_str.startswith(prefix):
#             try:
#                 num = int(code_str.replace(prefix, ""))
#                 highest_code = max(highest_code, num)
#             except ValueError:
#                 pass

# next_code = highest_code + 1
# Migrated to product_services.py

# Assign missing codes back to DataFrame
for index, code in df["Product Code"].items():
    if pd.isna(code) or str(code).strip() == "":
        new_code = f"{config.PRODUCT_PREFIX}-{next_code:03d}"
        df.at[index, "Product Code"] = new_code
        print_success(f"Generated Code: {new_code} -> {df.at[index, 'Product Name']}")
        next_code += 1


# ==========================================================
# 2. VALIDATION CHECK
# ==========================================================
print_section("Validating Catalog Data")

errors = validate_catalog(df, IMAGE_FOLDER, safe_filename)
if errors > 0:
    print_error("Catalog generation canceled due to validation errors.")
    exit(1)


# ==========================================================
# 3. CONFIGURE JINJA ENVIRONMENT
# ==========================================================
env = Environment(
    loader=FileSystemLoader(TEMPLATE_FOLDER),
    autoescape=True
)

product_template = env.get_template(PRODUCT_TEMPLATE)
index_template = env.get_template(INDEX_TEMPLATE)
print_success("Jinja Templates compiled.")


# ==========================================================
# 4. GENERATE QR CODES & INDIVIDUAL PRODUCT HTML CARDS
# ==========================================================
print_section("Generating QR Codes & Product Cards")

products = []
found_images = 0
missing_images = 0

for index, row in df.iterrows():
    # Build complete product object dictionary via helper
    product = create_product(row)
    
    # Assign standardized safe filename
    safe_name = safe_filename(product["product_name"])
    product["file_name"] = f"{safe_name}.html"
    
    # Generate QR Code image and assign to keys used by both parent & sub-templates
    qr_rel_path = generate_qr(product)
    product["qr_code_path"] = qr_rel_path
    product["qr"] = qr_rel_path
    
    # Pre-set year & nested product object directly into dict to avoid render parameter duplication
    product["current_year"] = datetime.now().year
    product["product"] = product

    # Track missing vs available product images
    if str(product.get("image", "")).endswith("default.png"):
        missing_images += 1
        print_warning(f"Default Image Assigned: {product['product_name']}")
    else:
        found_images += 1

    products.append(product)

    # Render Product HTML Card safely
    card_html = product_template.render(
        **product,
        config=config
    )

    output_file = OUTPUT_FOLDER / f"{safe_name}.html"
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(card_html)

    print_success(f"Generated QR & Card: {safe_name}.html")


# ==========================================================
# 5. GENERATE INDEX / CATALOG DASHBOARD
# ==========================================================
print_section("Generating Index Catalog")

categories = sorted(df["Category"].dropna().unique().tolist())

index_data = {
    "config": config,
    "brand_name": getattr(config, 'BRAND_NAME', 'Al Baraka Traders'),
    "tagline": getattr(config, 'TAGLINE', 'Your Trusted Wholesale Partner'),
    "website": getattr(config, 'WEBSITE', 'www.albarakatradersabbott.pk'),
    "email": getattr(config, 'EMAIL', 'info@albarakatraders.pk'),
    "whatsapp": getattr(config, 'WHATSAPP', '923231551535'),
    "products": products,
    "categories": categories,
    "total_products": len(products),
    "total_categories": len(categories),
    "generated_date": datetime.now().strftime("%d %b %Y"),
    "current_year": datetime.now().year
}

index_html = index_template.render(**index_data)
index_file = OUTPUT_FOLDER / "index.html"

with open(index_file, "w", encoding="utf-8") as file:
    file.write(index_html)

print_success("Generated: index.html")


# ==========================================================
# 6. COPY STATIC ASSETS & UPDATE EXCEL SOURCE
# ==========================================================
print_section("Deploying Static Assets")

# Copy CSS/JS resources
if PRODUCT_CSS.exists():
    copy_file(PRODUCT_CSS, OUTPUT_FOLDER / "gproduct_card.css")
if INDEX_CSS.exists():
    shutil.copy(INDEX_CSS, OUTPUT_FOLDER / "index.css")
if INDEX_JS.exists():
    shutil.copy(INDEX_JS, OUTPUT_FOLDER / "index.js")

# Copy static directory trees
copy_folder(ASSETS_FOLDER, OUTPUT_FOLDER / "assets")
copy_folder(IMAGE_FOLDER, OUTPUT_FOLDER / "images")

# Copy project root 'qr' folder if present
if (PROJECT_ROOT / "qr").exists():
    copy_folder(PROJECT_ROOT / "qr", OUTPUT_FOLDER / "qr")

print_success("Static assets successfully synced.")

# Save modified dataset containing auto-generated codes
# print_section("Updating Excel Data File")
# df.to_excel(EXCEL_FILE, index=False)
# print_success("Excel source updated successfully with new product codes.")

print("\n" + "=" * 60)
print(f" CATALOG GENERATION COMPLETE: {len(products)} CARDS GENERATED")
print("=" * 60 + "\n")