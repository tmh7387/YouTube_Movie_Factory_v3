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


CORPORATE_16X9 = {
    "name": "corporate_16x9",
    "description": "Aviation Synergy corporate presentations. 16:9.",
    "source": "Claude Design 'Aviation Synergy PPT Template', 11 layouts",

    # Design canvas is 1920x1080 CSS px, declared on the deck-stage import.
    # That is 144 px/in against PowerPoint's 13.333x7.5in 16:9 slide, so every
    # px value in the source converts to points by halving it.
    "canvas": {
        "gamma_dimensions": "16x9",
        "width_in": 13.333,
        "height_in": 7.50,
        "px_per_inch": 144,
        "margin_left_in": 0.625,   # 90px
        "margin_right_in": 0.625,
        "margin_top_in": 0.556,    # 80px
        "content_width_in": 12.083,
    },

    "colour": {
        "primary": "103558",       # navy -- all h1/h2/h3, 47 uses
        "variants": [],            # no strays in the source design
        "accent": "0080A9",        # teal -- eyebrow labels, numerals, 57 uses
        "body": "3D5570",          # mid slate -- subtitles and body copy
        "muted": "5C7085",         # light slate -- captions, presenter, notes
        "warm": "E58F65",          # links and the quote glyph
        "warm_dark": "C96F45",     # link hover
        "lettermark": "5EC8DC",    # cyan "AS" on the navy brand mark
        "reverse": "FFFFFF",
        "backgrounds": ["FAFCFE", "F1F6FA", "F4F9FC", "E8F1F7", "E9EFF5"],
    },

    "fonts": {
        "heading": "Michroma",     # all headings + eyebrow labels, 74 uses
        "body": "Inter",
        "quote_glyph": "Georgia",  # the decorative opening quote only
    },

    "min_font_pt": 12.0,

    # Measured from the source design (px halved). max_chars here are the
    # PLACEHOLDER lengths, not overflow thresholds -- see budgets_provisional.
    "type_ramp": {
        "cover_title":     {"pt": 31.0, "max_chars": 28},
        "section_title":   {"pt": 29.0, "max_chars": 23},
        "closing_title":   {"pt": 28.0, "max_chars": 9},
        "agenda_title":    {"pt": 26.0, "max_chars": 6},
        "title":           {"pt": 25.0, "max_chars": 21},   # workhorse slide title
        "image_statement": {"pt": 23.0, "max_chars": 25},
        "quote":           {"pt": 23.0, "max_chars": 60},
        "card_title":      {"pt": 16.0, "max_chars": 17},
        "agenda_item":     {"pt": 15.0, "max_chars": 28},
        "body":            {"pt": 14.0, "max_chars": 60},
        "supporting":      {"pt": 13.5, "max_chars": 60},
        "presenter":       {"pt": 13.0, "max_chars": 42},
        "note":            {"pt": 12.5, "max_chars": 21},
        "eyebrow":         {"pt": 12.0, "max_chars": 35},   # most common, 53 uses
        "stat_numeral":    {"pt": 44.0, "max_chars": 5},
        "step_numeral":    {"pt": 22.0, "max_chars": 1},
    },

    # IMPORTANT: unlike training_4x3, these budgets are NOT measured overflow
    # thresholds. The source template ships uniform ~60-char placeholder copy,
    # which carries no signal about where Gamma starts shrinking. These are
    # estimated by holding the training profile's chars-per-inch at a given
    # point size (86 chars / 5.63in at 14pt = 15.3 ch/in) and applying it to
    # this canvas's column widths. Inter runs slightly wider than Fira Sans, so
    # treat them as a starting point.
    #
    # To replace with real numbers: generate one corporate deck, export it, and
    # run the same title-length-vs-point-size analysis used for training_4x3.
    "budgets_provisional": True,

    "columns": {
        "full":   {"width_in": 12.08, "body_pt": 14.0, "budget": 185},
        "half":   {"width_in": 5.90,  "body_pt": 14.0, "budget": 90},
        "third":  {"width_in": 3.83,  "body_pt": 13.5, "budget": 60},
    },
    "default_column": "half",

    "max_body_lines_per_block": 6,
    "max_subheads_per_card": 3,

    # No measured grid yet -- the source design uses flex/grid layout rather
    # than absolute positions, so left-edge columns only become knowable from a
    # real .pptx export. Snapping is a no-op until then.
    "grid": {
        "columns": [],
        "snap_min_in": 0.010,
        "snap_max_in": 0.060,
    },

    # The source design places no explicit logo image on its slides -- brand
    # presence comes from the background art and the cover mark. Populate from a
    # real export before enabling the logo step.
    "logo": None,

    "layouts": [
        "Cover", "Agenda", "Section Divider", "Content + Image",
        "Three-Column Cards", "Key Figures", "Timeline",
        "Comparison Table", "Quote", "Full-Bleed Image", "Closing",
    ],

    "generation_profile": {
        # No Gamma theme id yet: the design lives on labs.gamma.app, which the
        # production API cannot see. Fill this in once a matching custom theme
        # exists in the main workspace.
        "themeId": None,
        "textMode": "preserve",
        "cardSplit": "inputTextBreaks",
        "cardOptions": {"dimensions": "16x9"},
        "textOptions": {
            "amount": "brief",
            "language": "en-gb",
            "tone": "professional",
        },
    },
}


PROFILES = {
    "training_4x3": TRAINING_4X3,
    "corporate_16x9": CORPORATE_16X9,
}

DEFAULT_PROFILE = "training_4x3"

# Profiles that are declared but not yet measured. Named here so the tools can
# fail with a useful message instead of a KeyError.
PENDING_PROFILES = {}


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
