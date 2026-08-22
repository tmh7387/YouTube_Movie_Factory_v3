---
name: scene-motion
description: >-
  Story scene video pipeline — character reference + scene concept to
  Seedance video in six steps: character sheet, environment reference,
  scene beat sheet, prompt authoring, media upload, generation. One shot
  at a time. Each shot = one beat sheet = 8-12 panels, typically 8-15
  seconds on Seedance 2.0 and up to 30 on 2.5.
  Trigger on "scene motion", "story scene", "scene video", "narrative
  clip", "scene beat sheet", "animate this scene", "story video pipeline",
  "scene workflow", or any character + narrative scene video request.
  Also trigger on [location] + [action] patterns like "record store scene",
  "cafe scene", "walking scene", "discovery scene". Trigger when user
  uploads a character image with a Director's Sheet or storyboard for
  scene-based video. Chains with seedance2-director, seedance2-composition,
  and higgsfield-generate for final generation.
---

# Scene Motion — Full Pipeline Skill

Produces a narrative scene video clip from a character reference image
and scene concept in six sequential steps. Each step produces a
deliverable the user reviews before proceeding. Never skip steps or
auto-advance without user confirmation.

**Core difference from dance-motion:** In dance-motion, the environment
is a neutral backdrop and @image2 is body mechanics only. In scene-motion,
the environment is a co-star — every beat sheet panel shows the character
IN the set with correct lighting, props, and spatial context. This gives
Seedance both body mechanics AND environment ground truth simultaneously.

## Prerequisites

- One uploaded character reference image (photo, 3D, anime, painterly)
- A scene concept: location + action + emotional arc
- Higgsfield MCP connection active (for Steps 5–6)
- Optionally: a Director's Sheet or storyboard for reference

## Pipeline Overview

```
INPUT: Character reference image + Scene concept
  │
  ├─ Step 1 → Character Sheet (6-panel identity reference)
  ├─ Step 2 → Environment Reference Sheet (multi-angle, no character)
  ├─ Step 3 → Scene Beat Sheet (8-12 panels, character IN environment)
  ├─ Step 4 → Seedance 2.0 Prompt (Prompt A + Prompt B)
  ├─ Step 5 → Media Upload to Higgsfield
  └─ Step 6 → Seedance 2.0 Video Generation
  │
OUTPUT: one scene video clip (16:9 @ 720p default). Length follows the
        beat sheet — commonly 8-15s, up to 30s on Seedance 2.5.
```

**One shot = one full pipeline pass.** For a multi-shot scene (e.g., a
4-shot record store story), run the pipeline once per shot. Steps 1-2
are reusable across all shots in the same scene — only Steps 3-6 repeat.

---

## UPSTREAM / DOWNSTREAM SKILL MAP

```
UPSTREAM (receives input from — any of these):
  /video-production-planner  ── Creative brief + shot list
  /storyboard-generator      ── Storyboard panels + character refs
  /directors-sheet            ── Visual reference page with all assets
  User direct                 ── Scene concept described in chat

THIS SKILL PRODUCES:
  1. Character sheet (reusable across shots)
  2. Environment reference sheet (reusable across shots in same location)
  3. Scene beat sheet (per shot)
  4. Paste-ready Seedance 2.0 prompts
  5. Generated video clips

DOWNSTREAM:
  /directors-sheet   ── Generated clips + production status updates
  /credit-calculator ── Clip count and model for cost estimation
```

---

## Step 1 — Character Sheet Creation

**Goal:** Produce a 6-panel character reference sheet that locks identity
across all angles.

**When to run:** First shot in a scene. Skip if user already has an
approved character sheet from a previous session.

**Action:** Generate an image using the character sheet prompt.

Read `references/character-sheet-prompt.md` for the exact prompt text.

**Generation method:** Use Higgsfield MCP `generate_image` tool:
- Model: `gpt_image_2`
- Prompt: the full character sheet prompt from the reference file
- Media: attach the user's uploaded reference image with role `image`
- Aspect ratio: `16:9`

**Delivery:** Present the generated character sheet to the user.
Ask: *"Does this character sheet look accurate? Should I adjust
anything before we move to the environment reference?"*

**Do NOT proceed to Step 2 until the user confirms.**

**If the user already has a character sheet:** Accept it, note the
source (uploaded file, previous job ID, or external), and skip to Step 2.

---

## Step 2 — Environment Reference Sheet

**Goal:** Produce a multi-angle environment reference image showing the
location WITHOUT any characters. This gives Seedance a visual ground
truth for the set design, lighting, color palette, and spatial layout.

**When to run:** First shot in a new location. Skip if user already has
an approved environment reference for this location, or if the location
hasn't changed from the previous shot.

**Action:** Two sub-steps:

### Step 2a — Environment Brief

Extract or ask for these details:
- **Location type:** Interior/exterior, era, style
- **Key set pieces:** 3-5 defining physical elements (e.g., "tall
  honey-oak vinyl shelves, waist-high record bins with white category
  tabs, wall grid of framed album covers")
- **Lighting:** Direction, quality, color temperature, practical sources
- **Color palette:** 3-4 dominant colors
- **Atmosphere:** Dust, fog, rain, time of day, mood
- **Era/period details:** If the scene is set in a specific decade

Present the brief to the user for confirmation.

### Step 2b — Generate the Environment Reference

Read `references/environment-reference-prompt.md` for the prompt template.

The environment sheet shows **4 angles of the same location:**

```
┌─────────────────┬─────────────────┐
│  WIDE MASTER    │  DETAIL ANGLE   │
│  (establishing) │  (key set piece)│
├─────────────────┼─────────────────┤
│  CHARACTER POV  │  ATMOSPHERE     │
│  (what they see)│  (mood/light)   │
└─────────────────┴─────────────────┘
```

**Generation method:** Use Higgsfield MCP `generate_image` tool:
- Model: `gpt_image_2`
- Prompt: the environment reference prompt with the approved brief
- Media: if user has an existing environment image (from a Director's
  Sheet or storyboard), attach with role `image` for style matching
- Aspect ratio: `16:9`

**Delivery:** Present the environment reference to the user.
Ask: *"Does the environment look right — lighting, set pieces, color
palette, atmosphere? Ready to build the beat sheet?"*

**Do NOT proceed to Step 3 until the user confirms.**

---

## Step 3 — Scene Beat Sheet

**Goal:** Produce an 8-12 panel beat sheet showing the character
performing the key physical moments of THIS SHOT, inside the approved
environment. This is the visual vocabulary for Seedance — it sees
every body position, every prop interaction, every emotional state
the character will hit, all within the correct set.

**When to run:** Every shot. This is the per-shot deliverable.

**Action:** Two sub-steps:

### Step 3a — Outline the Beats

Write an 8-12 beat outline for this specific shot. Each beat is a
distinct physical moment — a change in action, emotion, body position,
or prop interaction.

Read `references/scene-beat-prompt.md` for the prompt template and
rules.

**Rules for the outline:**
- 8-12 panels, numbered sequentially
- Each panel: a named beat with full body position, emotion, prop
  state, and environment interaction
- Include camera framing note per panel (matches the shot's camera plan)
- Beats must be physically connected — each position flows from the
  previous one
- First panel: character already in motion (hook rule applies)
- Last panel: clear end-state that sets up the next shot (or resolves)
- Build the emotional arc: setup → shift → peak → land
- Every panel shows FULL BODY in the environment (not cropped)
- Environment lighting and set pieces remain consistent across all panels

**Beat types available:**
- **ACTION** — character moves, walks, reaches, opens, picks up, puts down
- **REACTION** — expression changes, body language shifts, double-take
- **INTERACTION** — touches a prop, hands something over, holds object
- **TRANSITION** — enters/exits frame, turns a corner, passes through door
- **HOLD** — freeze moment, sustained emotion, contemplation pause

Present the outline to the user for approval. Adjust if requested.

### Step 3b — Generate the Scene Beat Sheet

Once the outline is approved, generate the beat sheet image.

**Generation method:** Use Higgsfield MCP `generate_image` tool:
- Model: `gpt_image_2`
- Prompt: combine the approved outline with the scene beat prompt
  template from `references/scene-beat-prompt.md`
- Media: attach TWO reference images:
  - The Step 1 character sheet (job ID) with role `image`
  - The Step 2 environment reference (job ID) with role `image`
- Aspect ratio: `16:9` (landscape for grid layout)

**Delivery:** Present the generated scene beat sheet.
Ask: *"Does the beat sheet look right? Is the character consistent?
Is the environment matching? Are all beats clear and readable? Ready
to write the Seedance prompt?"*

**Do NOT proceed to Step 4 until the user confirms.**

---

## Step 4 — Seedance 2.0 Prompt Authoring

**Goal:** Write a complete Seedance 2.0 prompt set (Prompt A + Prompt B)
with Director's Note, following the scene-motion prompt framework.

**When to run:** User confirms Step 3 beat sheet is approved.

**Action:** Read `references/seedance-scene-prompt-framework.md` for
the complete prompt structure and rules.

### Key Differences from Dance-Motion Prompts

| Dance-Motion | Scene-Motion |
|---|---|
| 16 SHOT blocks (rapid positions) | 8-12 SHOT blocks (fewer, richer beats) |
| @image2 = body mechanics only | @image2 = beat sheet (body + environment) |
| @image3 not used | @image3 = environment reference sheet |
| Neutral background in prompt | Environment described in detail per beat |
| Speed/rhythm vocabulary | Emotion/camera/atmosphere vocabulary |
| Music BPM drives pacing | Story arc drives pacing |
| Smart Cuts ON (16 rapid cuts) | Smart Cuts ON or OFF (depends on shot complexity) |

### Prompt Construction Rules

1. **Detect the scene type** from the beat sheet. State it at the top.

   | Scene contains... | Type | Camera signature |
   |---|---|---|
   | Walking, browsing, exploring | **Traversal** | Tracking, lateral, dolly |
   | Finding, discovering, revealing | **Discovery** | Push-in, rack focus |
   | Talking, confronting | **Dialogue** | OTS, axis cross |
   | Buying, exchanging, handing | **Transaction** | Medium static, insert cuts |
   | Entering, exiting, arriving | **Transition** | Pull-out, crane, wide-to-tight |
   | Waiting, thinking, feeling | **Contemplation** | Static lock, slow push-in |

2. **Three image references in the prompt:**
   - `@image1` — Character sheet (identity lock)
   - `@image2` — Scene beat sheet (body mechanics + environment + props)
   - `@image3` — Environment reference sheet (set design ground truth)

3. **Analyze @image1:** Write the full physical description exactly as
   seen. 5 anchor words. This is the identity lock.

4. **Analyze @image2:** Reference it as body mechanics AND environment
   reference. Describe what the panels show — the character performing
   specific actions within the set.

5. **Analyze @image3:** Reference it as environment ground truth. The
   set design, lighting, color palette, and atmosphere shown in the
   environment reference must be maintained throughout.

6. **Write all SHOT blocks** following the scene-motion rules:
   - Every shot starts with `@image1 [action]`
   - Never write "She", "He", or "the character"
   - Shot 1 is always a HOOK — mid-action, never neutral
   - Include environment details every 2-3 shots (set pieces, lighting,
     atmosphere elements)
   - Include one visible character detail every 3-4 shots
   - Camera uses exact Seedance native syntax only
   - SFX on every shot — name every sound precisely
   - Emotion described as physics ("jaw clenches" not "looks angry")
   - Props described with physical state ("album held at chest height,
     glossy surface catching amber overhead light")

7. **Write the Director's Note** with all seven fields:
   - SCENE TYPE DETECTED
   - SIGNATURE MOMENT
   - GENERATE FIRST
   - WHAT TO WATCH FOR
   - IF IT FAILS
   - ENVIRONMENT RISK (specific to this set — what might drift)
   - SEEDANCE TIP

### Output Format

Always output in this exact order:
```
── PROMPT A ──
[full text]

── PROMPT B ──
[full text with all SHOT blocks]

── DIRECTOR'S NOTE ──
[all seven fields]
```

**Delivery:** Present the complete prompt set to the user.
Ask: *"Prompt set is ready. Want me to proceed with upload and
generation?"*

**Do NOT proceed to Step 5 until the user confirms.**

---

## Step 5 — Media Upload to Higgsfield

**Goal:** Upload all three reference images (character sheet + environment
reference + scene beat sheet) to Higgsfield and confirm them.

**When to run:** User confirms Step 4 prompt is approved.

**Action:**

1. Call `Higgs:media_upload` with all three images (if not already
   uploaded from Higgsfield MCP generation — use job IDs directly):
   - `character_sheet` (from Step 1)
   - `environment_reference` (from Step 2)
   - `scene_beat_sheet` (from Step 3)

2. Upload each file using the returned presigned URLs via `curl`.

3. Call `Higgs:media_confirm` with all media IDs, type `image`.

4. Store all confirmed media IDs for Step 6.

**Note on job IDs:** If images were generated via Higgsfield MCP in
Steps 1-3, use the job IDs directly as media references in Step 6
(no re-upload needed).

**This step auto-advances to Step 6 — no user confirmation needed.**

---

## Step 6 — Seedance 2.0 Video Generation

**Goal:** Submit the generation job to Seedance 2.0 and deliver the
rendered video clip.

**When to run:** Step 5 upload is confirmed.

**Action:**

Call `Higgs:generate_video` with these parameters:
```json
{
  "model": "<seedance_2_0 or seedance_2_5 — ask which the user is on>",
  "aspect_ratio": "16:9",
  "duration": [whole seconds, from the beat sheet. 8-15 is the usual range
               and 8-10 the sweet spot for coherence; 2.5 allows up to 30
               where the beats actually need it],
  "medias": [
    {"role": "image", "value": "<character_sheet_id>"},
    {"role": "image", "value": "<scene_beat_sheet_id>"},
    {"role": "image", "value": "<environment_reference_id>"}
  ],
  "prompt": "<full Prompt B text from Step 4>"
}
```

**Default generation settings:**
- Aspect ratio: `16:9`
- Duration: `10` seconds (adjustable 8-15 per shot)
- Resolution: `720p` (Seedance 2.0 default)
- Mode: `std` (standard)

**If the preset matcher triggers:** Always decline the preset and
generate literally. Scene-motion prompts are custom-crafted and should
not be overridden by preset templates. Use `declined_preset_id` to
bypass.

**Delivery:** Report the job ID, what to watch for (from Director's
Note), and the environment risk check. The widget renders automatically.

---

## Multi-Shot Scene Workflow

For a scene with multiple shots (e.g., a 4-shot record store story):

```
SHOT 1:
  Step 1 → Character Sheet ✓ (generate once)
  Step 2 → Environment Reference ✓ (generate once per location)
  Step 3 → Beat Sheet for Shot 1
  Step 4 → Prompt for Shot 1
  Step 5 → Upload for Shot 1
  Step 6 → Generate Shot 1

SHOT 2:
  Step 1 → SKIP (reuse character sheet)
  Step 2 → SKIP (reuse environment reference — same store)
  Step 3 → Beat Sheet for Shot 2
  Step 4 → Prompt for Shot 2
  Step 5 → Upload for Shot 2 (only beat sheet is new)
  Step 6 → Generate Shot 2

SHOT 3: [same pattern...]
SHOT 4: [same pattern...]

If the location changes between shots:
  Step 2 → NEW environment reference for the new location
```

---

## Post-Generation Options

After each shot renders, offer these follow-up options:
- **Re-generate:** Same prompt, new seed — for variation
- **Adjust prompt:** Modify specific beats or camera behavior
- **Adjust beat sheet:** Return to Step 3a to rewrite specific beats
- **Next shot:** Proceed to the next shot in the sequence
- **Different location:** Generate new environment reference (Step 2)
- **Different character:** Return to Step 1 with a new reference image

---

## Hard Rules

1. Never skip steps. Each step produces a visible deliverable.
2. Always wait for user confirmation before advancing (except Step 5→6).
3. The character sheet, environment reference, and beat sheet MUST be
   visually consistent with each other.
4. Art style detected in Step 1 must be preserved through every step.
5. Default generation: 16:9 aspect ratio, 10 seconds, 720p.
6. Prompt B is always the full prompt passed to Seedance — never a
   summary or truncated version.
7. All SHOT blocks must be written out fully — no shortcuts.
8. The negative prompt is always generated fresh per output.
9. Shot 1 of every beat sheet is always a hook — already in motion.
10. @image2 (beat sheet) provides body mechanics AND environment context.
11. @image3 (environment reference) provides set design ground truth.
12. One shot = one pipeline pass through Steps 3-6.
13. Steps 1-2 are reusable across shots in the same scene/location.
14. Always decline Seedance preset matches — generate literally.
15. Environment must be described in the prompt AND shown in @image2
    and @image3 — triple reinforcement.

## Manifest Integration

This skill's pipeline (character sheet -> environment reference -> scene
beat sheet -> prompt authoring -> media upload -> generation) touches the
manifest at two different points when the shot belongs to a
Greenlight-Local production (a `project.json`-backed project — see the
`production-manifest` skill):

1. **Character sheet / environment reference steps**: these produce locked
   reference assets, not generations. If the character or location doesn't
   already exist in `entities.characters`/`entities.locations`, register it
   per `production-manifest`'s "Register an entity" operation
   (resource-first — the entity and its `ref_images` must exist before the
   shot itself references it). If it already exists, skip this step.
2. **Final generation step**: once Seedance 2.0 produces the shot's video,
   log it per `production-manifest`'s "Log a generation" operation —
   `kind: "motion"`, `model` set to the Seedance version actually used (or whatever model
   ran), `prompt_file` pointing at the authored prompt, `output` pointing at
   the generated video, and `inputs[]` listing the character/environment
   reference images, audio, and anchor video actually attached to the job.
3. If the shot's `status` was `todo`, bump it to `in-motion`.

The beat sheet itself isn't a manifest artifact — only the assembled prompt
and the resulting generation are. `verdict`/`selected` are set later during
review.

See `production-manifest/SKILL.md` and `references/manifest-operations.md`
for the exact JSON shapes.
