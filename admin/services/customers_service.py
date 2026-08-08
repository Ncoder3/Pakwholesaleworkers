import json
from datetime import datetime
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parent
ADMIN_DIR = SERVICE_DIR.parent
PROJECT_ROOT = ADMIN_DIR.parent

from services.orders_service import load_orders

CUSTOMERS_FILE = PROJECT_ROOT / "data" / "customers.json"

def ensure_customers_file():
    """Ensure data folder and customers.json exist."""
    CUSTOMERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not CUSTOMERS_FILE.exists():
        with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)

def load_customers():
    """Load all customer profiles merged with real-time order statistics."""
    ensure_customers_file()
    try:
        with open(CUSTOMERS_FILE, "r", encoding="utf-8") as f:
            customers = json.load(f)
    except Exception as e:
        print(f"Error reading customers file: {e}")
        customers = []

    orders = load_orders()
    
    # Calculate lifetime stats from orders per customer phone / name
    for cust in customers:
        phone = cust.get("phone", "").strip()
        name = cust.get("name", "").strip().lower()
        
        cust_orders = [
            o for o in orders 
            if (phone and o.get("phone", "").strip() == phone) or 
               (o.get("customer_name", "").strip().lower() == name)
        ]
        
        cust["total_orders"] = len(cust_orders)
        cust["lifetime_spend"] = round(sum(o.get("total_amount", 0) for o in cust_orders if o.get("status") != "Cancelled"), 2)
        cust["last_order_date"] = cust_orders[0].get("created_at") if cust_orders else "No Orders"

    return customers

def save_customers(customers):
    """Save customer profiles list to JSON."""
    ensure_customers_file()
    with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=4)

def create_customer(data):
    """Creates a new customer profile."""
    customers = load_customers()
    phone = str(data.get("phone", "")).strip()

    if phone and any(c.get("phone") == phone for c in customers):
        return False, "A customer with this phone number already exists."

    new_cust = {
        "id": f"CUST-{len(customers) + 1001}",
        "name": str(data.get("name", "")).strip(),
        "store_name": str(data.get("store_name", "")).strip(),
        "phone": phone,
        "address": str(data.get("address", "")).strip(),
        "tier": str(data.get("tier", "Standard Wholesale")),  # Standard, VIP, Distributor
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "notes": str(data.get("notes", "")).strip()
    }

    customers.append(new_cust)
    save_customers(customers)
    return True, "Customer profile created successfully."