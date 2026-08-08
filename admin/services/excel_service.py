import os
from pathlib import Path
import pandas as pd
import re

SERVICE_DIR = Path(__file__).resolve().parent
ADMIN_DIR = SERVICE_DIR.parent
PROJECT_ROOT = ADMIN_DIR.parent

EXCEL_FILE = PROJECT_ROOT / "data" / "products.xlsx"
IMAGE_FOLDER = PROJECT_ROOT / "images"

# Exact column sequence from your Excel file
ALL_COLUMNS = [
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


def calculate_price_per_piece(wholesale_price, pieces_per_pack):
    """Calculates Price per Piece rounded strictly to 2 decimal places."""
    try:
        wholesale = float(wholesale_price or 0)
        pieces = float(pieces_per_pack or 0)

        if pieces <= 0:
            return 0.0

        return round(wholesale / pieces, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def ensure_data_file():
    """Ensure data directory and products.xlsx exist."""
    EXCEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not EXCEL_FILE.exists():
        df = pd.DataFrame(columns=ALL_COLUMNS)
        df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")


def load_products():
    ensure_data_file()

    try:
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return pd.DataFrame(columns=ALL_COLUMNS)

    df = df.fillna("")

    numeric_cols = [
        "Pieces per Pack",
        "Wholesale Price per Pack (Rs)",
        "Price per Piece (Rs)",
        "Suggested Retail Price per Piece (Rs)",
        "Stock Available (Packs)",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Ensure all required schema columns exist
    for col in ALL_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df[ALL_COLUMNS]


def save_product_image(image_file, product_name):
    if not image_file or not image_file.filename:
        return None

    IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)

    ext = Path(image_file.filename).suffix.lower() or ".jpg"

    clean_name = str(product_name or "product").strip().replace(" ", "_")
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        clean_name = clean_name.replace(char, "")

    filename = f"{clean_name}{ext}"
    target_path = IMAGE_FOLDER / filename
    image_file.save(target_path)
    return filename


def get_products():
    df = load_products()

    def set_image_filename(row):
        if "Image File" in row and row["Image File"]:
            return str(row["Image File"]).strip()
        name = str(row["Product Name"]).strip()
        return f"{name.replace(' ', '_')}.jpg" if name else "default.jpg"

    df["Image File"] = df.apply(set_image_filename, axis=1)
    return df.to_dict(orient="records")


def dashboard_stats():
    """Calculates top-level inventory statistics for dashboard rendering."""
    df = load_products()
    total_products = len(df)
    total_categories = df["Category"].nunique() if "Category" in df.columns else 0
    total_stock = int(df["Stock Available (Packs)"].sum()) if "Stock Available (Packs)" in df.columns else 0

    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "total_stock": total_stock,
    }


def add_product(product_data, image_file=None):
    df = load_products()

    if "Product Code" in df.columns and str(product_data.get("Product Code")) in df["Product Code"].astype(str).values:
        return False, "Product Code already exists."

    product_data["Price per Piece (Rs)"] = calculate_price_per_piece(
        product_data.get("Wholesale Price per Pack (Rs)"),
        product_data.get("Pieces per Pack"),
    )

    product_data["Category"] = normalize_category_name(product_data.get("Category"))

    if image_file:
        saved_filename = save_product_image(image_file, str(product_data.get("Product Name", "product")))
        if saved_filename:
            product_data["Image File"] = saved_filename

    new_row = pd.DataFrame([product_data])
    df = pd.concat([df, new_row], ignore_index=True)
    df = df.reindex(columns=ALL_COLUMNS)
    df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")
    return True, "Product added successfully."


def update_product(product_data, image_file=None):
    df = load_products()

    search_code = str(product_data.get("original_code") or product_data.get("Product Code")).strip()
    mask = df["Product Code"].astype(str).str.strip() == search_code

    if not mask.any():
        return False, f"Product with code '{search_code}' not found."

    index = df[mask].index[0]

    price_per_piece = calculate_price_per_piece(
        product_data.get("Wholesale Price per Pack (Rs)"),
        product_data.get("Pieces per Pack"),
    )

    cat_name = normalize_category_name(product_data.get("Category"))

    if image_file and image_file.filename:
        saved_filename = save_product_image(image_file, str(product_data.get("Product Name", "product")))
        if saved_filename:
            df.at[index, "Image File"] = saved_filename

    # Explicit column updates with strict data type safety
    df.at[index, "Product Code"] = str(product_data.get("Product Code", "")).strip()
    df.at[index, "Category"] = cat_name
    df.at[index, "Product Name"] = str(product_data.get("Product Name", "")).strip()
    df.at[index, "Pack / Unit Type"] = str(product_data.get("Pack / Unit Type", "")).strip()
    df.at[index, "Pieces per Pack"] = float(product_data.get("Pieces per Pack") or 0)
    df.at[index, "Wholesale Price per Pack (Rs)"] = float(product_data.get("Wholesale Price per Pack (Rs)") or 0)
    df.at[index, "Price per Piece (Rs)"] = price_per_piece
    df.at[index, "Suggested Retail Price per Piece (Rs)"] = float(product_data.get("Suggested Retail Price per Piece (Rs)") or 0)
    df.at[index, "Stock Available (Packs)"] = int(float(product_data.get("Stock Available (Packs)") or 0))
    df.at[index, "Notes"] = str(product_data.get("Notes", "")).strip()

    df = df.reindex(columns=ALL_COLUMNS)
    df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")
    return True, "Product updated successfully."


def delete_product(product_code):
    df = load_products()
    mask = df["Product Code"].astype(str).str.strip() == str(product_code).strip()

    if not mask.any():
        return False, "Product not found."

    df = df[~mask]
    df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")
    return True, "Product deleted successfully."


def get_existing_categories():
    df = load_products()
    if "Category" not in df.columns:
        return []

    categories = [
        str(cat).strip()
        for cat in df["Category"].dropna().unique()
        if str(cat).strip() and str(cat).strip().lower() != "nan"
    ]
    return sorted(list(set(categories)))


def normalize_category_name(input_category):
    if not input_category or not str(input_category).strip():
        return "Miscellaneous"

    user_cat = str(input_category).strip()
    existing_cats = get_existing_categories()

    for cat in existing_cats:
        if cat.lower() == user_cat.lower():
            return cat

    user_stem = user_cat.lower().rstrip("s")
    for cat in existing_cats:
        cat_stem = cat.lower().rstrip("s")
        if user_stem == cat_stem or user_stem.rstrip("e") == cat_stem.rstrip("e"):
            return cat

    return user_cat.title()


def get_next_product_code(prefix="ABT-"):
    df = load_products()
    if df.empty or "Product Code" not in df.columns:
        return f"{prefix}001"

    numbers = []
    for code in df["Product Code"].dropna().astype(str):
        match = re.search(r"(\d+)", code)
        if match:
            numbers.append(int(match.group(1)))

    if not numbers:
        return f"{prefix}001"

    next_number = max(numbers) + 1
    return f"{prefix}{next_number:03d}"