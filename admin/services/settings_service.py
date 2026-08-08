import re
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parent
ADMIN_DIR = SERVICE_DIR.parent
PROJECT_ROOT = ADMIN_DIR.parent

CONFIG_FILE = PROJECT_ROOT / "scripts" / "config.py"

def read_config():
    """Dynamically reads key-value pairs from scripts/config.py."""
    config_data = {}
    if not CONFIG_FILE.exists():
        return config_data

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract string assignments using regex
    patterns = {
        "BRAND_NAME": r'BRAND_NAME\s*=\s*["\'](.*?)["\']',
        "TAGLINE": r'TAGLINE\s*=\s*["\'](.*?)["\']',
        "CITY": r'CITY\s*=\s*["\'](.*?)["\']',
        "COUNTRY": r'COUNTRY\s*=\s*["\'](.*?)["\']',
        "WHATSAPP": r'WHATSAPP\s*=\s*["\'](.*?)["\']',
        "EMAIL": r'EMAIL\s*=\s*["\'](.*?)["\']',
        "WEBSITE": r'WEBSITE\s*=\s*["\'](.*?)["\']',
        "PRODUCT_PREFIX": r'PRODUCT_PREFIX\s*=\s*["\'](.*?)["\']',
        "CURRENCY": r'CURRENCY\s*=\s*["\'](.*?)["\']',
        "PRIMARY_COLOR": r'PRIMARY_COLOR\s*=\s*["\'](.*?)["\']',
        "SECONDARY_COLOR": r'SECONDARY_COLOR\s*=\s*["\'](.*?)["\']',
        "FOOTER": r'FOOTER\s*=\s*["\'](.*?)["\']'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        config_data[key] = match.group(1) if match else ""

    return config_data

def update_config(new_settings):
    """Updates key variables in scripts/config.py while maintaining structure."""
    if not CONFIG_FILE.exists():
        return False, "config.py file not found."

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    for key, val in new_settings.items():
        pattern = rf'({key}\s*=\s*)["\'].*?["\']'
        replacement = rf'\1"{val}"'
        content = re.sub(pattern, replacement, content)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    return True, "Settings saved successfully and synced with config.py."