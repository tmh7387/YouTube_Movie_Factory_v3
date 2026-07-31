"""Aviation Synergy Gamma deck design tokens.

Single source of truth for the linter and the normalizer.

Tokens are grouped into **profiles**, because Aviation Synergy runs more than
one house standard:

  training_4x3   Training decks (IOSA, FDM, internal auditor). 4:3.
                 Every value measured from IOSARBIDay3_v31_1.pptx, 43 slides,
                 production-corrected. See AVS_Gamma_Deck_SPEC.md.

  corporate_16x9 Corporate presentations, from the Claude Design
                 "Aviation Synergy PPT Template" (11 layouts). Canvas, colour,
                 fonts, type ramp and layouts are measured. Char budgets are
                 ESTIMATED -- the template ships uniform placeholder copy that
                 carries no overflow signal -- so it sets budgets_provisional.

The brand palette is authoritative over any deck or design file:

    #103558  Prussian Blue      #FFFFFF  White
    #027EA7  Cerulean           #6E6E6E  Dim gray
    #E9E8E8  Platinum           #E58F65  Atomic tangerine

Both source files drifted from it by a channel or two (#103458 navy in the
training .pptx, #0080A9 teal in the design bundle). Those are listed as
`variants` so the normalizer folds them back rather than enshrining them.

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

    # Brand palette is authoritative: #103558 "Prussian Blue" is the house navy.
    # The exported .pptx carries #103458 on 283 body runs -- a one-digit drift
    # introduced downstream of the brand spec, folded back here.
    "colour": {
        "primary": "103558",        # Prussian Blue -- canonical
        "variants": ["103458"],     # drift found in .pptx body copy, 283 runs
        "accent": "027EA7",         # Cerulean
        "platinum": "E9E8E8",
        "dim_gray": "6E6E6E",
        "tangerine": "E58F65",
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
        # Measured by rendering the design in headless Chromium at 1920x1080
        # and normalising out the deck-stage transform. Supersedes the CSS
        # padding values, which belonged to sub-elements rather than the slide.
        "margin_left_in": 0.764,   # 110px, symmetric
        "margin_right_in": 0.764,  # 110px
        "content_width_in": 11.806,  # 1700px
    },

    # Brand palette (Prussian Blue / Cerulean / Platinum / White / Dim gray /
    # Atomic tangerine) is authoritative. The design file matches on navy and
    # tangerine but ships a slightly-off teal, so that one folds back.
    "colour": {
        "primary": "103558",       # Prussian Blue -- all h1/h2/h3, 47 uses
        "variants": ["0080A9"],    # design-file teal, 3 channels off Cerulean
        "accent": "027EA7",        # Cerulean -- brand spec
        "platinum": "E9E8E8",
        "dim_gray": "6E6E6E",
        "tangerine": "E58F65",     # Atomic tangerine -- exact match, 11 uses
        "reverse": "FFFFFF",
        # Tints the design introduces beyond the six brand colours. Kept
        # separate so they are visibly elaboration, not brand values.
        "design_body": "3D5570",
        "design_muted": "5C7085",
        "design_warm_dark": "C96F45",
        "design_lettermark": "5EC8DC",
        "backgrounds": ["FAFCFE", "F1F6FA", "F4F9FC", "E8F1F7", "E9EFF5"],
    },

    "fonts": {
        "heading": "Michroma",     # all headings + eyebrow labels, 74 uses
        "body": "Inter",
        "quote_glyph": "Georgia",  # the decorative opening quote only
    },

    "min_font_pt": 12.0,

    # MEASURED. The design was rendered in headless Chromium at 1920x1080 and
    # every text element grown word by word until a descendant clipped past the
    # section's fixed 1080px bounds (sections are height:1080px, overflow:hidden).
    # max_chars is the worst case across all 11 layouts, floored at the longest
    # string the template itself ships -- so a value here fits every layout.
    "type_ramp": {
        "cover_title":     {"pt": 31.0, "max_chars": 64},
        "section_title":   {"pt": 29.0, "max_chars": 194},
        "closing_title":   {"pt": 28.0, "max_chars": 90},
        "agenda_title":    {"pt": 26.0, "max_chars": 429},
        "title":           {"pt": 25.0, "max_chars": 246},  # workhorse slide title
        "image_statement": {"pt": 23.0, "max_chars": 25},   # tightest box in the set
        "quote":           {"pt": 23.0, "max_chars": 662},
        "card_title":      {"pt": 16.0, "max_chars": 241},
        "agenda_item":     {"pt": 15.0, "max_chars": 151},
        "body":            {"pt": 14.0, "max_chars": 80},
        "supporting":      {"pt": 13.5, "max_chars": 222},
        "presenter":       {"pt": 13.0, "max_chars": 195},
        "note":            {"pt": 12.5, "max_chars": 219},
        "eyebrow":         {"pt": 12.0, "max_chars": 35},   # at capacity by design
        "stat_numeral":    {"pt": 44.0, "max_chars": 5},    # at capacity by design
        "step_numeral":    {"pt": 22.0, "max_chars": 1},
    },

    # Budgets below are measured, not estimated. Note they describe the DESIGN's
    # box capacity -- the point at which content clips in this fixed-height
    # template. Gamma responds to the same pressure by shrinking type instead of
    # clipping, so treat these as the ceiling for a fixed-layout render and
    # re-measure against a Gamma export if you drive generation from this profile.
    #
    # Budget varies with box HEIGHT as much as width: the 6.67in slot holds only
    # 80 chars at 14pt because it is short, while the 2.71in slot holds 176.
    # Each entry is therefore the worst case observed at that width and size.
    "budgets_provisional": False,

    "columns": {
        "full":    {"width_in": 11.81, "body_pt": 25.0, "budget": 471},
        "wide":    {"width_in": 6.67,  "body_pt": 14.0, "budget": 80},
        "half":    {"width_in": 5.56,  "body_pt": 15.0, "budget": 682},
        "content": {"width_in": 4.72,  "body_pt": 15.0, "budget": 151},
        "third":   {"width_in": 3.75,  "body_pt": 14.0, "budget": 268},
        "quarter": {"width_in": 2.71,  "body_pt": 14.0, "budget": 176},
    },
    "default_column": "wide",   # tightest body slot -- safe default

    "max_body_lines_per_block": 6,
    # The design ships explicit 4-up layouts -- Key Figures is "four large
    # numbers with tracked labels", Timeline is "four milestones on a teal
    # line" -- so 4, not the 3 that training_4x3 uses.
    "max_subheads_per_card": 4,

    # Measured left edges from the rendered design (>=3 occurrences each).
    # The dominant edge is 110px / 0.764in, used by 49 elements.
    "grid": {
        "columns": [0.764, 1.007, 1.076, 1.181, 1.264, 1.361,
                    1.910, 4.521, 5.111, 6.833, 7.146, 7.201,
                    9.153, 9.882, 12.250],
        "snap_min_in": 0.010,
        "snap_max_in": 0.060,
    },

    # There IS a logo: a 34x34px mark sits at a fixed spot on slides 2-9.
    # Cover and closing carry larger brand marks at their own positions.
    "logo": {
        "width_in": 0.236,
        "height_in": 0.236,
        "top_in": 6.938,
        "x_content_in": 0.764,
        "x_section_in": 0.764,   # same slot on every content slide
        "detect_max_width_in": 0.40,
        "detect_min_top_in": 6.50,
    },
    "brand_marks": {
        "cover":   {"x_in": 1.326, "y_in": 1.326, "w_in": 1.389, "h_in": 1.192},
        "closing": {"x_in": 5.938, "y_in": 1.864, "w_in": 1.458, "h_in": 1.251},
    },

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
