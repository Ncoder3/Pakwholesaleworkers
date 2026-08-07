# ==========================================================
# AL BARAKA TRADERS
# PRODUCT CARD GENERATOR
# PART 1
# ==========================================================

from pathlib import Path
import os
import shutil
from config import *
from validator import validate_catalog
import pandas as pd

from datetime import datetime

from jinja2 import Environment
from jinja2 import FileSystemLoader

# ==========================================================
# PROJECT ROOT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

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
    create_product
)



# ==========================================================
# FOLDERS
# ==========================================================

DATA_FOLDER = PROJECT_ROOT / "data"

TEMPLATE_FOLDER = PROJECT_ROOT / "templates"

IMAGE_FOLDER = PROJECT_ROOT / "images"

#forpc
#OUTPUT_FOLDER = os.path.join(
#    "output",
#   "html"
#)

#foronline
OUTPUT_FOLDER = PROJECT_ROOT /"output"


# ==========================================================
# FILES
# ==========================================================

EXCEL_FILE = DATA_FOLDER / "products.xlsx"
ASSETS_FOLDER = PROJECT_ROOT / "assets"



PRODUCT_TEMPLATE = "product/gproduct_card.html"

INDEX_TEMPLATE = "index/index.html"

PRODUCT_CSS = TEMPLATE_FOLDER / "product" / "gproduct_card.css"

INDEX_CSS = TEMPLATE_FOLDER / "index" / "index.css"

INDEX_JS = TEMPLATE_FOLDER / "index" / "index.js"

# ==========================================================
# CREATE OUTPUT FOLDER
# ==========================================================

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

print("Output folder ready.")

# ==========================================================
# LOAD EXCEL
# ==========================================================

print("Reading Excel...")

df = pd.read_excel(EXCEL_FILE, header=0)

print(f"Total Products : {len(df)}")


# ==========================================================
# GENERATE MISSING PRODUCT CODES
# ==========================================================

print("\nGenerating Product Codes...")

highest_code = 0

for code in df["Product Code"]:

    if pd.notna(code):

        code = str(code).strip()

        if code.startswith("ABT-"):

            try:

                number = int(
                    code.replace("ABT-", "")
                )

                highest_code = max(
                    highest_code,
                    number
                )

            except ValueError:

                pass


next_code = highest_code + 1

for index, code in df["Product Code"].items():

    if pd.isna(code) or str(code).strip() == "":

        new_code = f"{PRODUCT_PREFIX}-{next_code:03d}"

        df.at[index, "Product Code"] = new_code

        print(
            f"✓ Generated Product Code : {new_code} "
            f"→ {df.at[index, 'Product Name']}"
        )

        next_code += 1

print("✓ Product Codes generated.")

# validation
errors = validate_catalog(
    df,
    IMAGE_FOLDER,
    safe_filename
)

if errors > 0:

    print("\nGeneration cancelled because validation failed.")

    exit()

# ==========================================================
# LOAD HTML TEMPLATE
# ==========================================================

env = Environment(

    loader=FileSystemLoader(
        TEMPLATE_FOLDER
    )

)

template = env.get_template(
    PRODUCT_TEMPLATE
)

print("HTML Template Loaded.")

index_template = env.get_template(INDEX_TEMPLATE)

print("Index Template Loaded.")

# ==========================================================
# SHOW EXCEL COLUMNS
# ==========================================================

print("\nExcel Columns:\n")

for col in df.columns:

    print("-", col)

print("\nReady to generate cards.")
# ==========================================================
# GENERATE HTML FILES
# ==========================================================

print("\nGenerating Product Cards...\n")
found_images = 0
missing_images = 0

# =====================================
# Find the highest existing Product Code
# =====================================

# highest_code = 0

# for code in df["Product Code"]:

#     if pd.notna(code):

#         code = str(code).strip()

#         if code.startswith("ABT-"):

#             try:

#                 number = int(code.replace("ABT-", ""))

#                 highest_code = max(highest_code, number)

#             except:

#                 pass

# next_code = highest_code + 1

# ==========================================
# PRODUCTS LIST FOR INDEX.HTML
# ==========================================

products = []

for index, row in df.iterrows():

    product = create_product(row)

    print(
    f"Theme Selected : {product['category']} -> {product['primary_color']}"
    )

    safe_name = safe_filename(
        product["product_name"]
    )

    product["file_name"] = safe_name + ".html"

    products.append(product)

    if product["product_code"] == "":

        product["product_code"] = f"{PRODUCT_PREFIX}-{next_code:03d}"

        df.at[index, "Product Code"] = product["product_code"]

        next_code += 1

    if product["image"].endswith("default.png"):

        missing_images += 1

        print_warning(
            f"Image Missing : {product['product_name']}"
        )

    else:

        found_images += 1

        print_success(
            f"Image Found : {product['product_name']}"
        )

    html = template.render(**product)

    safe_name = safe_filename(
        product["product_name"]
    )

    output_file = OUTPUT_FOLDER / f"{safe_name}.html"

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)

    print_success(
        f"Generated {safe_name}.html"
    )
# ==========================================
# CREATE CATEGORY LIST
# ==========================================

categories = sorted(

    df["Category"]

    .dropna()

    .unique()

)

# ==========================================
# PREPARE INDEX DATA
# ==========================================

index_data = {

    "brand_name": BRAND_NAME,

    "tagline": TAGLINE,

    "website": WEBSITE,

    "email": EMAIL,

    "whatsapp": WHATSAPP,

    "products": products,

    "categories": categories,

    "total_products": len(products),

    "total_categories": len(categories),

    "generated_date":

        datetime.now().strftime("%d %b %Y")

}

# ==========================================
# RENDER INDEX.HTML
# ==========================================

index_html = index_template.render(
    **index_data
)

# ==========================================
# SAVE INDEX.HTML
# ==========================================

index_file = OUTPUT_FOLDER / "index.html"

with open(

    index_file,

    "w",

    encoding="utf-8"

) as file:

    file.write(index_html)

print_success(
    "Generated index.html"
)


print("\n" + "=" * 50)

print("AL BARAKA TRADERS")

print("CATALOG GENERATION COMPLETED")

print("=" * 50)

print(f"Products Generated : {len(df)}")

print(f"Images Found       : {found_images}")

print(f"Default Images     : {missing_images}")

print("=" * 50)
print("\n====================================")

print("All Product Cards Generated Successfully.")

print("====================================")

print_section("Copying Project Assets")

#forpc
#copy_file(
#    "templates/gproduct_card.css",
#   "output/html/gproduct_card.css"
#)

#formonline
copy_file(

    PRODUCT_CSS,

    OUTPUT_FOLDER / "gproduct_card.css"

)

print_success("CSS copied.")

shutil.copy(

    INDEX_CSS,

    OUTPUT_FOLDER / "index.css"

)


print_success("index.css copied.")

shutil.copy(

    INDEX_JS,

    OUTPUT_FOLDER / "index.js"

)

print_success("index.js copied.")

#forpc
#copy_file(
#    "assets/logo.png",
#    "output/assets/logo.png"
#)
#print_success("Logo copied.")

#foronline
copy_folder(

    ASSETS_FOLDER,

    OUTPUT_FOLDER / "assets"

)

print_success("Assets copied.")


copy_folder(

    IMAGE_FOLDER,

    OUTPUT_FOLDER / "images"

)

print_success("Images copied.")

print("\nSaving updated Excel...")

df.to_excel(
    EXCEL_FILE,
    index=False
)

print("✓ Excel updated successfully.")

# Suggestions for improvement:
# remove this from inside the product loop:

# if product["product_code"] == "":

#     product["product_code"] = f"{PRODUCT_PREFIX}-{next_code:03d}"

#     df.at[index, "Product Code"] = product["product_code"]

#     next_code += 1

# Because now every row already has a Product Code before you call:

# product = create_product(row)
