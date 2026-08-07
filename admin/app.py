from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from services.excel_service import (
    dashboard_stats,
    get_products,
    add_product,
    update_product,
    delete_product
)

ADMIN_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ADMIN_DIR.parent
IMAGES_FOLDER = PROJECT_ROOT / "images"

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

@app.route("/")
def dashboard():
    stats = dashboard_stats()
    return render_template("dashboard.html", stats=stats)

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

@app.route("/update_product", methods=["POST"])
def update_product_route():
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

    success, message = update_product(product_data, image_file)
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)