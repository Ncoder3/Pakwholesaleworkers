"""
===========================================================
AL BARAKA TRADERS
CATEGORY THEMES
===========================================================

Every category has its own colors.

generate.py only calls

theme = get_theme(category)

and receives the complete theme dictionary.

===========================================================
"""

# ===========================================================
# CATEGORY THEMES
# ===========================================================

CATEGORY_THEMES = {

    "Stationery": {

        "primary": "#3949AB",
        "secondary": "#E8EAF6",
        "accent": "#7986CB",
        "text": "#1A237E"

    },

    "Baby Care": {

        "primary": "#0B7D5A",
        "secondary": "#EAF8F3",
        "accent": "#D4AF37",
        "text": "#173D2D"

    },

    "Household Cleaning": {

        "primary": "#1565C0",
        "secondary": "#E3F2FD",
        "accent": "#42A5F5",
        "text": "#0D47A1"

    },

    "Kitchen": {

        "primary": "#EF6C00",
        "secondary": "#FFF3E0",
        "accent": "#FFA726",
        "text": "#E65100"

    },

    "Disposable Items": {

        "primary": "#8E24AA",
        "secondary": "#F3E5F5",
        "accent": "#CE93D8",
        "text": "#4A148C"

    },

    "Personal Care": {

        "primary": "#D81B60",
        "secondary": "#FCE4EC",
        "accent": "#F06292",
        "text": "#880E4F"

    },

    "Medical": {

        "primary": "#C62828",
        "secondary": "#FFEBEE",
        "accent": "#EF5350",
        "text": "#8E0000"

    }

}

# ===========================================================
# DEFAULT THEME
# ===========================================================

DEFAULT_THEME = {

    "primary": "#0B7D5A",

    "secondary": "#F5F5F5",

    "accent": "#D4AF37",

    "text": "#173D2D"

}

# ===========================================================
# GET THEME
# ===========================================================

def get_theme(category):
    """
    Return theme colors for a category.

    Unknown categories use DEFAULT_THEME.
    """

    if category is None:

        return DEFAULT_THEME

    category = str(category).strip()

    return CATEGORY_THEMES.get(
        category,
        DEFAULT_THEME
    )