# Aviation Synergy — Gamma Deck Toolkit

Gets a Gamma export closer to production-ready on the first pass, instead of
after a round of manual font and position fixes.

## Why this exists

Gamma **auto-fits type to content volume**. When text overflows its box, Gamma
shrinks the type — no theme setting overrides this, because it is the layout
engine rather than the style layer.

Measured across the corrected `IOSARBIDay3_v31_1.pptx` (43 slides):

| Titles | Result |
|---|---|
| 36 slides at ≤ 36 chars | held 34.5 pt |
| 6 slides at ≥ 37 chars | shrank to 33 / 31 / 30 / 29.5 / 28 pt |

So the fix is not "lock the font size". It is **stop sending Gamma content that
overflows**, then clean up whatever it still does on its own.

That is the two-stage split here:

```
outline.md  ──lint_content.py──>  Gamma generate  ──normalize_pptx.py──>  deck
            (prevent overflow)     (locked params)   (enforce tokens)
```

## Files

| File | Role |
|---|---|
| `avs_tokens.py` | All measured design tokens. Single source of truth. |
| `lint_content.py` | Pre-flight: checks an outline against char budgets. |
| `normalize_pptx.py` | Post-export: enforces tokens on a Gamma `.pptx`. |

## Install

```bash
pip install python-pptx
```

## 1. Lint before generating

Costs nothing and catches the shrink before you spend credits.

```bash
python lint_content.py outline.md
python lint_content.py outline.md --column half     # for 2-column decks
python lint_content.py outline.md --json            # for CI
```

Outline format matches what you feed Gamma with `cardSplit: "inputTextBreaks"`:

```markdown
# Slide title            <- ≤ 36 chars
## Subhead               <- ≤ 27 chars
- Body line              <- ≤ 86 chars (standard column)
---                      <- card break
```

Exits non-zero when anything is over budget.

Column profiles: `standard` (5.63in @14pt, 86), `half` (4.22in @16pt, 63),
`narrow` (4.00in @16pt, 70), `wide` (8.61in @15pt, 92).

## 2. Generate with the locked profile

`GENERATION_PROFILE` in `avs_tokens.py` holds the parameter set to pass on every
run. `textMode: "preserve"` is the critical entry — the default `generate` mode
expands your outline into prose, which is what overflows the boxes in the first
place.

## 3. Normalize the export

```bash
python normalize_pptx.py deck.pptx              # -> deck-normalized.pptx
python normalize_pptx.py deck.pptx --dry-run    # report only
python normalize_pptx.py deck.pptx --skip snap  # opt out of a step
```

| Step | Action |
|---|---|
| `floor` | Lifts any run below 14 pt |
| `colour` | Folds stray `#103558` into canonical `#103458` |
| `logo` | Snaps footer logo to 1.00 × 0.84in at y 6.46 — x 8.81 content, x 6.14 section dividers |
| `snap` | Corrects left-edge drift of 0.010–0.060in back onto the grid |
| `titles` | **Reports** shrunk titles (needs a text edit, so never forced) |

Idempotent: re-running a normalized file makes zero changes.

### On the current deck

```
colour    65 fixed     all titles carried the #103558 variant
snap      63 fixed     drifts of 0.013–0.043in
titles     6 flagged   the six over-length titles
floor      0           already ≥ 14 pt
logo       0           already correct
```

## Canvas

Tokens assume **4:3 (10.00 × 7.50in)**. The normalizer warns if the input canvas
differs. Moving to 16:9 means changing `CANVAS` and re-deriving `COLUMNS` and
`LOGO`.

## Still manual

The Gamma MCP cannot edit an existing gamma or theme, so these are one-time jobs
in the Gamma editor:

- Unify the theme text colour to `#103458`
- Confirm heading font **Open Sans Bold**, body **Fira Sans**
- Upload the AVS logo as **theme logo** (enables `headerFooter` auto-placement)
- Save a corrected deck as a **Template** — the workspace currently has none,
  so `generate_from_template` is unavailable until one exists
