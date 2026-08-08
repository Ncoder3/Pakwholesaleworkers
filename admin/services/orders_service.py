import json
from datetime import datetime
from pathlib import Path
from services.excel_service import load_products, ALL_COLUMNS, EXCEL_FILE

SERVICE_DIR = Path(__file__).resolve().parent
ADMIN_DIR = SERVICE_DIR.parent
PROJECT_ROOT = ADMIN_DIR.parent

ORDERS_FILE = PROJECT_ROOT / "data" / "orders.json"

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

def get_next_order_id():
    """Generates next incremental Order ID e.g., ORD-1001."""
    orders = load_orders()
    if not orders:
        return "ORD-1001"
    
    ids = []
    for o in orders:
        try:
            num = int(str(o.get("order_id", "")).replace("ORD-", ""))
            ids.append(num)
        except ValueError:
            continue
            
    next_num = max(ids) + 1 if ids else 1001
    return f"ORD-{next_num}"

def create_order(customer_data, items):
    """
    Creates a new order and calculates total cost dynamically.
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
    return True, "Order created successfully.", new_order["order_id"]

def update_order_status(order_id, new_status):
    """
    Updates order status. Deducts stock from Excel when status moves to 'Completed'.
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

    # If transitioning to Completed, deduct stock from Excel
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
    return True, f"Order status updated to '{new_status}'."