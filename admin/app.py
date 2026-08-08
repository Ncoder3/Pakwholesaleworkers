
from pathlib import Path
import json
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory
from services.excel_service import (
    dashboard_stats,
    get_products,
    add_product,
    update_product,
    delete_product
)
from services.excel_service import get_next_product_code
from services.excel_service import get_next_product_code, get_existing_categories

ADMIN_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ADMIN_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from publish import run_publish_workflow

ADMIN_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ADMIN_DIR.parent
IMAGES_FOLDER = PROJECT_ROOT / "images"

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

LOG_FILE = PROJECT_ROOT / "admin" / "publish_log.json"


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

@app.route("/inventory")
def inventory():
    return render_template("inventory.html")

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