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
| `avs_tokens.py` | All measured design tokens, grouped into profiles. Single source of truth. |
| `lint_content.py` | Pre-flight: checks an outline against char budgets. |
| `normalize_pptx.py` | Post-export: enforces tokens on a Gamma `.pptx`. |

## Profiles

Aviation Synergy runs more than one house standard, so tokens are grouped into
profiles. Both tools take `--profile`.

| Profile | Status | Canvas | Source |
|---|---|---|---|
| `training_4x3` | ✅ measured | 4:3, 10.00 × 7.50in | `IOSARBIDay3_v31_1.pptx`, 43 slides |
| `corporate_16x9` | ✅ measured | 16:9, 13.33 × 7.50in | Claude Design "Aviation Synergy PPT Template", 11 layouts |

### What each profile actually knows

`training_4x3` is measured from output: 43 production slides, budgets taken from
where Gamma's auto-fit actually shrank the type.

`corporate_16x9` is measured too, by a different method. The design bundle was
rendered in headless Chromium at 1920 × 1080, the deck-stage transform
normalised out, and every text element grown word by word until a descendant
clipped past the section's fixed bounds (`height: 1080px; overflow: hidden`).

That yields real numbers for the three things a static read of the HTML could
not give: the layout grid, the logo tokens, and the char budgets.

**Budget tracks box height, not just width.** The 6.67in slot holds only 80
chars at 14pt because it is short; the 2.71in slot holds 176. Each column entry
is the worst case observed at that width and size, floored at the longest string
the template itself ships — so anything inside budget fits every layout.

One caveat worth keeping in view: these describe the **design's** capacity, the
point at which content clips in a fixed-height template. Gamma answers the same
pressure by shrinking type rather than clipping. Re-measure against a Gamma
export if you drive generation from this profile.

### Corporate tokens at a glance

- **Fonts** — Michroma (headings + eyebrow labels), Inter (body), Georgia (quote glyph only)
- **Brand palette** (authoritative) — `#103558` Prussian Blue · `#027EA7` Cerulean ·
  `#E9E8E8` Platinum · `#FFFFFF` White · `#6E6E6E` Dim gray · `#E58F65` Atomic tangerine
- **Type ramp** — cover 31pt, section 29pt, slide title 25pt, card title 16pt,
  body 14pt, eyebrow 12pt
- **Grid** — symmetric 110px (0.764in) margins, 1700px (11.81in) content width
- **Logo** — 34 × 34px mark at 0.764, 6.938in on slides 2–9; larger brand marks
  on cover and closing
- **11 layouts** — Cover, Agenda, Section Divider, Content + Image,
  Three-Column Cards, Key Figures, Timeline, Comparison Table, Quote,
  Full-Bleed Image, Closing

Adding a profile: copy the `TRAINING_4X3` dict, replace every value with one
measured from a real source deck, register it in `PROFILES`. Never hand-tune a
number without a deck to measure it from.

## Install

```bash
pip install python-pptx
```

## 1. Lint before generating

Costs nothing and catches the shrink before you spend credits.

```bash
python lint_content.py outline.md
python lint_content.py outline.md --column half        # for 2-column decks
python lint_content.py outline.md --profile training_4x3
python lint_content.py outline.md --json               # for CI
```

Markdown roles map onto whichever ramp entry a profile defines — `##` is a
`subhead` under `training_4x3` and a `card_title` under `corporate_16x9`. The
linter prints the mapping it resolved.

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
python normalize_pptx.py deck.pptx                     # -> deck-normalized.pptx
python normalize_pptx.py deck.pptx --dry-run           # report only
python normalize_pptx.py deck.pptx --profile training_4x3
python normalize_pptx.py deck.pptx --skip snap         # opt out of a step
```

| Step | Action |
|---|---|
| `floor` | Lifts any run below 14 pt |
| `colour` | Folds drift back to the brand palette — `#103458` → `#103558`, `#0080A9` → `#027EA7` |
| `logo` | Snaps footer logo to 1.00 × 0.84in at y 6.46 — x 8.81 content, x 6.14 section dividers |
| `snap` | Corrects left-edge drift of 0.010–0.060in back onto the grid |
| `titles` | **Reports** shrunk titles (needs a text edit, so never forced) |

Idempotent: re-running a normalized file makes zero changes.

### On the current deck

```
colour   283 fixed     body copy had drifted to #103458
snap      63 fixed     drifts of 0.013–0.043in
titles     6 flagged   the six over-length titles
floor      0           already ≥ 14 pt
logo       0           already correct
```

## Canvas

The normalizer warns when the input canvas does not match the selected profile,
since grid snapping and logo placement would land in the wrong places.

## Outlines

`outlines/` holds linted source outlines ready to feed Gamma.

| File | Profile | Cards |
|---|---|---|
| `corporate_capability.md` | `corporate_16x9` | 11, one per template layout |

## Still manual

The Gamma MCP cannot edit an existing gamma or theme, so these are one-time jobs
in the Gamma editor:

- Unify the theme text colour to `#103558` Prussian Blue
- Confirm heading font **Open Sans Bold**, body **Fira Sans**
- Save a corrected deck as a **Template** — the production workspace has none,
  so `generate_from_template` is unavailable until one exists

Already done, confirmed by reading the Day 3 gamma's `page-setup`:

```
<card-dimensions>4:3</card-dimensions>
<font-size>lg</font-size>
<scale-content-to-fit>true</scale-content-to-fit>
<card-margins>
  <bottom-center type="card-numbers" />
  <bottom-right type="theme-logo" size="xl" />
```

The theme logo is already wired into `card-margins`, so it needs no upload.
`scale-content-to-fit: true` is Gamma's name for the auto-shrink behaviour this
whole toolkit exists to work around.

## Importing a Claude Design template

`mcp__Gamma__import-claude-design-from-url` imports a Claude Design bundle into
Gamma, but note two limits:

- It needs a short-lived (~10 min) **publicly fetchable** URL to the
  self-contained `.dc.html`. A `claude.ai/design/p/...?via=share` viewer link is
  auth-gated and returns 403 to the server.
- It creates a **gamma, not a theme**. Save the result as a Template in the
  editor for the layout layer; the theme layer (fonts, colours, logo) still has
  to be rebuilt by hand from the design's tokens.

Note that Claude Design's send-to-Gamma targets `labs.gamma.app`, a separate
research surface. Docs created there are invisible to the production Gamma API
(`read_gamma` on a labs id returns 404, and `get_gammas type=template` stays
empty), so a labs template cannot drive `generate_from_template`.
