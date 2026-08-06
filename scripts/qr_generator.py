"""
==========================================================
AL BARAKA TRADERS
QR CODE GENERATOR
==========================================================
"""

import os
import urllib.parse
import qrcode
from pathlib import Path
from config import WHATSAPP, OUTPUT_FOLDER


def generate_whatsapp_link(product):
    """
    Create a WhatsApp URL with a pre-filled message.
    """

    message = f"""
Hello Al Baraka Traders,

I am interested in the following product.

Product Code : {product['product_code']}
Product Name : {product['product_name']}

Please share the wholesale price and availability.

Thank you.
"""

    encoded = urllib.parse.quote(message.strip())

    return f"https://wa.me/{WHATSAPP}?text={encoded}"


def generate_qr(product):
    """
    Generate a QR code for one product.
    """

    qr_folder = Path(OUTPUT_FOLDER) / "qr"

    qr_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    url = generate_whatsapp_link(product)

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2
    )

    qr.add_data(url)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    filename = product["product_code"] + ".png"

    image.save(
        qr_folder / filename
    )
    return f"qr/{filename}"