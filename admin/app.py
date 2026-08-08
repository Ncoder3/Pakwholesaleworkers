from pathlib import Path
import json
import sys
import os
import zipfile
import io
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file

from services.excel_service import (
    dashboard_stats,
    get_products,
    add_product,
    update_product,
    delete_product,
    get_next_product_code,
    get_existing_categories
)

ADMIN_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ADMIN_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

IMAGES_FOLDER = PROJECT_ROOT / "images"
HTML_OUTPUT_FOLDER = PROJECT_ROOT / "output" / "html"
PNG_OUTPUT_FOLDER = PROJECT_ROOT / "output" / "png"
LOG_FILE = PROJECT_ROOT / "admin" / "publish_log.json"

from publish import run_publish_workflow

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

# ==========================================
# HELPER FUNCTIONS FOR STOCK BADGES
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

# ==========================================
# DASHBOARD & INVENTORY ROUTES
# ==========================================

@app.route("/")
def dashboard():
    raw_products = get_products()
    products, stock_summary = process_stock_status(raw_products)
    stats = dashboard_stats()
    
    # Inject detailed stock status metrics for the Dashboard cards
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

    return render_template(
        "dashboard.html", stats=stats, last_publish=last_publish
    )

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

# import update_product from excel_service

@app.route("/update_product", methods=["POST"])
def update_product_route():
    try:
        def safe_float(val, default=0.0):
            try:
                return float(val) if val not in [None, ""] else default
            except (ValueError, TypeError):
                return default

        def safe_int(val, default=0):
            try:
                return int(float(val)) if val not in [None, ""] else default
            except (ValueError, TypeError):
                return default

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
    target_product = None
    for p in products:
        if str(p.get("Product Code")).strip() == str(code).strip():
            target_product = p
            break

    if not target_product:
        return jsonify({"success": False, "message": "Product not found."}), 404

    target_product["original_code"] = target_product.get("Product Code")
    target_product["Stock Available (Packs)"] = int(new_stock)

    success, message = update_product(target_product)
    return jsonify({"success": success, "message": message, "new_stock": int(new_stock)})

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

@app.route("/orders")
def orders():
    return render_template("orders.html")

@app.route("/customers")
def customers():
    return render_template("customers.html")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/publish_site", methods=["POST"])
def publish_site_route():
    success, message = run_publish_workflow()
    return jsonify({"success": success, "message": message})

if __name__ == "__main__":
    app.run(debug=True, port=5000)