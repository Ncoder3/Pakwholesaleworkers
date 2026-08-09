"""
===========================================================
AL BARAKA TRADERS
HELPER FUNCTIONS
===========================================================

This module provides utility functions for file path management,
price formatting, stock status evaluation, and product object compilation.
"""

import os
import re
import shutil
from datetime import datetime
import pandas as pd

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

# Global Category Icon Mapping
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
    Convert product name into a filesystem-safe filename string.
    Example: 'Baby Nipple (PP)' -> 'Baby_Nipple_(PP)'
    """
    if not name or pd.isna(name):
        return ""

    name = str(name).strip()
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Replace forbidden path characters with a hyphen
    return re.sub(r'[\/:*?"<>|]', '-', name)


# ===========================================================
# FIND PRODUCT IMAGE
# ===========================================================

def find_product_image(product_name, explicit_image="", image_folder="images"):
    """
    Search for a product image file. Checks explicit filename specified 
    in Excel first, then checks derived filenames (.jpg, .jpeg, .png, .webp).
    """
    # 1. Check explicit filename saved in Excel
    if explicit_image and not pd.isna(explicit_image):
        clean_file = str(explicit_image).strip()
        if clean_file and clean_file.lower() != "nan":
            full_path = os.path.join(image_folder, clean_file)
            if os.path.exists(full_path):
                return f"../images/{clean_file}"

    # 2. Check derived product name with standard image extensions
    base = safe_filename(product_name)
    extensions = [".jpg", ".jpeg", ".png", ".webp"]

    for ext in extensions:
        filename = f"{base}{ext}"
        full_path = os.path.join(image_folder, filename)
        if os.path.exists(full_path):
            return f"../images/{filename}"

    return "../images/default.png"


# ===========================================================
# FORMAT PRICE
# ===========================================================

def format_price(value):
    """
    Format float or string into standard currency string with 2 decimal places.
    Example: 27.5 -> '27.50'
    """
    if value is None or pd.isna(value):
        return "0.00"

    try:
        # Strip out non-numeric characters like commas, Rs, spaces
        cleaned = re.sub(r'[^\d.]', '', str(value))
        return f"{float(cleaned):,.2f}"
    except (ValueError, TypeError):
        return "0.00"


# ===========================================================
# STOCK STATUS
# ===========================================================

def stock_status(stock):
    """
    Returns stock status label and visual state class (success/warning/danger).
    """
    try:
        stock_count = int(stock) if not pd.isna(stock) else 0
    except (ValueError, TypeError):
        stock_count = 0

    if stock_count >= 20:
        return "In Stock", "success"
    elif stock_count >= 5:
        return "Limited Stock", "warning"
    else:
        return "Out of Stock", "danger"


# ===========================================================
# FILE & DIRECTORY UTILITIES
# ===========================================================

def copy_file(source, destination):
    """
    Copy a single file safely, ensuring target directory exists.
    """
    if os.path.exists(source):
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(source, destination)


def copy_folder(source_folder, destination_folder):
    """
    Copy all files from source directory into target directory.
    """
    if not os.path.exists(source_folder):
        return

    os.makedirs(destination_folder, exist_ok=True)

    for file_name in os.listdir(source_folder):
        source = os.path.join(source_folder, file_name)
        if os.path.isfile(source):
            shutil.copy2(source, os.path.join(destination_folder, file_name))


# ===========================================================
# CONSOLE LOGGING UTILITIES
# ===========================================================

def print_section(title):
    """Print formatted console header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def print_success(message):
    print(f"✓ {message}")


def print_warning(message):
    print(f"⚠ {message}")


def print_error(message):
    print(f"✖ {message}")


# ===========================================================
# CREATE PRODUCT OBJECT
# ===========================================================

def create_product(row):
    """
    Convert an Excel record into a dictionary prepared for Jinja2 rendering.
    """
    # Safely extract raw numeric values
    wholesale_val = row.get("Wholesale Price per Pack (Rs)", 0)
    pieces_val = row.get("Pieces per Pack", 0)
    raw_piece_price = row.get("Price per Piece (Rs)", 0)

    # Calculate fallback price_per_piece if missing or zero
    try:
        ppp = float(raw_piece_price) if not pd.isna(raw_piece_price) else 0.0
        pieces_float = float(pieces_val) if not pd.isna(pieces_val) else 0.0
        wholesale_float = float(wholesale_val) if not pd.isna(wholesale_val) else 0.0

        if ppp <= 0 and pieces_float > 0:
            ppp = round(wholesale_float / pieces_float, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        ppp = 0.0

    # Extract strings safely avoiding 'nan' text outputs
    category = str(row.get("Category", "")).strip() if not pd.isna(row.get("Category")) else ""
    product_name = str(row.get("Product Name", "")).strip() if not pd.isna(row.get("Product Name")) else ""
    product_code = str(row.get("Product Code", "")).strip() if not pd.isna(row.get("Product Code")) else ""
    pack_unit = str(row.get("Pack / Unit Type", "Pack")).strip() if not pd.isna(row.get("Pack / Unit Type")) else "Pack"
    notes = str(row.get("Notes", "")).strip() if not pd.isna(row.get("Notes")) else ""
    explicit_img = row.get("Image File", "") if not pd.isna(row.get("Image File")) else ""

    product = {
        "product_code": product_code,
        "category": category,
        "product_name": product_name,
        "packing": pack_unit,
        "pack_unit_type": pack_unit,
        "pieces": pieces_val if not pd.isna(pieces_val) else 0,
        "pieces_per_pack": str(pieces_val) if not pd.isna(pieces_val) and str(pieces_val) != "0" else "1",
        "wholesale_price": format_price(wholesale_val),
        "price_per_piece": format_price(ppp),
        "retail_price": format_price(row.get("Suggested Retail Price per Piece (Rs)", 0)),
        "stock": row.get("Stock Available (Packs)", 0) if not pd.isna(row.get("Stock Available (Packs)")) else 0,
        "description": notes,
        "image": find_product_image(product_name, explicit_image=explicit_img),
        "brand": BRAND_NAME,
        "tagline": TAGLINE,
        "whatsapp": WHATSAPP,
        "email": EMAIL,
        "website": WEBSITE,
        "footer": FOOTER,
        "current_year": datetime.now().year,
        "file_name": f"product_{product_code.lower()}.html",
        "carton": "",
        "pack_type": pack_unit
    }

    # Evaluate Stock Status
    stock_text, stock_class = stock_status(product["stock"])
    product["stock_text"] = stock_text
    product["stock_class"] = stock_class

    # Get Theme Branding Colors
    theme = get_theme(product["category"])
    product["primary_color"] = theme.get("primary", "#0B7D5A")
    product["secondary_color"] = theme.get("secondary", "#064E3B")
    product["accent_color"] = theme.get("accent", "#10B981")
    product["text_color"] = theme.get("text", "#1E293B")

    # Generate Dynamic Assets
    product["qr"] = generate_qr(product)
    product["icon"] = CATEGORY_ICONS.get(product["category"], "📦")

    return product