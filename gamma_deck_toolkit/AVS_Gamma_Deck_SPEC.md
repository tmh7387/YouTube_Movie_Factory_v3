# Aviation Synergy — Gamma Deck Production Spec
Measured from `IOSARBIDay3_v31_1.pptx` (43 slides, production-corrected).
Gamma theme: **Aviation Synergy 2024** (`6k7l8ert7ql57ok`)

---

## 1. Canvas

| Property | Value | Gamma param |
|---|---|---|
| Slide size | 10.00 × 7.50 in (**4:3**) | `cardOptions.dimensions: "4x3"` |
| Left margin | 0.54 in | — |
| Content width | 8.91 in | — |
| Right margin | 0.55 in | — |
| Inset content | 0.71 – 0.81 in | — |

> ⚠ 4:3 confirmed. If presenting on 16:9, switch to `"16x9"` (13.33 × 7.5 in) and re-derive widths.

## 2. Colour

| Token | Hex | Notes |
|---|---|---|
| Brand navy | `#103458` | 283 runs — **canonical** |
| Navy (stray) | `#103558` | 65 runs — **bug, unify to #103458** |
| Accent blue | `#1A6496` | 1 run |
| Reverse text | `#FFFFFF` | 14 runs (on navy fills) |

## 3. Type ramp

| Role | Size | Font | Char budget |
|---|---|---|---|
| Slide title | **34.5 pt** | Open Sans Bold | **≤ 36** (hard limit) |
| Hero title | 40 pt | Open Sans Bold | ≤ 25 |
| Agenda item | 24 pt | Open Sans Bold | ≤ 30 |
| Lead-in | 20 pt | Fira Sans | ≤ 60 |
| Section subhead | 16.5 – 17 pt | Open Sans Bold | ≤ 27 |
| Body | 14 – 16 pt | Fira Sans | see §5 |
| Table cell | 14 pt | Fira Sans / Bold | ≤ 25 |
| **Floor** | **14 pt** | — | never go below |

### Title shrink rule (measured)
Titles ≤ 36 chars held 34.5 pt on **36 of 36** slides.
All 6 failures were ≥ 37 chars in a box < 1.21 in tall:

| Slide | Chars | Box h | Fell to |
|---|---|---|---|
| 2 | 38 | 0.57 | 30.0 pt |
| 6 | 42 | 0.51 | 29.5 pt |
| 8 | 40 | 1.15 | 33.0 pt |
| 27 | 42 | 1.09 | 31.0 pt |
| 35 | 37 | 1.15 | 33.0 pt |
| 42 | 44 | 0.93 | 28.0 pt |

**Rule: keep every title ≤ 36 characters.**

## 4. Layout archetypes

**A — Section divider** (9 slides)
- Portrait image right: `[7.56, 2.02] 2.31 × 3.47`
- Title left: `[0.54] w 6.60`, 34.5 pt
- Body: 16 – 18 pt
- Logo: `[6.14, 6.46]`

**B — Square image + text column** (9 slides)
- Title full width: `[0.54] w 8.91`
- Square image left: `[0.54–0.61, 2.71–3.02] ~2.7 × 2.7`
- Text column: `x 3.83, w 5.63`
- Subheads 16.5–17 pt, body 14 pt

**C — Two equal columns** (2 slides)
- Columns at `x 0.54` and `x 5.24`, each `w 4.22` (0.48 in gutter)

**D — Four-column table** (1 slide)
- Columns at `x 0.71 / 2.05 / 4.28 / 6.95`, all 14 pt

**E — Agenda list** (1 slide)
- Item head 24 pt + descriptor 15 pt, `x 0.81, w 8.61`

## 5. Body line budgets (p90 from production deck)

| Column width | Size | Avg | p90 | Max |
|---|---|---|---|---|
| 5.63 in | 14 pt | 70 | **86** | 132 |
| 5.63 in | 16 pt | 78 | **110** | 137 |
| 4.22 in | 14 pt | 70 | **83** | 83 |
| 4.22 in | 16 pt | 57 | **63** | 63 |
| 4.00 in | 16 pt | 41 | **70** | 77 |
| 8.61 in | 15 pt | 71 | **92** | 92 |

Use p90 as the lint threshold.

## 6. Logo

| Context | Position | Size | Count |
|---|---|---|---|
| Content slides | `[8.81, 6.46]` | 1.00 × 0.84 | 34 |
| Section dividers | `[6.14, 6.46]` | 1.00 × 0.84 | 9 |

Baseline `y = 6.46` in on all 43 slides.
→ `cardOptions.headerFooter.bottomRight = { type: "image", source: "themeLogo", size: "sm" }`, `hideFromFirstCard: true`

## 7. Locked generation profile

```json
{
  "themeId": "6k7l8ert7ql57ok",
  "textMode": "preserve",
  "cardSplit": "inputTextBreaks",
  "cardOptions": {
    "dimensions": "4x3",
    "headerFooter": {
      "bottomRight": { "type": "image", "source": "themeLogo", "size": "sm" },
      "hideFromFirstCard": true
    }
  },
  "textOptions": { "amount": "brief", "language": "en-gb", "tone": "professional" },
  "imageOptions": { "source": "themeAccent" }
}
```

`textMode: "preserve"` is the critical setting — it stops Gamma expanding the outline
into prose, which is the direct cause of box overflow and auto-shrink.

## 8. Theme checklist (manual — Gamma editor)

Themes → Aviation Synergy 2024 → Edit:

- [ ] Heading font → **Open Sans Bold**
- [ ] Body font → **Fira Sans**
- [ ] Primary text colour → **#103458** (remove the #103558 variant)
- [ ] Accent → #1A6496
- [ ] Upload AVS logo as **theme logo** (enables headerFooter auto-placement)
- [ ] Raise base font scale so body lands at 14–16 pt equivalent
- [ ] Save corrected Day 3 deck as a **Template** → unlocks `generate_from_template`

## 9. Known limits

- The Gamma MCP **cannot edit** an existing gamma or theme — §8 is manual, one time.
- No theme setting forces a per-card font size; auto-fit always wins.
  Control **content volume**, not type size.
- Workspace currently has **0 templates**.
