"""Aviation Synergy Gamma deck design tokens.

Single source of truth for the linter and the normalizer. Every value here was
measured from IOSARBIDay3_v31_1.pptx (43 slides, production-corrected) rather
than chosen by hand -- see AVS_Gamma_Deck_SPEC.md for the derivation.

Canvas is 4:3 (10.00 x 7.50 in). If the house standard ever moves to 16:9,
change CANVAS and re-derive COLUMNS/LOGO; nothing else should need editing.
"""

EMU_PER_INCH = 914400


def inches(emu):
    return emu / EMU_PER_INCH


def emu(inches_value):
    return int(round(inches_value * EMU_PER_INCH))


# --- Canvas -----------------------------------------------------------------

CANVAS = {
    "name": "4x3",
    "width_in": 10.00,
    "height_in": 7.50,
    "margin_left_in": 0.54,
    "margin_right_in": 0.55,
    "content_width_in": 8.91,
}

# Gamma's cardOptions.dimensions value matching CANVAS.
GAMMA_DIMENSIONS = "4x3"


# --- Colour -----------------------------------------------------------------

NAVY = "103458"          # canonical brand navy (283 runs)
NAVY_VARIANTS = ["103558"]  # near-identical strays to fold into NAVY (65 runs)
ACCENT = "1A6496"
REVERSE = "FFFFFF"


# --- Type -------------------------------------------------------------------

HEADING_FONT = "Open Sans Bold"
BODY_FONT = "Fira Sans"
BODY_FONT_BOLD = "Fira Sans Bold"

# Minimum legible size. Nothing in a production deck should fall below this.
MIN_FONT_PT = 14.0

# Role -> (point size, max characters). Char limits are the p90 observed in the
# corrected deck, which is the level at which Gamma's auto-fit stops shrinking.
TYPE_RAMP = {
    "hero_title":  {"pt": 40.0, "max_chars": 25},
    "title":       {"pt": 34.5, "max_chars": 36},
    "agenda_item": {"pt": 24.0, "max_chars": 30},
    "lead_in":     {"pt": 20.0, "max_chars": 60},
    "subhead":     {"pt": 17.0, "max_chars": 27},
    "body":        {"pt": 14.0, "max_chars": 86},
    "table_cell":  {"pt": 14.0, "max_chars": 25},
}


# --- Body line budgets ------------------------------------------------------
# Column width (in) + size (pt) -> p90 characters per line. Exceeding these is
# what triggers overflow, which is what triggers Gamma's auto-shrink.

LINE_BUDGETS = {
    ("standard", 14.0): 86,   # 5.63 in text column, archetype B
    ("standard", 16.0): 110,
    ("half", 14.0): 83,       # 4.22 in column, archetype C
    ("half", 16.0): 63,
    ("narrow", 16.0): 70,     # 4.00 in column
    ("wide", 15.0): 92,       # 8.61 in full-bleed list, archetype E
}

# Named column profiles the linter can be pointed at.
COLUMN_PROFILES = {
    "standard": {"width_in": 5.63, "body_pt": 14.0, "budget": 86},
    "half":     {"width_in": 4.22, "body_pt": 16.0, "budget": 63},
    "narrow":   {"width_in": 4.00, "body_pt": 16.0, "budget": 70},
    "wide":     {"width_in": 8.61, "body_pt": 15.0, "budget": 92},
}

DEFAULT_COLUMN_PROFILE = "standard"

# Cards get crowded past this regardless of individual line length.
MAX_BODY_LINES_PER_BLOCK = 6
MAX_SUBHEADS_PER_CARD = 3


# --- Layout grid ------------------------------------------------------------
# Left-edge positions that appear repeatedly across the deck. The normalizer
# snaps shapes to these only when already within SNAP_TOLERANCE_IN.

COLUMNS = [0.54, 0.61, 0.71, 0.81, 2.05, 3.83, 4.28, 5.11, 5.16, 5.24, 6.95, 7.56]

# Only correct drift inside this band. Below MIN it is sub-visual rounding noise
# (the grid values above are themselves rounded to 2dp); above TOLERANCE it was a
# deliberate placement and must not be moved.
SNAP_MIN_IN = 0.010
SNAP_TOLERANCE_IN = 0.06


# --- Logo -------------------------------------------------------------------

LOGO = {
    "width_in": 1.00,
    "height_in": 0.84,
    "top_in": 6.46,
    "x_content_in": 8.81,   # 34 slides
    "x_section_in": 6.14,   # 9 section dividers
    # A picture is treated as the logo if it is smaller than this and sits
    # below this baseline.
    "detect_max_width_in": 1.20,
    "detect_min_top_in": 5.90,
}


# --- Locked Gamma generation profile ---------------------------------------
# Pass this to mcp__Gamma__generate / generate_from_template on every run.
# textMode "preserve" is the critical entry: it stops Gamma expanding the
# outline into prose, which is the direct cause of overflow and auto-shrink.

GENERATION_PROFILE = {
    "themeId": "6k7l8ert7ql57ok",  # Aviation Synergy 2024
    "textMode": "preserve",
    "cardSplit": "inputTextBreaks",
    "cardOptions": {
        "dimensions": GAMMA_DIMENSIONS,
        "headerFooter": {
            "bottomRight": {"type": "image", "source": "themeLogo", "size": "sm"},
            "hideFromFirstCard": True,
        },
    },
    "textOptions": {
        "amount": "brief",
        "language": "en-gb",
        "tone": "professional",
    },
    "imageOptions": {"source": "themeAccent"},
}
