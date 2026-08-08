
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
# INVENTORY, PNG EXPORT & STOCK UPDATE API
# ==========================================

@app.route("/inventory")
def inventory():
    products = get_products()
    categories = get_existing_categories()
    return render_template("inventory.html", products=products, categories=categories)

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
            # Check generated PNG first, fallback to original uploaded image
            png_path = PNG_OUTPUT_FOLDER / f"{code}.png"
            
            # Find any image starting with code in IMAGES_FOLDER
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

@app.route("/products")
def products_page():
    products = get_products()
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

@app.route("/")
def dashboard():
    stats = dashboard_stats()

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



@app.route("/products")
def products():
    df = get_products()
    products_list = df.to_dict(orient="records")
    return render_template("products.html", products=products_list)

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


@app.route("/delete_product", methods=["POST"])
def delete_product_route():
    data = request.get_json() or {}
    code = data.get("product_code")
    if not code:
        return jsonify({"success": False, "message": "Product code missing"})
    success, message = delete_product(code)
    return jsonify({"success": success, "message": message})

@app.route("/images/<filename>")
def product_image(filename):
    return send_from_directory(IMAGES_FOLDER, filename)

@app.route("/api/adjust-stock", methods=["POST"])
def adjust_stock():
    data = request.get_json() or {}
    code = data.get("product_code")
    delta = int(data.get("delta", 0))

    products = get_products()
    for product in products:
        if product["Product Code"] == code:
            current_stock = int(product.get("Stock Available (Packs)", 0))
            new_stock = max(0, current_stock + delta)
            product["Stock Available (Packs)"] = new_stock
            
            # Save updated data back via update_product service
            update_product(product)
            return jsonify({"success": True, "new_stock": new_stock})

    return jsonify({"success": False, "message": "Product not found"}), 404

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

@app.route("/update_product", methods=["POST"])
def update_product_route():
    product_data = {
        "original_code": request.form.get("original_code") or request.form.get("Product Code"),
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

    success, message = update_product(product_data, image_file)
    return jsonify({"success": success, "message": message})

if __name__ == "__main__":
    app.run(debug=True, port=5000)