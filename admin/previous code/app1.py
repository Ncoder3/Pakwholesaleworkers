from flask import Flask, render_template
from flask import request, jsonify

from services.excel_service import dashboard_stats
from services.excel_service import get_products
from services.excel_service import update_product

from flask import send_from_directory

from pathlib import Path

app = Flask(__name__)


@app.route("/")
def dashboard():

    stats = dashboard_stats()

    return render_template(
        "dashboard.html",
        stats=stats
    )


@app.route("/products")
def products():

    df = get_products()

    products = df.to_dict(orient="records")

    return render_template(

        "products.html",

        products=products

    )


@app.route("/inventory")
def inventory():

    return render_template("inventory.html")


@app.route("/orders")
def orders():

    return render_template("orders.html")


@app.route("/customers")
def customers():

    return render_template("customers.html")

PROJECT_ROOT = Path(__file__).resolve().parents[1]

IMAGES_FOLDER = PROJECT_ROOT / "images"


@app.route("/images/<filename>")
def product_image(filename):

    return send_from_directory(IMAGES_FOLDER, filename)

@app.route("/update_product", methods=["POST"])
def update_product_route():

    data = request.get_json()

    success = update_product(data)

    return jsonify({
        "success": success
    })

@app.route("/product-images/<filename>")
def product_images(filename):
    return send_from_directory("../images", filename)


@app.route("/analytics")
def analytics():

    return render_template("analytics.html")


if __name__ == "__main__":

    app.run(
        debug=True
    )