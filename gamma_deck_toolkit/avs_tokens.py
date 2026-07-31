"""Aviation Synergy Gamma deck design tokens.

Single source of truth for the linter and the normalizer.

Tokens are grouped into **profiles**, because Aviation Synergy runs more than
one house standard:

  training_4x3   Training decks (IOSA, FDM, internal auditor). 4:3.
                 Every value measured from IOSARBIDay3_v31_1.pptx, 43 slides,
                 production-corrected. See AVS_Gamma_Deck_SPEC.md.

  corporate_16x9 Corporate presentations, from the Claude Design
                 "Aviation Synergy PPT Template". NOT YET POPULATED -- awaiting
                 the .dc.html bundle so the tokens can be measured rather than
                 guessed. Do not invent values here.

Add a profile by copying the training_4x3 dict and replacing measured values.
Never hand-tune a number in here without a source deck to measure it from.
"""

EMU_PER_INCH = 914400


def inches(emu):
    return emu / EMU_PER_INCH


def emu(inches_value):
    return int(round(inches_value * EMU_PER_INCH))


# --- Profiles ---------------------------------------------------------------

TRAINING_4X3 = {
    "name": "training_4x3",
    "description": "Aviation Synergy training decks (IOSA / FDM / auditor). 4:3.",
    "source": "IOSARBIDay3_v31_1.pptx (43 slides)",

    "canvas": {
        "gamma_dimensions": "4x3",
        "width_in": 10.00,
        "height_in": 7.50,
        "margin_left_in": 0.54,
        "margin_right_in": 0.55,
        "content_width_in": 8.91,
    },

    "colour": {
        "primary": "103458",        # canonical brand navy, 283 runs
        "variants": ["103558"],     # near-identical strays to fold in, 65 runs
        "accent": "1A6496",
        "reverse": "FFFFFF",
    },

    "fonts": {
        "heading": "Open Sans Bold",
        "body": "Fira Sans",
        "body_bold": "Fira Sans Bold",
    },

    "min_font_pt": 14.0,

    # Role -> (point size, max characters). Char limits are the p90 observed in
    # the corrected deck: the level at which Gamma's auto-fit stops shrinking.
    "type_ramp": {
        "hero_title":  {"pt": 40.0, "max_chars": 25},
        "title":       {"pt": 34.5, "max_chars": 36},
        "agenda_item": {"pt": 24.0, "max_chars": 30},
        "lead_in":     {"pt": 20.0, "max_chars": 60},
        "subhead":     {"pt": 17.0, "max_chars": 27},
        "body":        {"pt": 14.0, "max_chars": 86},
        "table_cell":  {"pt": 14.0, "max_chars": 25},
    },

    # Named body-column shapes. `budget` is p90 chars per line -- exceeding it
    # is what causes overflow, which is what causes auto-shrink.
    "columns": {
        "standard": {"width_in": 5.63, "body_pt": 14.0, "budget": 86},
        "half":     {"width_in": 4.22, "body_pt": 16.0, "budget": 63},
        "narrow":   {"width_in": 4.00, "body_pt": 16.0, "budget": 70},
        "wide":     {"width_in": 8.61, "body_pt": 15.0, "budget": 92},
    },
    "default_column": "standard",

    "max_body_lines_per_block": 6,
    "max_subheads_per_card": 3,

    # Left-edge positions that recur across the deck. The normalizer snaps to
    # these only when a shape is already inside the drift band.
    "grid": {
        "columns": [0.54, 0.61, 0.71, 0.81, 2.05, 3.83,
                    4.28, 5.11, 5.16, 5.24, 6.95, 7.56],
        # Below snap_min is sub-visual rounding noise (the values above are
        # themselves rounded to 2dp); above snap_max it was a deliberate
        # placement and must not be moved.
        "snap_min_in": 0.010,
        "snap_max_in": 0.060,
    },

    "logo": {
        "width_in": 1.00,
        "height_in": 0.84,
        "top_in": 6.46,
        "x_content_in": 8.81,   # 34 slides
        "x_section_in": 6.14,   # 9 section dividers
        "detect_max_width_in": 1.20,
        "detect_min_top_in": 5.90,
    },

    # Pass to mcp__Gamma__generate / generate_from_template on every run.
    # textMode "preserve" is the critical entry: it stops Gamma expanding the
    # outline into prose, the direct cause of overflow and auto-shrink.
    "generation_profile": {
        "themeId": "6k7l8ert7ql57ok",  # Aviation Synergy 2024
        "textMode": "preserve",
        "cardSplit": "inputTextBreaks",
        "cardOptions": {
            "dimensions": "4x3",
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
    },
}


PROFILES = {
    "training_4x3": TRAINING_4X3,
}

DEFAULT_PROFILE = "training_4x3"

# Profiles that are declared but not yet measured. Named here so the tools can
# fail with a useful message instead of a KeyError.
PENDING_PROFILES = {
    "corporate_16x9": (
        "Awaiting the Claude Design 'Aviation Synergy PPT Template' .dc.html "
        "bundle. Tokens must be measured from it, not guessed."
    ),
}


def get_profile(name=None):
    """Return a profile dict by name, with a useful error for pending ones."""
    name = name or DEFAULT_PROFILE
    if name in PROFILES:
        return PROFILES[name]
    if name in PENDING_PROFILES:
        raise KeyError(f"profile '{name}' is not populated yet: {PENDING_PROFILES[name]}")
    known = ", ".join(sorted(PROFILES))
    raise KeyError(f"unknown profile '{name}'. Available: {known}")


def profile_names():
    return sorted(PROFILES)
