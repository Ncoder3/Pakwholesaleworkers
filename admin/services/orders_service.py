import json
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from services.excel_service import load_products, ALL_COLUMNS, EXCEL_FILE
from services.database import get_db_connection

SERVICE_DIR = Path(__file__).resolve().parent
ADMIN_DIR = SERVICE_DIR.parent
PROJECT_ROOT = ADMIN_DIR.parent

ORDERS_FILE = PROJECT_ROOT / "data" / "orders.json"
EXCEL_ORDERS_FILE = PROJECT_ROOT / "data" / "Orders_Database.xlsx"


def ensure_orders_file():
    """Ensure data folder and orders.json exist."""
    ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ORDERS_FILE.exists():
        with open(ORDERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)


def load_orders():
    """Load all orders sorted by date descending."""
    ensure_orders_file()
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            orders = json.load(f)
            return sorted(orders, key=lambda x: x.get("created_at", ""), reverse=True)
    except Exception as e:
        print(f"Error reading orders file: {e}")
        return []


def save_orders(orders):
    """Save order list to JSON."""
    ensure_orders_file()
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=4)


def save_order_to_excel(order):
    """Appends order details to Orders_Database.xlsx as an Excel-based database."""
    rows = []
    for item in order.get("items", []):
        rows.append({
            "Order ID": order.get("order_id"),
            "Date": order.get("created_at"),
            "Customer Name": order.get("customer_name"),
            "Phone": order.get("phone"),
            "Address": order.get("address"),
            "Product Code": item.get("product_code"),
            "Product Name": item.get("product_name"),
            "Packs": item.get("packs"),
            "Pack Price (Rs)": item.get("pack_price"),
            "Line Total (Rs)": item.get("line_total"),
            "Grand Total (Rs)": order.get("total_amount"),
            "Status": order.get("status")
        })

    new_df = pd.DataFrame(rows)

    if EXCEL_ORDERS_FILE.exists():
        existing_df = pd.read_excel(EXCEL_ORDERS_FILE)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_excel(EXCEL_ORDERS_FILE, index=False, engine="openpyxl")
    else:
        new_df.to_excel(EXCEL_ORDERS_FILE, index=False, engine="openpyxl")


def get_next_order_id():
    """
    Generates the next incremental Order ID (e.g., ORD-1036)
    by taking the maximum ID sequence across:
    - active PostgreSQL orders
    - deleted PostgreSQL orders
    - local active orders
    - local deleted orders
    """
    max_num = 1000
    conn = get_db_connection()

    if conn:
        try:
            cur = conn.cursor()
            # Check if deleted_orders table exists in PostgreSQL.
            # RealDictCursor returns a dictionary-like row,
            # so we must access the result by column name.
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'deleted_orders'
                ) AS table_exists;
            """)
            table_result = cur.fetchone()
            has_deleted_table = (
                table_result["table_exists"]
                if table_result
                else False
            )
            if has_deleted_table:
                query = """
                    SELECT MAX(num) AS max_num
                    FROM (
                        SELECT CAST(
                            SUBSTRING(order_id FROM '[0-9]+$')
                            AS INTEGER
                        ) AS num
                        FROM orders
                        WHERE order_id ~ '^ORD-[0-9]+$'

                        UNION ALL

                        SELECT CAST(
                            SUBSTRING(order_id FROM '[0-9]+$')
                            AS INTEGER
                        ) AS num
                        FROM deleted_orders
                        WHERE order_id ~ '^ORD-[0-9]+$'
                    ) AS all_orders;
                """
            else:
                query = """
                    SELECT MAX(
                        CAST(
                            SUBSTRING(order_id FROM '[0-9]+$')
                            AS INTEGER
                        )
                    ) AS max_num
                    FROM orders
                    WHERE order_id ~ '^ORD-[0-9]+$';
                """

            cur.execute(query)
            result = cur.fetchone()

            if result and result["max_num"] is not None:
                max_num = max(max_num, result["max_num"])

        except Exception as e:
            print(f"Error checking DB max order ID: {e}")
        finally:
            conn.close()

    # ---------------------------------------------------------
    # Fallback / supplemental check against local JSON files
    # ---------------------------------------------------------

    orders = load_orders()
    deleted_orders = []
    try:
        from pathlib import Path
        import json
        deleted_file = Path("data/deleted_orders.json")
        if deleted_file.exists():
            with open(deleted_file, "r", encoding="utf-8") as f:
                deleted_orders = json.load(f)
    except Exception:
        deleted_orders = []

    # Check both active and deleted local orders.
    for o in (orders + deleted_orders):
        order_id_str = str(o.get("order_id", ""))
        match = re.search(r'\d+$', order_id_str)
        if match:
            max_num = max(
                max_num,
                int(match.group())
            )

    # Generate next ID.
    next_num = max_num + 1
    return f"ORD-{next_num}"

def get_deleted_orders():
    """
    Returns deleted orders from PostgreSQL deleted_orders table,
    newest deleted order first.

    The deleted_orders table already stores:
    - order_id
    - customer information
    - total amount
    - source
    - deleted_at
    - complete order_data including items
    """

    conn = get_db_connection()

    if not conn:
        return None

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                order_id,
                customer_name,
                customer_phone,
                customer_city,
                customer_address,
                total_amount,
                source,
                deleted_at,
                order_data
            FROM deleted_orders
            ORDER BY deleted_at DESC;
        """)

        rows = cur.fetchall()

        deleted_orders = []

        for row in rows:
            # Convert RealDictCursor row into a normal dictionary
            order = dict(row)

            # PostgreSQL JSONB is normally already returned as a Python dict.
            # This extra check safely handles it if it comes back as text.
            order_data = order.get("order_data")

            if isinstance(order_data, str):
                try:
                    order_data = json.loads(order_data)
                except (json.JSONDecodeError, TypeError):
                    order_data = {}

            if not isinstance(order_data, dict):
                order_data = {}

            # Keep the complete archived order information.
            # Values stored directly in deleted_orders remain available
            # even if something is missing from order_data.
            order["order_data"] = order_data

            # Make the original order fields easily available to frontend.
            order["created_at"] = order_data.get(
                "created_at",
                order.get("created_at")
            )

            order["status"] = order_data.get(
                "status",
                "Deleted"
            )

            order["items"] = order_data.get(
                "items",
                []
            )

            deleted_orders.append(order)

        return deleted_orders

    except Exception as e:
        print(f"Error loading deleted orders: {e}")
        raise

    finally:
        conn.close()

def create_order(customer_data, items, source="Website"):
    """
    Creates a new order, calculates total cost dynamically, 
    saves to orders.json, and appends rows to Orders_Database.xlsx.
    Items format: [{"product_code": "ABT-001", "packs": 2}, ...]
    """
    orders = load_orders()
    products_df = load_products().set_index("Product Code")
    
    order_items = []
    total_amount = 0.0

    for item in items:
        code = str(item.get("product_code", "")).strip()
        packs = int(item.get("packs", 1))

        if code in products_df.index:
            row = products_df.loc[code]
            unit_price = float(row.get("Wholesale Price per Pack (Rs)", 0))
            line_total = unit_price * packs
            
            order_items.append({
                "product_code": code,
                "product_name": str(row.get("Product Name", "")),
                "pack_price": unit_price,
                "packs": packs,
                "line_total": line_total
            })
            total_amount += line_total

    new_order = {
        "order_id": get_next_order_id(),
        "customer_name": str(customer_data.get("name", "")).strip(),
        "phone": str(customer_data.get("phone", "")).strip(),
        "address": str(customer_data.get("address", "")).strip(),
        "status": "Pending",  # Pending, Processing, Completed, Cancelled
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_amount": round(total_amount, 2),
        "items": order_items,
        "notes": str(customer_data.get("notes", "")).strip()
    }

    orders.append(new_order)
    save_orders(orders)
    save_order_to_excel(new_order)  # Syncs order directly into Excel sheet database
    
    return True, "Order created successfully.", new_order["order_id"]


def update_order_status(order_id, new_status):
    """
    Updates order status. Deducts stock from main inventory Excel when status moves to 'Completed'.
    Also updates status in Orders_Database.xlsx if present.
    """
    orders = load_orders()
    order_found = None

    for order in orders:
        if order["order_id"] == order_id:
            order_found = order
            break

    if not order_found:
        return False, "Order not found."

    old_status = order_found["status"]
    if old_status == new_status:
        return True, f"Order status is already '{new_status}'."

    # If transitioning to Completed, deduct stock from main product Excel
    if new_status == "Completed" and old_status != "Completed":
        df = load_products()
        
        for item in order_found.get("items", []):
            code = item["product_code"]
            packs_bought = int(item["packs"])
            
            mask = df["Product Code"].astype(str).str.strip() == code
            if mask.any():
                idx = df[mask].index[0]
                current_stock = int(float(df.at[idx, "Stock Available (Packs)"] or 0))
                new_stock = max(0, current_stock - packs_bought)
                df.at[idx, "Stock Available (Packs)"] = new_stock

        df = df.reindex(columns=ALL_COLUMNS)
        df.to_excel(EXCEL_FILE, index=False, engine="openpyxl")

    order_found["status"] = new_status
    save_orders(orders)

    # Sync status update to Orders_Database.xlsx if file exists
    if EXCEL_ORDERS_FILE.exists():
        try:
            excel_orders = pd.read_excel(EXCEL_ORDERS_FILE)
            if "Order ID" in excel_orders.columns:
                excel_orders.loc[excel_orders["Order ID"] == order_id, "Status"] = new_status
                excel_orders.to_excel(EXCEL_ORDERS_FILE, index=False, engine="openpyxl")
        except Exception as e:
            print(f"Failed to sync status update to Excel database: {e}")

    return True, f"Order status updated to '{new_status}'."