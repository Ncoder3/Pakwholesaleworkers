import psycopg2
from services.database import get_db_connection
from services.orders_service import load_orders


def get_analytics_metrics():
    """
    Calculates sales revenue, order metrics, category analytics,
    and top-selling product using PostgreSQL products data.
    """

    orders = load_orders()

    # ---------------------------------------------------------
    # Order metrics
    # ---------------------------------------------------------

    valid_orders = [
        o for o in orders
        if o.get("status") != "Cancelled"
    ]

    completed_orders = [
        o for o in orders
        if o.get("status") == "Completed"
    ]

    total_revenue = sum(
        float(o.get("total_amount", 0) or 0)
        for o in valid_orders
    )

    total_orders_count = len(orders)
    completed_count = len(completed_orders)

    aov = (
        total_revenue / len(valid_orders)
        if valid_orders
        else 0.0
    )

    # ---------------------------------------------------------
    # Product/category lookup from PostgreSQL
    # ---------------------------------------------------------

    product_categories = {}

    conn = get_db_connection()

    if conn:
        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    product_code,
                    category
                FROM products;
            """)

            rows = cur.fetchall()

            for row in rows:
                product_categories[
                    str(row["product_code"]).strip()
                ] = row["category"] or "Uncategorized"

        except Exception as e:
            print(
                f"[ANALYTICS] Product lookup failed: {e}"
            )

        finally:
            conn.close()

    # ---------------------------------------------------------
    # Sales aggregation
    # ---------------------------------------------------------

    category_sales = {}
    product_units_sold = {}

    for order in valid_orders:

        for item in order.get("items", []):

            code = str(
                item.get("product_code", "")
            ).strip()

            packs = int(
                item.get("packs", 0) or 0
            )

            line_total = float(
                item.get("line_total", 0) or 0
            )

            product_units_sold[code] = (
                product_units_sold.get(code, 0)
                + packs
            )

            category = product_categories.get(
                code,
                "Uncategorized"
            )

            category_sales[category] = (
                category_sales.get(category, 0.0)
                + line_total
            )

    # ---------------------------------------------------------
    # Chart data
    # ---------------------------------------------------------

    categories_labels = (
        list(category_sales.keys())
        if category_sales
        else ["No Data"]
    )

    categories_data = (
        list(category_sales.values())
        if category_sales
        else [0]
    )

    # ---------------------------------------------------------
    # Top product
    # ---------------------------------------------------------

    top_selling_code = (
        max(
            product_units_sold,
            key=product_units_sold.get
        )
        if product_units_sold
        else "N/A"
    )

    # ---------------------------------------------------------
    # Return
    # ---------------------------------------------------------

    return {
        "total_revenue": round(
            total_revenue,
            2
        ),

        "total_orders": total_orders_count,

        "completed_orders": completed_count,

        "aov": round(
            aov,
            2
        ),

        "category_labels": categories_labels,

        "category_data": [
            round(float(value), 2)
            for value in categories_data
        ],

        "top_selling_code": top_selling_code,
    }