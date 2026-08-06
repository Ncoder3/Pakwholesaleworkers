"""
===========================================================
AL BARAKA TRADERS
HELPER FUNCTIONS
===========================================================

This file contains reusable utility functions.

These functions can be imported into any module.

Example:

from helpers import safe_filename
from helpers import find_product_image

===========================================================
"""

import os
import shutil
from config import (
    BRAND_NAME,
    TAGLINE,
    WHATSAPP,
    EMAIL,
    WEBSITE,
    FOOTER
)

from themes import get_theme

from qr_generator import generate_qr

CATEGORY_ICONS = {

    "Personal Care": "🪥",

    "Beauty": "💄",

    "Household Cleaning": "🧼",

    "Stationery": "✏️",

    "Baby Products": "🍼",

    "Kids & Toys": "🧸",

    "Disposable Items": "🥤",

    "Soaps": "🧴",

    "Miscellaneous": "📦"

}


# ===========================================================
# SAFE FILE NAME
# ===========================================================

def safe_filename(name):
    """
    Convert a product name into a safe filename.

    Example:

    Baby Nipple (PP)

    becomes

    Baby_Nipple_(PP)
    """

    if name is None:
        return ""

    name = str(name).strip()

    name = name.replace(" ", "_")

    invalid = r'\/:*?"<>|'

    for char in invalid:
        name = name.replace(char, "-")

    return name


# ===========================================================
# FIND PRODUCT IMAGE
# ===========================================================

def find_product_image(product_name, image_folder="images"):
    """
    Search for a product image.

    Supports:

    jpg
    jpeg
    png
    webp

    Returns:

    ../images/filename.jpg

    otherwise

    ../images/default.png
    """

    base = safe_filename(product_name)

    extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    ]

    for ext in extensions:

        filename = base + ext

        full_path = os.path.join(
            image_folder,
            filename
        )

        if os.path.exists(full_path):

            return "../images/" + filename

    return "../images/default.png"


# ===========================================================
# FORMAT PRICE
# ===========================================================

def format_price(value):
    """
    Convert

    27.5

    into

    27.50
    """

    try:

        return f"{float(value):,.2f}"

    except:

        return "0.00"


# ===========================================================
# STOCK STATUS
# ===========================================================

def stock_status(stock):
    """
    Returns

    status text

    status class

    Example

    In Stock

    success
    """

    try:

        stock = int(stock)

    except:

        stock = 0

    if stock >= 20:

        return (
            "In Stock",
            "success"
        )

    elif stock >= 5:

        return (
            "Limited Stock",
            "warning"
        )

    else:

        return (
            "Out of Stock",
            "danger"
        )


# ===========================================================
# COPY FILE
# ===========================================================

def copy_file(source, destination):
    """
    Copy one file safely.
    """

    if os.path.exists(source):

        os.makedirs(
            os.path.dirname(destination),
            exist_ok=True
        )

        shutil.copy2(
            source,
            destination
        )


# ===========================================================
# COPY ENTIRE FOLDER
# ===========================================================

def copy_folder(source_folder, destination_folder):
    """
    Copy all files from one folder.

    Missing folders are ignored.
    """

    if not os.path.exists(source_folder):

        return

    os.makedirs(
        destination_folder,
        exist_ok=True
    )

    for file in os.listdir(source_folder):

        source = os.path.join(
            source_folder,
            file
        )

        if os.path.isfile(source):

            shutil.copy2(
                source,
                os.path.join(
                    destination_folder,
                    file
                )
            )


# ===========================================================
# PRINT SECTION
# ===========================================================

def print_section(title):
    """
    Print a formatted console heading.
    """

    print()

    print("=" * 60)

    print(title)

    print("=" * 60)


# ===========================================================
# PRINT SUCCESS
# ===========================================================

def print_success(message):

    print(f"✓ {message}")


# ===========================================================
# PRINT WARNING
# ===========================================================

def print_warning(message):

    print(f"⚠ {message}")


# ===========================================================
# PRINT ERROR
# ===========================================================

def print_error(message):

    print(f"✖ {message}")

# ===========================================================
# CREATE PRODUCT OBJECT
# ===========================================================

def create_product(row):
    """
    Convert one Excel row into a dictionary
    that is directly passed to the HTML template.
    """

    product = {

        "product_code":
            str(row.get("Product Code", "")).strip(),

        "category":
            str(row.get("Category", "")).strip(),

        "product_name":
            str(row.get("Product Name", "")).strip(),

        "packing":
            str(row.get("Pack / Unit Type", "")).strip(),

        "pieces":
            row.get("Pieces per Pack", ""),

        "wholesale_price":
            format_price(
                row.get("Wholesale Price per Pack (Rs)", 0)
            ),

        "price_per_piece":
            format_price(
                row.get("Price per Piece (Rs)", 0)
            ),

        "retail_price":
            format_price(
                row.get(
                    "Suggested Retail Price per Piece (Rs)",
                    0
                )
            ),

        "stock":
            row.get("Stock Available (Packs)", 0),

        "description":
            str(row.get("Notes", "")).strip(),

        "image":
            find_product_image(
                row.get("Product Name", "")
            ),

        "brand": BRAND_NAME,

        "tagline": TAGLINE,

        "whatsapp": WHATSAPP,

        "email": EMAIL,

        "website": WEBSITE,

        "footer": FOOTER,

        "carton": "",

        "pack_type": "Pack"

    }

    stock_text, stock_class = stock_status(
        product["stock"]
    )

    product["stock_text"] = stock_text

    product["stock_class"] = stock_class

    theme = get_theme(product["category"])

    product["primary_color"] = theme["primary"]

    product["secondary_color"] = theme["secondary"]

    product["accent_color"] = theme["accent"]

    product["text_color"] = theme["text"]

    product["qr"] = generate_qr(product)

    product["icon"] = CATEGORY_ICONS.get(
        product["category"],
        "📦"
    )

    return product