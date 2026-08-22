---
name: directors-sheet
description: >
  Generate a cinematic Director's Sheet — a single-page HTML visual reference for any video production
  (music video, corporate video, documentary, short film, ad, animation). The sheet consolidates
  character references, environments, color palette, visual rules, camera/lighting specs, thematic
  motifs, and production status into one polished, printable page. Use this skill whenever the user
  mentions "director's sheet", "visual reference sheet", "production reference", "look book",
  "mood board page", "one-pager for a video project", or asks to create a visual summary for a
  film/video production. Also trigger when the user has been building a video project (characters,
  environments, scenes) and asks to "put it all together" or "make a reference page" or "create
  a visual overview". Trigger on any mention of creating a director's sheet for ANY type of video
  project — music videos, corporate videos, documentaries, short films, commercials, or animations.
---

# Director's Sheet Generator

---

## UPSTREAM / DOWNSTREAM SKILL MAP

```
UPSTREAM (receives input from — any of these):
  /video-production-planner  ── Complete production package (brief, shot list, generated images, prompts)
  /storyboard-generator      ── Character refs, environment refs, storyboard panels (Higgsfield MCP job IDs)
  /seedance2-director        ── Generated video clip job IDs + production status
  /higgsfield-creator        ── Generated video clips + Soul Cast data + Cinema Studio settings
  /music-video-producer      ── Generated clips + timing map + assembly status
  /credit-calculator         ── Cost estimates and remaining balance
  User direct                ── Project details provided in chat

THIS SKILL SERVES ALL GENERATION SKILLS (many-to-many):
  The Director's Sheet is the universal visual reference document. It consolidates
  assets from ANY upstream skill and serves as the shared reference for ANY
  generation skill currently in use:
  - /seedance2-director reads it for character locks, color palette, visual rules
  - /higgsfield-creator reads it for Soul Cast parameters, Moodboard references, Cinema Studio settings
  - /music-video-producer reads it for scene-to-lyric visual mapping, character wardrobe per section

DOWNSTREAM (its output feeds):
  All generation skills ── as described above
  User ── printable one-page reference for the production
```

### Higgsfield MCP Image Integration:

When upstream skills provide Higgsfield MCP job IDs for generated images:
- Use `job_display` tool to retrieve image URLs from job IDs
- Embed these URLs directly in the HTML Director's Sheet
- Label each image with its source (character ref, environment, storyboard panel)
- Track generation status (complete/pending/failed) in the Production Status section

---

Create a polished, single-page HTML Director's Sheet that serves as the definitive visual reference
for a video production. The sheet is designed to be opened in a browser, printed, or shared with
collaborators — everything a director, cinematographer, or AI video generation pipeline needs on
one page.

## What the Director's Sheet Contains

A Director's Sheet has up to 7 sections, arranged in a responsive CSS grid. Not every project
needs all sections — adapt based on project type. The sections are:

1. **Header** — Project title, subtitle, format specs (resolution, aspect ratio, duration), I2V platform, production status summary, date
2. **Character Reference** — Image grid with labels, physical description, wardrobe, expression range, performance notes
3. **Environments & Set Design** — Environment images, descriptions with key props, atmosphere notes
4. **Color Palette & Visual Rules** — Named color swatches with hex codes and descriptions, visual rules list, negative prompt
5. **Thematic Motifs** — Recurring symbolic imagery with names, meanings, and image references (for artistic/surreal projects, branding elements for corporate)
6. **Camera & Lighting** — Camera body, lens specs, color grade, key/fill lighting, movement style, mood keywords
7. **Production Status** — Progress bar, clip grid showing complete/pending/next status, legend, performance notes

See `references/project_types.md` (read it with the Read tool at `<this-skill-folder>/references/project_types.md`)
for which sections are relevant to each project type and what to call them.

## Workflow

### Step 1: Identify the Project Context

Check the user's project folder for existing project data. Look for:
- `project_bible.json` — structured data file (if found, most data can be extracted from here)
- `PRODUCTION_PACKAGE.md` or similar — scene breakdowns with timing and visual metaphors
- Image files (`.png`, `.jpg`, `.webp`) — potential character/environment references
- Any existing `directors_sheet.html`

If a `project_bible.json` exists, read it and confirm with the user: "I found your project bible
for [project name]. Want me to generate the Director's Sheet from this, or do you want to update
any details first?"

If no structured data exists, proceed to the interview.

### Step 2: Interview for Missing Information

Gather the information needed to populate the sheet. The goal is a conversation, not a form.
Group related questions together, adapt based on what the user has already provided, and use
the AskUserQuestion tool for choices with clear options.

Think of this like a pre-production meeting — you're the production designer asking the director
the right questions to build their visual bible.

#### Always needed:

- **Project name** and subtitle or tagline
- **Project type** — music video, corporate, documentary, short film, ad, animation, other
- **Target duration** in seconds or mm:ss
- **Aspect ratio** and **resolution** (default to 16:9 and 1920×1080 if not specified)
- **I2V / generation platform(s)** if this is an AI video project (Kling, Seedance, Runway, Sora, etc.)
- **Overall mood / tone** described in 3–5 keywords

#### Characters (if the project has on-screen talent or animated characters):

- Number of characters, their names, and roles (hero, supporting, background)
- Physical descriptions: ethnicity, age range, hair, eyes, build, skin tone
- Wardrobe and key props (what makes this character visually distinctive?)
- Expression range: what emotions does this character convey? What's their default state?
- Performance notes: how do they move, gesture, carry themselves?
- Reference images — scan the project folder first (Step 3), then ask the user to confirm
  or reassign. If no images exist, note what's needed.
- **Locked asset name** *(added 2026-07-15)* — if the production platform has a named-asset
  library (e.g. Higgsfield's Elements panel), record the exact saved name here and use it
  consistently in every downstream prompt reference (`@name`). Matching names let some
  platforms auto-attach the correct reference image without manual re-uploading.
- **State variants** *(added 2026-07-15)* — note any appearance states this character passes
  through in the project (dry/sweat-soaked, clean/injured, day-1/day-30 costume, etc.). Each
  state that needs to stay visually consistent should get its own locked reference sheet, not
  just a text description of the change — flag which states need a dedicated sheet.

#### Environments (usually 1–3 primary locations):

- Environment names and one-paragraph descriptions
- Key props and set dressing
- Atmosphere: what does this place feel like? Smell like? Sound like?
- Lighting characteristics specific to this environment
- Reference images — same scan-and-confirm approach

#### Color palette:

If the user specifies exact colors, use them. If not, derive a palette from the mood keywords,
reference images, and genre conventions. A palette has 3–5 named colors:
- A poetic, descriptive name (not "Blue" — instead "Midnight Teal" or "Burnished Amber")
- Hex code
- What this color represents in the project's visual language

Always present the derived palette to the user for confirmation before generating.

#### Visual rules:

- "Always" and "never" rules for the visual style (e.g., "the red scarf is the ONLY saturated element")
- Negative prompt — what to explicitly avoid in AI generation. **Note (added 2026-07-15):**
  if the project's video model is Seedance, scope negative prompts to the image-generation
  steps only (character/prop/location sheets) — Seedance does not reliably understand
  negation in video prompts and tends to produce the opposite of what's negated. State the
  desired positive state directly in any video-prompt "always" rule instead.
- Aesthetic references — cinematic touchstones (e.g., "Tarkovsky meets Wes Anderson")

#### Camera & Lighting:

- Camera body feel (ARRI Alexa, RED, Blackmagic, iPhone, drone, etc.)
- Lens type and default focal lengths (primes vs zooms, wide vs telephoto)
- Color grade description in plain language
- Key and fill light temperatures (warm amber, cool daylight, mixed, etc.)
- Movement style (locked tripod, handheld, steadicam, slow dolly, drone, etc.)

#### Thematic motifs (mainly for artistic or surreal projects):

- Recurring symbols, their names, and what they mean in the story
- Which reference images connect to which motifs
- For corporate/brand projects, these become "brand pillars" or "key messages" instead

#### Production status (optional):

- Total clips or scenes planned
- Which are complete, in progress, or pending
- What's in the next batch

For simpler projects, skip motifs and production status entirely. The interview should feel
proportional to the project's complexity.

### Step 3: Scan and Assign Images

After gathering text data, scan the project folder for image files:
```
*.png, *.jpg, *.jpeg, *.webp
```

Present a summary of what was found and ask the user to assign images to sections:
- **Character references** — label each (e.g., "Wide shot", "Close-up", "Profile", "Action pose")
- **Environment references** — label each (e.g., "Primary location wide", "Detail: bleeding fruit")
- **Lighting references** — images that show the lighting style
- **Motif / thematic images** — images of recurring symbols

If the user already provided assignments (in a project_bible.json or during the interview),
confirm them rather than re-asking.

All image paths in the final HTML must be relative — the sheet and images live in the same folder.

### Step 4: Derive the Color Palette and CSS Theme

From the confirmed palette, create CSS custom properties for the sheet's own chrome. The sheet's
background and UI should harmonize with the project palette — warm palette = warm dark backgrounds,
cool palette = cooler dark tones.

Required CSS variables:
```css
:root {
  /* Project palette colors */
  --color-1: #hex;  /* e.g., "Ash Grey" */
  --color-2: #hex;  /* e.g., "Deep Crimson" */
  --color-3: #hex;  /* e.g., "Warm Amber" — typically used for accents/labels */
  --color-4: #hex;  /* e.g., "Teal Blue" */

  /* Sheet chrome — derived from palette mood */
  --warm-bg: #...;     /* page background (dark) */
  --card-bg: #...;     /* section card background */
  --border: #...;      /* subtle card borders */
  --bone: #...;        /* primary text color (light) */
  --smoke: #...;       /* secondary/muted text */
  --accent: var(--color-3);  /* labels, numbers, highlights */
  --highlight: var(--color-2); /* rules borders, emphasis */
}
```

### Step 5: Generate the HTML

Read the HTML template reference: use the Read tool to load
`<this-skill-folder>/references/html_template.md`

This reference contains the complete CSS structure, HTML patterns for each section, and layout
rules. Follow it closely to produce consistent, high-quality output.

Alternatively, run the generation script if structured JSON data is available:
```bash
python <this-skill-folder>/scripts/generate_directors_sheet.py \
  --data <path-to-project-data.json> \
  --output <project-folder>/directors_sheet.html
```

**Key rendering rules:**
- CSS Grid with 3-column layout, 1px gap borders between sections
- Each section: dark card background, decorative section number (large, faded) in top-right
- Section labels: 10px uppercase, heavy letter-spacing, accent color, trailing horizontal line
- Images: `object-fit: cover`, slight d
## Manifest Integration

For a Greenlight-Local production (a `project.json`-backed project — see
the `production-manifest` skill), this skill reads the manifest as its
data source instead of asking the user to re-describe characters,
locations, props, style, or shot status.

1. Load `project.json` from the project root.
2. Characters/locations/props sections of the sheet come from
   `entities.characters`/`entities.locations`/`entities.props` — use each
   entity's `ref_images`, `notes`, and (for characters) `soul_id`/
   `element_id` directly.
3. Style/palette references come from `styles.fragments` (type `look`) and
   `styles.motion_presets`.
4. Scene/shot status for the production-status portion of the sheet comes
   from each shot's `status` field; the thumbnail shown for a shot is the
   generation with `selected: true` (there is at most one per shot).
5. **This skill is read-only with respect to the manifest** — it must never
   write to `project.json` or the folder tree. If the sheet needs
   information the manifest doesn't have, ask the user rather than
   inventing it or writing a placeholder back into the manifest.

See `production-manifest/SKILL.md` and `references/schema.md` for the full
field reference.
