import pandas as pd
from pathlib import Path

# Path to your Excel file
excel_path = Path("data/products.xlsx")  # Adjust path if located elsewhere

# Load Excel file
df = pd.read_excel(excel_path, engine="openpyxl")

# Recalculate Price per Piece (Rs) and round strictly to 2 decimal places
df["Price per Piece (Rs)"] = (
    df["Wholesale Price per Pack (Rs)"] / df["Pieces per Pack"]
).round(2)

# Save back to Excel
df.to_excel(excel_path, index=False, engine="openpyxl")
print("Successfully updated 'Price per Piece (Rs)' values to 2 decimal places!")