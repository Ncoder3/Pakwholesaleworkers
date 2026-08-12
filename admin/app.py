import io
import json
import os
from pathlib import Path
import sys
import time
import zipfile
import requests

from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, abort
from flask_cors import CORS

# Path and Environment Setup
ADMIN_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ADMIN_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

IMAGES_FOLDER = PROJECT_ROOT / "images"
HTML_OUTPUT_FOLDER = PROJECT_ROOT / "output" / "html"
PNG_OUTPUT_FOLDER = PROJECT_ROOT / "output" / "png"
LOG_FILE = PROJECT_ROOT / "admin" / "publish_log.json"

# Service Imports
from publish import run_publish_workflow
from services.excel_service import (
    dashboard_stats,
    get_products,
    add_product,
    update_product,
    delete_product,
    get_next_product_code,
    get_existing_categories
)
from services.orders_service import load_orders, create_order as local_create_order, save_orders, update_order_status
from services.customers_service import load_customers, create_customer
from services.analytics_service import get_analytics_metrics
from services.settings_service import read_config, update_config
from services.database import get_db_connection, init_db

# App Initialization
app = Flask(__name__, template_folder="templates", static_folder="static")

# CORS Setup for Cloudflare domain & local testing
CORS(app, origins=[
    "https://pakwholesaleworkers.pages.dev",
    "https://pakwholesaleworkers.up.railway.app",
    "http://localhost:5000",
    "http://127.0.0.1:5000"
])

# Initialize PostgreSQL Schema if DB is configured
init_db()

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def process_stock_status(products):
    """Categorizes stock levels into Red, Yellow, and Green badges."""
    in_stock_count = 0
    low_stock_count = 0
    out_of_stock_count = 0

    for p in products:
        try:
            stock = int(p.get("Stock Available (Packs)", 0))
        except (ValueError, TypeError):
            stock = 0
        
        if stock == 0:
            p["stock_status"] = "out_of_stock"
            p["stock_color"] = "red"
            out_of_stock_count += 1
        elif stock <= 5:
            p["stock_status"] = "low_stock"
            p["stock_color"] = "yellow"
            low_stock_count += 1
        else:
            p["stock_status"] = "in_stock"
            p["stock_color"] = "green"
            in_stock_count += 1

    return products, {
        "in_stock": in_stock_count,
        "low_stock": low_stock_count,
        "out_of_stock": out_of_stock_count
    }

import re

def safe_float(val, default=0.0):
    if val in [None, ""]:
        return default
    try:
        # Strip currency symbols (Rs), spaces, and commas
        clean_val = re.sub(r"[^\d.]", "", str(val))
        return float(clean_val) if clean_val else default
    except (ValueError, TypeError):
        return default

def safe_int(val, default=1):
    if val in [None, ""]:
        return default
    try:
        clean_val = re.sub(r"[^\d]", "", str(val))
        return int(clean_val) if clean_val else default
    except (ValueError, TypeError):
        return default

# ==========================================
# ORDER ENDPOINTS (HYBRID DB / LOCAL)
# ==========================================

@app.route('/api/orders/create', methods=['POST', 'OPTIONS'])
@app.route('/api/order', methods=['POST', 'OPTIONS'])
def submit_order():
    """Handles order creation with dynamic product lookup & PostgreSQL customer upsert."""
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json() or {}
    customer = data.get('customer', {})
    items = data.get('items', [])
    source = data.get('source', 'Website')  # Capture source: 'Website' or 'Dashboard'

    if not customer.get('name') or not customer.get('phone') or not items:
        return jsonify({'success': False, 'message': 'Missing required order details'}), 400

    # Build product lookup map to automatically fetch real name and wholesale price
    all_products = get_products()
    product_map = {
        str(p.get('Product Code')).strip(): p 
        for p in all_products if p.get('Product Code')
    }

    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # 1. UPSERT Customer into PostgreSQL 'customers' table
            cust_name = customer.get('name', '').strip()
            cust_phone = customer.get('phone', '').strip()
            cust_city = customer.get('city', '').strip()
            cust_address = customer.get('address', '').strip()
            
            if cust_phone:
                cur.execute("""
                    INSERT INTO customers (name, phone, city, address)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (phone) DO UPDATE 
                    SET name = EXCLUDED.name,
                        city = COALESCE(EXCLUDED.city, customers.city),
                        address = COALESCE(EXCLUDED.address, customers.address);
                """, (cust_name, cust_phone, cust_city, cust_address))

            # 2. Generate Order ID
            cur.execute("SELECT COUNT(*) FROM orders;")
            count_res = cur.fetchone()
            count = count_res['count'] if count_res else 0
            order_id = f"ORD-{1001 + count}"

            # 3. Calculate line totals with fallback lookup
            processed_items = []
            total_amount = 0.0

            for item in items:
                # Key fallbacks for product code
                code = str(item.get('product_code') or item.get('code') or item.get('id') or '').strip()
                
                # Key fallbacks for quantity / packs
                packs = safe_int(item.get('packs') or item.get('quantity') or item.get('qty'), default=1)
                
                matched_prod = product_map.get(code, {})
                
                # Key fallbacks for product name
                prod_name = (
                    item.get('product_name') 
                    or item.get('name') 
                    or item.get('title') 
                    or matched_prod.get('Product Name') 
                    or 'Unknown Product'
                )
                
                # Key fallbacks for price
                raw_price = item.get('price') if item.get('price') is not None else item.get('unit_price')
                if raw_price is not None and str(raw_price).strip() != "":
                    unit_price = safe_float(raw_price)
                else:
                    unit_price = safe_float(matched_prod.get('Wholesale Price per Pack (Rs)', 0.0))

                subtotal = unit_price * packs
                total_amount += subtotal

                processed_items.append({
                    'code': code,
                    'name': prod_name,
                    'packs': packs,
                    'price': unit_price,
                    'subtotal': subtotal
            })

            # 4. Insert into 'orders' with is_read and source columns
            cur.execute("""
                INSERT INTO orders (
                    order_id, customer_name, customer_phone, customer_city, 
                    customer_address, customer_notes, total_amount, is_read, source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                order_id,
                cust_name,
                cust_phone,
                cust_city,
                cust_address,
                customer.get('notes', ''),
                total_amount,
                False,   # Always marked as unread upon creation
                source   # Stores 'Website' or 'Dashboard'
            ))

            # 5. Insert into 'order_items'
            for p_item in processed_items:
                cur.execute("""
                    INSERT INTO order_items (order_id, product_code, product_name, quantity, unit_price, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (
                    order_id,
                    p_item['code'],
                    p_item['name'],
                    p_item['packs'],
                    p_item['price'],
                    p_item['subtotal']
                ))

            conn.commit()
            return jsonify({'success': True, 'order_id': order_id, 'message': 'Order submitted successfully!'}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
        finally:
            conn.close()
    else:
        # File fallback (passes source context)
        success, message, order_id = local_create_order(customer, items, source=source)
        return jsonify({'success': success, 'order_id': order_id, 'message': message})

    
@app.route('/api/orders/update-status', methods=['POST'])
def api_update_order_status():
    try:
        data = request.get_json() or {}
        order_id = data.get("order_id")
        status = data.get("status")

        if not order_id or not status:
            return jsonify({"success": False, "message": "Missing order ID or status."}), 400

        conn = get_db_connection()

        # Update Order Status directly without altering product stock
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("UPDATE orders SET status = %s WHERE order_id = %s;", (status, order_id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                return jsonify({"success": False, "message": f"DB Error: {str(e)}"}), 500
            finally:
                conn.close()
        else:
            success, message = update_order_status(order_id, status)
            if not success:
                return jsonify({"success": False, "message": message})

        return jsonify({"success": True, "message": f"Order {order_id} status updated to {status}."})

    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {str(e)}"}), 500

# To add  the automatic stock deduction feature,
# @app.route('/api/orders/update-status', methods=['POST'])
# def api_update_order_status():
#     try:
#         data = request.get_json() or {}
#         order_id = data.get("order_id")
#         status = data.get("status")

#         if not order_id or not status:
#             return jsonify({"success": False, "message": "Missing order ID or status."}), 400

#         conn = get_db_connection()
#         items_to_deduct = []

#         # 1. Update Order Status in Database or Local File
#         if conn:
#             try:
#                 cur = conn.cursor()
#                 cur.execute("UPDATE orders SET status = %s WHERE order_id = %s;", (status, order_id))
                
#                 # Fetch order items to sync stock if marked as Completed
#                 if status == "Completed":
#                     cur.execute("SELECT product_code, quantity FROM order_items WHERE order_id = %s;", (order_id,))
#                     items_to_deduct = cur.fetchall()
#                 conn.commit()
#             except Exception as e:
#                 conn.rollback()
#                 return jsonify({"success": False, "message": f"DB Error: {str(e)}"}), 500
#             finally:
#                 conn.close()
#         else:
#             success, message = update_order_status(order_id, status)
#             if not success:
#                 return jsonify({"success": False, "message": message})
            
#             if status == "Completed":
#                 orders_list = load_orders()
#                 matched_order = next((o for o in orders_list if o.get("order_id") == order_id), None)
#                 if matched_order:
#                     items_to_deduct = matched_order.get("items", [])

#         # 2. Deduct Stock from Products in Excel / Storage
#         if status == "Completed" and items_to_deduct:
#             all_products = get_products()
            
#             for item in items_to_deduct:
#                 # Handle both Dict cursor and fallback dict object
#                 code = str(item.get("product_code") or item.get("code") or "").strip()
#                 deduct_qty = int(item.get("quantity") or item.get("packs") or 0)

#                 target_prod = next((p for p in all_products if str(p.get("Product Code")).strip() == code), None)
#                 if target_prod:
#                     current_stock = int(target_prod.get("Stock Available (Packs)", 0))
#                     new_stock = max(0, current_stock - deduct_qty)
                    
#                     target_prod["original_code"] = target_prod.get("Product Code")
#                     target_prod["Stock Available (Packs)"] = new_stock
                    
#                     # Persist updated stock count back to storage/Excel
#                     update_product(target_prod)

#         return jsonify({"success": True, "message": f"Order {order_id} updated and stock synced!"})

#     except Exception as e:
#         return jsonify({"success": False, "message": f"Server Error: {str(e)}"}), 500

#for order management, we will not automatically deduct stock when an order is marked as completed. This is to prevent accidental stock depletion in case of order cancellations or returns. 
#Instead, stock management should be handled manually or through a dedicated inventory adjustment process.
#order updation from dashbaord or from order page.

ADMIN_DELETE_PIN = "2345"

@app.route('/api/orders/delete/<order_id>', methods=['DELETE', 'POST'])
def delete_single_order(order_id):
    # Check Admin PIN passed in headers
    client_pin = request.headers.get('X-Admin-PIN') or request.args.get('pin')
    if client_pin != ADMIN_DELETE_PIN:
        return jsonify({'success': False, 'message': 'Unauthorized: Incorrect Admin PIN'}), 403

    try:
        orders = load_orders()
        updated_orders = [o for o in orders if str(o.get('order_id')) != str(order_id)]
        
        if len(orders) == len(updated_orders):
            return jsonify({'success': False, 'message': 'Order not found'}), 404
            
        save_orders(updated_orders)
        return jsonify({'success': True, 'message': f'Order {order_id} deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/orders/clear-all', methods=['POST'])
def clear_all_orders():
    # Check Admin PIN passed in headers
    client_pin = request.headers.get('X-Admin-PIN') or request.args.get('pin')
    if client_pin != ADMIN_DELETE_PIN:
        return jsonify({'success': False, 'message': 'Unauthorized: Incorrect Admin PIN'}), 403

    try:
        save_orders([])
        return jsonify({'success': True, 'message': 'All orders cleared successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orders/unread-count', methods=['GET'])
def get_unread_orders_count():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE LOWER(COALESCE(source, 'website')) = 'website') AS website_count,
                    COUNT(*) FILTER (WHERE LOWER(source) IN ('dashboard', 'manual')) AS manual_count
                FROM orders 
                WHERE is_read = FALSE;
            """)
            res = cur.fetchone()
            
            # Handle dictionary cursor or tuple access safely
            if res:
                total = res['total'] if isinstance(res, dict) else res[0]
                web_cnt = res['website_count'] if isinstance(res, dict) else res[1]
                man_cnt = res['manual_count'] if isinstance(res, dict) else res[2]
            else:
                total, web_cnt, man_cnt = 0, 0, 0

            return jsonify({
                'success': True, 
                'unread_count': total or 0,
                'website_count': web_cnt or 0,
                'manual_count': man_cnt or 0
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            conn.close()
    else:
        # Fallback for local JSON file storage (load_orders)
        orders_list = load_orders()
        unread_orders = [o for o in orders_list if not o.get('is_read', False)]
        
        web_cnt = sum(
            1 for o in unread_orders 
            if o.get('source', 'website').lower() == 'website' or not o.get('source')
        )
        man_cnt = sum(
            1 for o in unread_orders 
            if o.get('source', '').lower() in ['dashboard', 'manual']
        )
        
        return jsonify({
            'success': True, 
            'unread_count': len(unread_orders),
            'website_count': web_cnt,
            'manual_count': man_cnt
        })

@app.route('/api/orders/mark-read', methods=['POST'])
def mark_orders_read():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("UPDATE orders SET is_read = TRUE WHERE is_read = FALSE;")
            conn.commit()
            return jsonify({'success': True, 'message': 'Orders marked as read'})
        finally:
            conn.close()
    return jsonify({'success': True})
    
@app.route('/orders')
def orders():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM orders ORDER BY created_at DESC;")
            all_orders = cur.fetchall()
            for o in all_orders:
                cur.execute("SELECT * FROM order_items WHERE order_id = %s;", (o['order_id'],))
                o['items'] = cur.fetchall()
        finally:
            conn.close()
    else:
        all_orders = load_orders()

    products = get_products()
    return render_template('orders.html', orders=all_orders, products=products)

@app.route('/orders/<order_id>/invoice')
def order_invoice(order_id):
    conn = get_db_connection()
    order = None
    items_list = []

    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM orders WHERE order_id = %s;", (order_id,))
            order = cur.fetchone()
            if order:
                cur.execute("SELECT * FROM order_items WHERE order_id = %s;", (order_id,))
                items_list = cur.fetchall()
        finally:
            conn.close()
    else:
        orders_list = load_orders()
        order = next((o for o in orders_list if o.get("order_id") == order_id), None)
        if order:
            items_list = order.get("items", [])

    if not order:
        abort(404, description="Order not found")
        
    return render_template('invoice.html', order=order, items=items_list)

# ==========================================
# DASHBOARD & INVENTORY ROUTES
# ==========================================

@app.route("/")
def dashboard():
    raw_products = get_products()
    products, stock_summary = process_stock_status(raw_products)
    stats = dashboard_stats()
    
    stats["in_stock"] = stock_summary["in_stock"]
    stats["low_stock"] = stock_summary["low_stock"]
    stats["out_of_stock"] = stock_summary["out_of_stock"]

    last_publish = {
        "timestamp": "Never",
        "success": True,
        "message": "No publish actions performed yet.",
        "error_details": "",
    }
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                last_publish = json.load(f)
        except Exception:
            pass

    return render_template("dashboard.html", stats=stats, last_publish=last_publish)

@app.route("/inventory")
def inventory():
    raw_products = get_products()
    products, _ = process_stock_status(raw_products)
    categories = get_existing_categories()
    return render_template("inventory.html", products=products, categories=categories)

@app.route("/products")
def products_page():
    raw_products = get_products()
    products, _ = process_stock_status(raw_products)
    next_code = get_next_product_code()
    existing_categories = get_existing_categories()

    return render_template(
        "products.html",
        products=products,
        next_code=next_code,
        existing_categories=existing_categories
    )

@app.route("/add-product", methods=["GET"])
def add_product_page():
    next_code = get_next_product_code()
    return render_template("add_product.html", next_code=next_code)

@app.route("/add_product", methods=["POST"])
def add_product_route():
    product_data = {
        "Product Code": request.form.get("Product Code"),
        "Product Name": request.form.get("Product Name"),
        "Category": request.form.get("Category"),
        "Pack / Unit Type": request.form.get("Pack / Unit Type"),
        "Pieces per Pack": request.form.get("Pieces per Pack", 0),
        "Wholesale Price per Pack (Rs)": request.form.get("Wholesale Price per Pack (Rs)", 0),
        "Suggested Retail Price per Piece (Rs)": request.form.get("Suggested Retail Price per Piece (Rs)", 0),
        "Stock Available (Packs)": request.form.get("Stock Available (Packs)", 0),
        "Notes": request.form.get("Notes", "")
    }
    image_file = request.files.get("product_image")
    success, message = add_product(product_data, image_file)
    return jsonify({"success": success, "message": message})

@app.route("/update_product", methods=["POST"])
def update_product_route():
    try:
        product_data = {
            "original_code": request.form.get("original_code") or request.form.get("Product Code"),
            "Product Code": request.form.get("Product Code"),
            "Product Name": request.form.get("Product Name"),
            "Category": request.form.get("Category"),
            "Pack / Unit Type": request.form.get("Pack / Unit Type"),
            "Pieces per Pack": safe_int(request.form.get("Pieces per Pack")),
            "Wholesale Price per Pack (Rs)": safe_float(request.form.get("Wholesale Price per Pack (Rs)")),
            "Suggested Retail Price per Piece (Rs)": safe_float(request.form.get("Suggested Retail Price per Piece (Rs)")),
            "Stock Available (Packs)": safe_int(request.form.get("Stock Available (Packs)")),
            "Notes": request.form.get("Notes", "")
        }
        image_file = request.files.get("product_image")

        success, message = update_product(product_data, image_file)
        status_code = 200 if success else 400
        return jsonify({"success": success, "message": message}), status_code

    except Exception as e:
        app.logger.error(f"Error updating product: {str(e)}")
        return jsonify({"success": False, "message": f"Server Error: {str(e)}"}), 500

@app.route("/delete_product", methods=["POST"])
def delete_product_route():
    data = request.get_json() or {}
    code = data.get("product_code")
    if not code:
        return jsonify({"success": False, "message": "Product code missing"})
    success, message = delete_product(code)
    return jsonify({"success": success, "message": message})

@app.route("/api/update-stock", methods=["POST"])
def update_stock_route():
    data = request.get_json() or {}
    code = data.get("product_code")
    new_stock = data.get("new_stock")

    if not code or new_stock is None:
        return jsonify({"success": False, "message": "Missing product code or stock count."}), 400

    products = get_products()
    target_product = next((p for p in products if str(p.get("Product Code")).strip() == str(code).strip()), None)

    if not target_product:
        return jsonify({"success": False, "message": "Product not found."}), 404

    target_product["original_code"] = target_product.get("Product Code")
    target_product["Stock Available (Packs)"] = int(new_stock)

    success, message = update_product(target_product)
    return jsonify({"success": success, "message": message, "new_stock": int(new_stock)})

# ==========================================
# ASSET & EXPORT ROUTES
# ==========================================

@app.route("/api/export-pngs", methods=["POST"])
def export_selected_pngs():
    data = request.get_json() or {}
    selected_codes = data.get("product_codes", [])

    if not selected_codes:
        return jsonify({"success": False, "message": "No products selected"}), 400

    zip_buffer = io.BytesIO()
    found_files = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for code in selected_codes:
            png_path = PNG_OUTPUT_FOLDER / f"{code}.png"
            raw_img = None
            for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                candidate = IMAGES_FOLDER / f"{code}{ext}"
                if candidate.exists():
                    raw_img = candidate
                    break

            if png_path.exists():
                zip_file.write(png_path, arcname=f"{code}_card.png")
                found_files += 1
            elif raw_img and raw_img.exists():
                zip_file.write(raw_img, arcname=f"{code}{raw_img.suffix}")
                found_files += 1

    if found_files == 0:
        return jsonify({"success": False, "message": "No images or PNG cards found for selected products."}), 404

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="selected_products_images.zip"
    )

@app.route("/images/<filename>")
def product_image(filename):
    return send_from_directory(IMAGES_FOLDER, filename)

# ==========================================
# CUSTOMERS, ANALYTICS & SETTINGS
# ==========================================

@app.route('/customers')
def customers():
    return render_template('customers.html', customers=load_customers())

@app.route('/api/customers/create', methods=['POST'])
def api_create_customer():
    try:
        data = request.get_json() or {}
        if not data.get("name") or not data.get("phone"):
            return jsonify({"success": False, "message": "Name and Phone number are required."}), 400

        success, message = create_customer(data)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {str(e)}"}), 500

@app.route('/analytics')
def analytics():
    return render_template('analytics.html', metrics=get_analytics_metrics())

@app.route('/settings')
def settings():
    return render_template('settings.html', config=read_config())

@app.route('/api/settings/update', methods=['POST'])
def api_update_settings():
    try:
        data = request.get_json() or {}
        success, message = update_config(data)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "message": f"Server Error: {str(e)}"}), 500

# ==========================================
# PUBLISH & DEPLOYMENT ROUTES
# ==========================================

@app.route("/publish_site", methods=["POST"])
def publish_site_route():
    success, message = run_publish_workflow()
    return jsonify({"success": success, "message": message})

@app.route('/api/publish-remote', methods=['POST'])
def trigger_remote_publish():
    """Triggers GitHub Actions rebuild for Cloudflare Pages."""
    github_token = os.environ.get("GITHUB_DISPATCH_TOKEN")
    repo_owner = os.environ.get("GITHUB_REPO_OWNER", "Ncoder3")
    repo_name = os.environ.get("GITHUB_REPO_NAME", "Pakwholesaleworkers")

    if not github_token:
        success, message = run_publish_workflow()
        return jsonify({"success": success, "message": message})

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"event_type": "remote_publish_trigger"}

    res = requests.post(
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/dispatches",
        json=payload,
        headers=headers
    )

    if res.status_code == 204:
        return jsonify({"success": True, "message": "Remote site rebuild triggered on Cloudflare/GitHub!"}), 200
    return jsonify({"success": False, "message": f"Failed to trigger GitHub Action: {res.text}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)