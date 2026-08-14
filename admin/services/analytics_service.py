import pandas as pd
from datetime import datetime
from services.product_service import load_products
from services.orders_service import load_orders

def get_analytics_metrics():
    """Calculates sales revenue, order metrics, and category analytics."""
    orders = load_orders()
    products_df = load_products()
    
    # Exclude cancelled orders for financial calculations
    valid_orders = [o for o in orders if o.get("status") != "Cancelled"]
    completed_orders = [o for o in orders if o.get("status") == "Completed"]

    total_revenue = sum(o.get("total_amount", 0.0) for o in valid_orders)
    total_orders_count = len(orders)
    completed_count = len(completed_orders)
    
    aov = (total_revenue / len(valid_orders)) if valid_orders else 0.0

    # Aggregate sales volume per product category
    category_sales = {}
    product_units_sold = {}

    for order in valid_orders:
        for item in order.get("items", []):
            code = item.get("product_code", "")
            packs = int(item.get("packs", 0))
            line_total = float(item.get("line_total", 0.0))

            product_units_sold[code] = product_units_sold.get(code, 0) + packs

            # Find product category from dataframe
            if not products_df.empty and "Product Code" in products_df.columns:
                match = products_df[products_df["Product Code"].astype(str).str.strip() == code]
                if not match.empty:
                    cat = match.iloc[0].get("Category", "Uncategorized")
                    category_sales[cat] = category_sales.get(cat, 0.0) + line_total

    # Format category breakdown for charts
    categories_labels = list(category_sales.keys()) if category_sales else ["No Data"]
    categories_data = list(category_sales.values()) if category_sales else [0]

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders_count,
        "completed_orders": completed_count,
        "aov": round(aov, 2),
        "category_labels": categories_labels,
        "category_data": categories_data,
        "top_selling_code": max(product_units_sold, key=product_units_sold.get) if product_units_sold else "N/A"
    }