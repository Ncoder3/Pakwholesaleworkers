"""
==========================================================
AL BARAKA TRADERS - CENTRAL SYSTEM CONFIGURATION
==========================================================
This module serves as the single source of truth for brand metadata,
contact details, directory structures, and global template variables.
"""

from pathlib import Path

# ==========================================================
# COMPANY & BRAND METADATA
# ==========================================================
BRAND_NAME = "Al Baraka Traders"
COMPANY_NAME = BRAND_NAME  # Dynamic alias for template engines
TAGLINE = "Your Trusted Wholesale Partner"
SOCIAL_HANDLE = "@AlBarakaTraders"
VERIFIED_TAG = "Verified Official Direct Wholesale Partner"

# Location Details
CITY = "Shah Alam Market, Lahore"
ADDRESS_LINE = "Shah Alam Market, Lahore, Punjab, Pakistan"
COUNTRY = "Pakistan"


# ==========================================================
# CONTACT INFORMATION
# ==========================================================
WHATSAPP = "923231551535"
WHATSAPP_NUMBER = WHATSAPP  # Alias for HTML/JS engines
EMAIL = "info@albarakatraders.pk"
WEBSITE = "www.albarakatradersabbott.pk"
WEBSITE_URL = WEBSITE  # Alias for HTML templates
SUPPORT_HOURS = "Mon - Sat: 9:00 AM - 8:00 PM"


# ==========================================================
# PRODUCT & CURRENCY SETTINGS
# ==========================================================
PRODUCT_PREFIX = "ABT"
CURRENCY = "Rs"
DEFAULT_IMAGE = "../images/default.png"


# ==========================================================
# PROJECT DIRECTORIES (PATH MANAGEMENT)
# ==========================================================
BASE_DIR = Path(__file__).resolve().parent

DATA_FOLDER = BASE_DIR / "data"
TEMPLATE_FOLDER = BASE_DIR / "templates"
IMAGE_FOLDER = BASE_DIR / "images"
ASSET_FOLDER = BASE_DIR / "assets"
OUTPUT_FOLDER = BASE_DIR / "output"
HTML_FOLDER = BASE_DIR / "output" / "html"
PNG_FOLDER = BASE_DIR / "output" / "png"
QR_FOLDER = BASE_DIR / "output" / "qr"

# String path aliases for legacy modules
DATA_DIR_STR = str(DATA_FOLDER)
IMAGE_DIR_STR = str(IMAGE_FOLDER)


# ==========================================================
# UI & CATALOG CARD SETTINGS
# ==========================================================
PRIMARY_COLOR = "#0b7d5a"
SECONDARY_COLOR = "#ffffff"
ACCENT_COLOR = "#10b981"

# Formatted Footer Text for Cards & Export Prints
FOOTER = "Wholesale Supplier • Quality Products • Fast Delivery • Trusted Service"