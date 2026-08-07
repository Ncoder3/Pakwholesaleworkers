import os
from pathlib import Path
import pandas as pd
from werkzeug.utils import secure_filename

# PROJECT_ROOT points to AlBarakaCatalogGenerator (parent of admin)
SERVICE_DIR = Path(__file__).resolve().parent
ADMIN_DIR = SERVICE_DIR.parent
PROJECT_ROOT = ADMIN_DIR.parent

EXCEL_FILE = PROJECT_ROOT / "data" / "products.xlsx"
IMAGE_FOLDER = PROJECT_ROOT / "images"

def ensure_data_file():
    """Ensure the Excel file directory exists and file contains basic columns if new."""
    EXCEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not EXCEL_FILE.exists():
        columns = [
            "Product Code", "Product Name", "Category", "Pack / Unit Type",
            "Pieces per Pack", "Wholesale Price per Pack (Rs)",
            "Suggested Retail Price per Piece (Rs)", "Stock Available (Packs)", 
            "Notes", "Image File"
        ]
        df = pd.DataFrame(columns=columns)
        df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")

def load_products():
    ensure_data_file()
    
    try:
        # Read Excel using explicit openpyxl engine
        df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        # Return fallback empty dataframe on read failure
        return pd.DataFrame(columns=[
            "Product Code", "Product Name", "Category", "Pack / Unit Type",
            "Pieces per Pack", "Wholesale Price per Pack (Rs)",
            "Suggested Retail Price per Piece (Rs)", "Stock Available (Packs)", 
            "Notes", "Image File"
        ])

    # Sanitize NaN values for clean rendering
    df = df.fillna("")
    
    # Ensure numeric columns are formatted properly
    numeric_cols = [
        "Pieces per Pack", 
        "Wholesale Price per Pack (Rs)", 
        "Suggested Retail Price per Piece (Rs)", 
        "Stock Available (Packs)"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            
    return df

def save_product_image(image_file, product_name):
    """Saves uploaded image as {product_name}.jpg/png into /images directory."""
    if not image_file or not image_file.filename:
        return None
    
    IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Extract file extension (.jpg, .png, etc.)
    ext = Path(image_file.filename).suffix.lower()
    if not ext:
        ext = ".jpg"
        
    # Format filename: replace spaces with underscores to match catalog structure
    clean_name = product_name.strip().replace(" ", "_")
    filename = f"{clean_name}{ext}"
    
    target_path = IMAGE_FOLDER / filename
    image_file.save(target_path)
    return filename

def get_products():
    df = load_products()
    
    # Generate image filename dynamically from Product Name if not explicitly stored
    def set_image_filename(row):
        if "Image File" in row and row["Image File"]:
            return row["Image File"]
        name = str(row["Product Name"]).strip()
        return f"{name.replace(' ', '_')}.jpg" if name else "default.jpg"

    df["Image File"] = df.apply(set_image_filename, axis=1)
    return df

def dashboard_stats():
    df = load_products()
    total_products = len(df)
    total_categories = df["Category"].nunique() if "Category" in df.columns else 0
    total_stock = int(df["Stock Available (Packs)"].sum()) if "Stock Available (Packs)" in df.columns else 0
    
    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "total_stock": total_stock
    }

def add_product(product_data, image_file=None):
    df = load_products()
    
    # Check for duplicate product code
    if "Product Code" in df.columns and str(product_data.get("Product Code")) in df["Product Code"].astype(str).values:
        return False, "Product Code already exists."

    # Process and save uploaded image
    if image_file:
        saved_filename = save_product_image(image_file, product_data.get("Product Name", "product"))
        if saved_filename:
            product_data["Image File"] = saved_filename

    new_row = pd.DataFrame([product_data])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")
    return True, "Product added successfully."

def update_product(product_data, image_file=None):
    df = load_products()
    
    # Match product by code (converting both to string)
    mask = df["Product Code"].astype(str) == str(product_data.get("Product Code"))
    if not mask.any():
        return False, "Product not found."

    index = df[mask].index[0]

    # Save new image if uploaded
    if image_file:
        saved_filename = save_product_image(image_file, product_data.get("Product Name", "product"))
        if saved_filename:
            df.at[index, "Image File"] = saved_filename

    df.at[index, "Product Name"] = product_data.get("Product Name")
    df.at[index, "Category"] = product_data.get("Category")
    df.at[index, "Pack / Unit Type"] = product_data.get("Pack / Unit Type")
    df.at[index, "Pieces per Pack"] = product_data.get("Pieces per Pack")
    df.at[index, "Wholesale Price per Pack (Rs)"] = product_data.get("Wholesale Price per Pack (Rs)")
    df.at[index, "Suggested Retail Price per Piece (Rs)"] = product_data.get("Suggested Retail Price per Piece (Rs)")
    df.at[index, "Stock Available (Packs)"] = product_data.get("Stock Available (Packs)")
    df.at[index, "Notes"] = product_data.get("Notes")

    df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")
    return True, "Product updated successfully."

def delete_product(product_code):
    df = load_products()
    mask = df["Product Code"].astype(str) == str(product_code)
    
    if not mask.any():
        return False, "Product not found."

    df = df[~mask]
    df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")
    return True, "Product deleted successfully."