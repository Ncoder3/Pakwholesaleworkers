from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXCEL_FILE = PROJECT_ROOT / "data" / "products.xlsx"


def load_products():

    df = pd.read_excel(EXCEL_FILE)

    print("\nExcel Columns:\n")
    print(df.columns.tolist())

    return df


def dashboard_stats():

    df = load_products()

    return {
        "total_products": len(df),
        "total_categories": df["Category"].nunique(),

        # Temporary values until we inspect your columns
        "total_images": 0,
        "total_qr": len(df)
    }

def get_products():

    df = pd.read_excel(EXCEL_FILE)

    df["Image File"] = (

        df["Product Name"]

        .astype(str)

        .str.replace(" ", "_")

        + ".jpg"

    )

    df["Image File"] = df["Product Name"].apply(
    lambda x: f"{x}.jpg"
    )

    return df


def total_products():

    df = get_products()

    return len(df)

def update_product(product_data):

    df = load_products()

    index = df[
        df["Product Code"] == product_data["Product Code"]
    ].index

    if len(index) == 0:
        return False

    i = index[0]

    df.at[i, "Product Name"] = product_data["Product Name"]
    df.at[i, "Category"] = product_data["Category"]
    df.at[i, "Pack / Unit Type"] = product_data["Pack / Unit Type"]
    df.at[i, "Pieces per Pack"] = product_data["Pieces per Pack"]
    df.at[i, "Wholesale Price per Pack (Rs)"] = product_data["Wholesale Price per Pack (Rs)"]
    df.at[i, "Suggested Retail Price per Piece (Rs)"] = product_data["Suggested Retail Price per Piece (Rs)"]
    df.at[i, "Stock Available (Packs)"] = product_data["Stock Available (Packs)"]
    df.at[i, "Notes"] = product_data["Notes"]

    df.to_excel(EXCEL_FILE, index=False)

    return True

from pathlib import Path

IMAGE_FOLDER = PROJECT_ROOT / "images"