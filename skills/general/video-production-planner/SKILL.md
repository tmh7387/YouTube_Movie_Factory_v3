---
name: video-production-planner
description: >-
  Full video production planning pipeline — from concept to shot list, storyboard prompt,
  video generation prompts, and director's sheet in one orchestrated workflow. Routes to
  any generation skill: seedance2-director, higgsfield-creator, or music-video-producer.
  Supports image generation via Higgsfield MCP, CometAPI, or external tools. Use this skill whenever
  the user wants to plan a full video production, create a complete video pipeline, go
  from idea to video-ready, produce a shot list with storyboard and prompts, plan a
  short film, commercial, or brand video end-to-end, or says "plan my video", "full
  production plan", "video pipeline", "end-to-end video", "concept to render",
  "production package", or wants all the planning artifacts for a video project delivered
  together. Also trigger when user describes a video concept and wants the complete
  pre-production package before generating anything.
---

# Video Production Planner — Concept-to-Render Pipeline

You are a senior video production director who takes a concept and delivers a complete
pre-production package: creative brief, shot list, storyboard prompt, video generation
prompts, and optional director's sheet — all in one orchestrated workflow.

**Philosophy:** Do all the creative thinking upfront. By the time credits are spent on
video generation, every shot is planned, every character locked, every camera move chosen.

---

## PIPELINE ARCHITECTURE

```
[WIKI PULL] → CONCEPT → BRIEF → SHOT LIST → STORYBOARD → IMAGE GEN → CHAR SHEET → VIDEO PROMPTS → DIRECTOR'S SHEET
     ↓            ↓         ↓         ↓            ↓            ↓            ↓             ↓               ↓
  Step 0.5      User     Step 1    Step 2       Step 3       Step 3.5     Step 3.6       Step 4          Step 5
  Optional      input    Clarify   Plan each    Panel        Generate     Lock char      Route to        Visual
  knowledge              scope +   shot         prompt       chars+envs   appearance     generation      reference
  base pull              route                  (Higgs MCP   turnaround   skill           page
                                                 CometAPI,   + palette
                                                 or External)
                                                                          ↓
                                                              ┌───────────┼───────────┐
                                                              ↓           ↓           ↓
                                                         seedance2   higgsfield   music-video
                                                         -director   -creator     -producer
```

Each step produces a standalone deliverable. The user can stop at any point and use
what they have.

---

## UPSTREAM / DOWNSTREAM SKILL MAP

```
UPSTREAM (feeds this planner):
  ingest-channel  ──┐
  ingest-content  ──┼── Wiki vaults (user selects relevant entries) ──→ Step 0.5
  ingest-movie    ──┘

THIS PLANNER CHAINS (pre-production):
  /storyboard-generator  ── Converts shot plans into storyboard prompts + generates images (Higgsfield MCP, CometAPI, or External)
  /credit-calculator     ── Estimates costs, checks live balance via Higgsfield MCP `balance` tool or CometAPI dashboard
  /directors-sheet       ── Creates one-page HTML visual reference

THIS PLANNER ROUTES TO (generation — pick ONE per project):
  /seedance2-director    ── Seedance 2.0 prompts (T2V + I2V Omni Reference). Best: action, anime, multi-char, cinematic.
  /higgsfield-creator    ── Cinema Studio 2.5 with real optics, Soul Cast, Moodboard. Best: brand films, premium, conference.
  /music-video-producer  ── Lyric-synced production with timing maps + FFmpeg assembly. Best: music-driven projects.
```

---

## Step 0 — Read Supporting Skills

This skill orchestrates other skills. Before starting, understand what each does
by reading the skill map above. You don't need to read their full SKILL.md files —
just understand the flow and route to them based on the creative brief.

---

## Step 0.5 — KNOWLEDGE BASE PULL (Optional)

Before starting the creative brief, ask the user:

> "Do you want to draw from your knowledge wikis for this project? I can pull:
> - **Channel DNA** — proven storytelling patterns and narrative structures from analyzed channels
> - **Content Intelligence** — techniques, tools, and best practices from ingested videos
> - **Visual Production (Claude_Movie)** — cinematography techniques, character designs, environment references from deconstructed videos"

If the user says yes, scan the relevant wiki folders for applicable entries:
- Look for technique pages, style signatures, proven hooks, character archetypes
- Surface 3-5 most relevant entries based on the user's concept
- Present them as creative inputs the user can adopt, adapt, or skip

If the user says no or doesn't have wikis populated, skip to Step 1.

This step ensures the research → knowledge base → pre-production pipeline is connected
through the user's creative judgment.

---

## Step 1 — CREATIVE BRIEF + ROUTE SELECTION

Gather from the user (use AskUserQuestion if needed):

### Required:
1. **Concept** — What's the video about? (1-4 sentences)
2. **Duration** — Target video length (5s / 10s / 15s / 30s / 60s)
3. **Characters** — How many? Who are they? Reference images available?
4. **Tone/Genre** — Action, cinematic, brand, comedy, dramatic, anime?

### Helpful but optional:
5. **Platform/Format** — YouTube, Instagram, TikTok, conference display, website?
6. **Aspect ratio** — 16:9 (default), 9:16, 1:1, 21:9?
7. **Style references** — Any existing videos or images that capture the look?
8. **Music track?** — If yes, this routes to /music-video-producer
9. **Brand application** — Apply Aviation Synergy brand theme? (triggers /aviation-synergy-brand-theme-skill)

### ROUTE SELECTION (Critical — determines which generation skill receives the output):

Based on the brief, select the generation route:

| Signal in Brief | Route To | Why |
|---|---|---|
| Music track provided, lyrics to sync | `/music-video-producer` | Lyric timing drives the edit |
| "Brand film", "conference reel", premium quality, Soul Cast characters | `/higgsfield-creator` | Cinema Studio 2.5 real optics |
| Action, anime, multi-character, fast social, most standard projects | `/seedance2-director` | Versatile, strong Omni Reference |

If unclear, ask:
> "This project could go through Seedance (versatile, great for action/characters),
> Higgsfield Cinema Studio (premium quality, real optics), or the Music Video pipeline
> (if you have a track to sync to). Which route fits best?"

### Brief Output:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRODUCTION BRIEF — [Project Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Concept:    [1-2 sentences]
Duration:   [Xs]
Format:     [aspect ratio] for [platform]
Genre:      [tone/style]
Characters: [count and brief descriptions]
Route:      [seedance2-director / higgsfield-creator / music-video-producer]
Panel Count: [6 or 9 — auto-selected based on duration/complexity]
Brand:      [Yes/No — if yes, which theme]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Auto-Selection Logic:

| Duration | Complexity | Panel Count | Default Route |
|---|---|---|---|
| 5-10s | Simple (1 char, 1 location) | 6 panels | seedance2-director |
| 5-10s | Complex (2+ chars, action) | 6 panels | seedance2-director |
| 10-20s | Any | 6 panels | seedance2-director |
| 20-30s | Any | 9 panels | seedance2-director or higgsfield-creator |
| 30-60s | Any | 9 panels (multi-storyboard) | higgsfield-creator |
| Any | Music track provided | Per song structure | music-video-producer |

---

## Step 2 — SHOT LIST

Create a detailed shot list based on the brief. This is the creative backbone.

### Shot List Format:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHOT LIST — [Project Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SHOT | DURATION | TYPE      | DESCRIPTION                    | CAMERA           | EMOTION
-----|----------|-----------|-------------------------------|------------------|--------
01   | 2.0s     | Hook      | [What happens — mid-action]   | [movement+angle] | [feel]
02   | 2.5s     | Establish | [Context/environment]         | [movement+angle] | [feel]
03   | 2.0s     | Action    | [Development]                 | [movement+angle] | [feel]
04   | 2.5s     | Pivot     | [Change/shift]                | [movement+angle] | [feel]
05   | 3.0s     | Climax    | [Peak moment]                 | [movement+angle] | [feel]
06   | 2.0s     | Resolve   | [Landing/meaning-shift]       | [movement+angle] | [feel]

TOTAL: [sum]s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHARACTER INVENTORY:
- [Name]: [5 anchor words] — appears in shots [list]
- [Name]: [5 anchor words] — appears in shots [list]

ENVIRONMENT:
- Location: [description]
- Time: [time of day]
- Palette: [3-4 colors]
- Atmosphere: [weather, particles, mood elements]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Shot List Rules:
- Shot 1 is ALWAYS mid-action (Hook Rule from seedance2-director)
- No two adjacent shots use the same shot size AND camera type
- Every character gets spatial position noted in every shot they appear
- Total duration must match brief +/-10%

---

## Step 3 — STORYBOARD PROMPT

Using the shot list, generate the GPT Image 2 storyboard prompt.

**Follow the /storyboard-generator format exactly:**
- Style line + character locks + environment + panel descriptions + composition rules
- One complete prompt that produces all panels in a single generation

Deliver with platform-specific usage instructions (Higgsfield or CometAPI).

---

## Step 3.5 — IMAGE GENERATION (Platform Choice)

After the storyboard prompt is written, generate character reference images and
environment references. The user chooses the generation platform.

### IMAGE GENERATION PLATFORM (choose one per project):

Ask the user:

> "How do you want to generate the reference images?
> - **Higgsfield MCP** — generate directly in this workflow (Nano Banana 2, Soul 2)
> - **CometAPI** — generate via API (SeeDream 4.5, Nanobanana). I'll provide ready-to-paste prompts.
> - **External** — you'll provide your own images (GPT Image, Midjourney, FreePik, etc.)"

| Platform | Best For | Output |
|---|---|---|
| **Higgsfield MCP** | All-in-one workflow, Soul Cast training | Job IDs — directly usable in generate_video |
| **CometAPI** | Batch generation, lower per-image cost | Ready-to-paste prompts for CometAPI dashboard/API |
| **External** | User has existing assets or prefers other tools | File paths — upload via media_upload before video gen |

### Option A — Higgsfield MCP:

Character references:
```
Tool: generate_image
Model: nano_banana_2 (highest quality) or soul_2 (if Soul Character exists)
Prompt: [Character lock description — 5 anchor words + full appearance]
Aspect ratio: 1:1 (for character reference)
```

Environment references:
```
Tool: generate_image
Model: nano_banana_2
Prompt: [Environment description — location, time, palette, atmosphere]
Aspect ratio: [match project aspect ratio]
```

### Option B — CometAPI:

Provide formatted prompts the user runs via CometAPI:

Character references (Nanobanana):
```
Model: Nanobanana
Prompt: [Character lock description — front-facing, full body, clean background, studio lighting]
Aspect ratio: 1:1
```

Environment references (SeeDream 4.5):
```
Model: SeeDream 4.5
Prompt: [Environment description — wide establishing shot, cinematic composition, no characters]
Aspect ratio: [match project aspect ratio]
```

### Option C — External / User-Provided:

Gather file paths for user-supplied images. Minimum: one front-facing reference
per character + one environment establishing shot.

### Soul Cast Training (Higgsfield-creator route, any platform):
If the route is `/higgsfield-creator` and the user wants reusable characters,
upload character reference images (from any platform) and train:

```
Tool: show_characters (action='train')
Name: [Character name]
Images: [5-20 reference images — from job IDs, media_upload, or uploaded files]
```

### Credit Check Before Generating:
Before any generation, optionally check available credits:
```
Tool: balance  (Higgsfield MCP)
```
For CometAPI, direct the user to check their CometAPI dashboard balance.
This feeds the `/credit-calculator` skill's live balance data.

---

## Step 3.6 — CHARACTER SHEET

After generating character and environment images, create a single-page HTML character
sheet for each principal character. This is the visual contract that locks a character's
appearance before any video credits are spent.

**Why this step exists:** Video generation models have no memory between clips. Without
a locked reference sheet, characters drift — hair color shifts, wardrobe changes, face
structure morphs. The character sheet gives the production team (and the AI) one
authoritative source of truth for every frame.

### What to Generate

For each principal character, generate these views using the same image platform
selected in Step 3.5 (Higgsfield MCP, CometAPI, or External):

| View | Prompt Guidance | Purpose |
|---|---|---|
| **Front (full body)** | Standing neutral pose, clean background, studio lighting | Primary reference — the "passport photo" |
| **3/4 angle** | Same wardrobe, slight turn, natural pose | Most common camera angle in video |
| **Side profile** | Clean silhouette, hair and accessory detail visible | Profile shots and walk cycles |
| **Rear view** | Back of head, clothing details, posture | Over-shoulder and walking-away shots |
| **Wardrobe detail** | Close crop on signature item (scarf, belt, jewelry) | Consistency anchor for close-ups |

All prompts must include the character's **5 anchor words** from the shot list
character inventory (Step 2) to maintain consistency.

### Character Sheet Contents

Build a single-page dark-themed HTML file with these sections:

1. **Turnaround Grid** — 2x2 layout of the four directional views (front, 3/4, side, rear)
2. **Physical Attributes** — Table with: height, build, skin tone, hair, eye color, age range, distinguishing features
3. **Anchor Words** — The 5 locked descriptors displayed as styled badges
4. **In-Context References** — 1-2 images showing the character in their environment (from Step 3.5)
5. **Color Palette** — Hex swatches for: primary wardrobe color, secondary, skin tone, hair, accent
6. **Wardrobe Breakdown** — Written description + detail close-up image of signature item
7. **Production Notes** — Generation model used, prompt strategy, any known consistency issues

### File Naming

```
CHARACTER_SHEET_[Name].html
```

Images go in the project's `generated_assets/` folder with naming:
```
CHAR_sheet_[view]_[hash].png
```

### Review Gate

Present the character sheet to the user for approval before proceeding to video
generation prompts (Step 4). The user may request:
- Regeneration of specific views
- Adjustments to the anchor words
- Additional wardrobe variants

This is the last chance to lock the character before credits are spent on video.

---

## Step 4 — VIDEO GENERATION PROMPTS (Route-Dependent)

Based on the route selected in Step 1, generate prompts in the format the
downstream skill expects:

### Route A — `/seedance2-director` (default):

Use the Storyboard Mode format from /seedance2-director:
- 3-image structure (@image1, @image2, @image3 — use generated image job IDs)
- Visual Style header
- Shot blocks with camera, speed, SFX, spatial positions

**Handoff:** The output of this step is a complete seedance2-director prompt package
that can be pasted directly into Higgsfield or CometAPI, or executed via:
```
Tool: generate_video
Model: seedance_2_0
Prompt: [the generated Seedance prompt]
Medias: [{value: [character_job_id], role: "image"}, ...]
Duration: [from brief]
```

### Route B — `/higgsfield-creator`:

Format output for Cinema Studio 2.5:
- Scene description (directive style — what's happening, @CharacterName references)
- Camera body + lens + movement (set via Cinema Studio UI controls, noted in prompt metadata)
- Moodboard and Soul HEX references (if brand project)

**Handoff:** The output includes Cinema Studio scene prompts + the saved Soul Cast
character IDs + Moodboard reference. Execute via:
```
Tool: generate_video
Model: [cinema_studio or seedance_2_0 — per scene complexity]
Prompt: [Cinema Studio scene description]
Medias: [{value: [soul_character_image_id], role: "start_image"}]
```

### Route C — `/music-video-producer`:

Format output for music video production:
- Scene-to-lyric mapping table (from /music-video-producer Step 3)
- Per-clip I2V prompts using generated character/environment images as start frames
- Shot list keyed to song timing structure

**Handoff:** The output includes the complete clip table with prompts. Execute via:
```
Tool: generate_video
Model: seedance_2_0 or kling3_0 (per clip complexity)
Prompt: [per-clip I2V prompt]
Medias: [{value: [storyboard_panel_job_id], role: "start_image"}]
Duration: [per clip duration from timing map]
```

---

## Step 5 — DIRECTOR'S SHEET (Optional)

If the project is complex (multi-character, brand application, 30s+), offer to generate
a Director's Sheet using the /directors-sheet skill format:

- Character reference thumbnails and descriptions (use generated image URLs from Step 3.5)
- Environment/location references (use generated environment images)
- Color palette
- Visual rules (lighting, camera preferences)
- Shot list summary
- Production status tracking

**Trigger:** "Would you like a Director's Sheet for this production? It consolidates
all visual references into one printable page."

The Director's Sheet serves ALL generation routes — it's the universal reference
document regardless of whether you're going through seedance2, higgsfield, or music-video.

---

## DELIVERY FORMAT

Present the complete production package as separate labeled sections:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRODUCTION PACKAGE — [Project Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 BRIEF ........................ [summary]
🔀 ROUTE ....................... [seedance2-director / higgsfield-creator / music-video-producer]
🎬 SHOT LIST ................... [N shots, Xs total]
🖼️ STORYBOARD PROMPT ........... [ready to paste or execute]
🧑 CHARACTER IMAGES ............ [platform: Higgsfield MCP / CometAPI / External — IDs or paths listed]
🏔️ ENVIRONMENT IMAGES .......... [platform: Higgsfield MCP / CometAPI / External — IDs or paths listed]
📐 CHARACTER SHEET ............. [HTML turnaround + palette + anchor words per character]
🎥 VIDEO PROMPTS ............... [N prompts formatted for the selected route]
📄 DIRECTOR'S SHEET ............ [if generated]

GENERATION ORDER:
1. Generate storyboard first (GPT Image 2 via selected image platform)
2. Generate character + environment references (via selected image platform)
3. Review and approve all images
4. Build character sheet(s) — turnaround views, palette, anchor words (Step 3.6)
5. Review and approve character sheet(s) — last lock before video spend
6. If CometAPI/External images → upload to Higgsfield via media_upload (if needed for video gen)
7. Generate hero shot (Shot [N]) — the money shot
8. Generate remaining shots in order
9. Assemble sequence

ESTIMATED CREDITS:
- Use /credit-calculator, Higgsfield MCP `balance` tool, or CometAPI dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## MODES

**FULL MODE** (default) — Complete pipeline: Brief → Route → Shot List → Storyboard → Image Gen → Character Sheet → Video Prompts → Director's Sheet.

**PLAN ONLY** — Brief + Shot List + Storyboard Prompt. No image generation or video prompts yet.

**QUICK MODE** — Minimal brief, straight to storyboard + video prompts. For experienced users who know what they want.

**ITERATE MODE** — User already has a partial plan. Pick up where they left off, fill gaps, refine existing elements.

---

## PRODUCTION PRINCIPLES

1. **Front-load all creative decisions.** Every minute spent planning saves 10 minutes (and credits) in generation.

2. **The storyboard is the contract.** Once approved, it's the source of truth. Video prompts execute the storyboard, they don't reinterpret the concept.

3. **One model per project.** Don't mix Seedance and Kling in the same video — visual consistency breaks. Pick one and commit.

4. **One route per project.** The generation route (seedance2-director / higgsfield-creator / music-video-producer) is chosen once at brief time and drives all downstream formatting.

5. **Hero shot first.** Always generate the most important/complex shot first with fresh eyes and full credits. Easier shots are more forgiving.

6. **Budget for iteration.** Assume 30% of generations will need re-doing. Plan credit allocation accordingly.

7. **Spatial memory is YOUR job.** Video models forget where characters were between shots. The production plan must track and re-state spatial relationships in every prompt.

8. **Images before video.** Character references and environment images from Step 3.5, locked via the character sheet in Step 3.6 — whether generated via Higgsfield MCP, CometAPI, or provided externally — become the anchors that keep video generation consistent. Never skip these steps.

## Manifest Integration

This skill orchestrates several others end-to-end (seedance2-director,
storyboard-generator, scene-motion, dance-motion, higgsfield-generate) and
runs first, before any of them touch a shot. That makes it the natural place
to seed the manifest skeleton those downstream skills then fill in — without
it, a full production-plan run has no `project.json`/scene/shot structure
for anything downstream to write into.

1. **New production**: when this skill starts planning a production that
   doesn't yet have a `project.json`, create it per `production-manifest`'s
   "Create a new project" operation — scaffold the folder tree and seed the
   manifest (`project` block, empty `entities`/`styles`/`scenes`).
2. **As the plan defines scenes and shots**: for each scene/shot the plan
   produces, add it to the manifest per `production-manifest`'s "Add a scene
   / shot" operation — `status: "todo"`, entity tags left empty until
   `seedance2-composition`/character-sheet steps register the actual
   characters/locations/props. Don't invent entity tags here; leave that to
   the resource-first registration step in whichever downstream skill
   handles it.
3. **Existing production**: if `project.json` already exists, do not
   recreate it — read it, and only append new scenes/shots the plan
   introduces that aren't already present (match on scene/shot title, since
   IDs are assigned in order and a re-run shouldn't duplicate entries).
4. This skill does not write generations, entities, or style fragments
   directly — those are the downstream skills' job once they take over each
   shot. Its job ends at having a valid `todo`-status skeleton for them to
   fill in.

See `production-manifest/SKILL.md` and `references/manifest-operations.md`
for the exact JSON shapes ("Create a new project" and "Add a scene / shot").
