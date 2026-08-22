---
name: dance-motion
description: |
  End-to-end dance video production pipeline — from a single character
  reference image to a fully generated Seedance 2.0 dance video in five
  steps: (1) character sheet, (2) 16-panel motion reference, (3) Seedance
  prompt authoring, (4) media upload, (5) Seedance 2.0 video generation.
  Use this skill whenever the user says "dance motion", "dance video
  pipeline", "dance workflow", "create a dance video", "animate a dancer",
  "hip-hop dance video", "dance motion reference", "dance character sheet",
  "motion reference sheet", "16-panel dance", "dance routine video",
  "choreography video", or any request that combines character reference
  creation with dance motion video generation. Also trigger when the user
  uploads a character image and asks for a dance animation or choreography
  clip. This skill chains with seedance2-director, seedance2-composition,
  and higgsfield-generate for the final generation step, but owns the full
  orchestration from image input to rendered video output.
---

# Dance Motion — Full Pipeline Skill

Produces a dance video from a single character reference image in five
sequential steps. Each step produces a deliverable the user reviews
before proceeding. Never skip steps or auto-advance without user
confirmation.

## Prerequisites

- One uploaded character reference image (any style: photo, 3D, anime,
  painterly — the pipeline preserves the source style automatically)
- Higgsfield MCP connection active (for Steps 4–5)
- User must specify or confirm: dance style, energy, mood

## Pipeline Overview

```
INPUT: Character reference image
  │
  ├─ Step 1 → Character Sheet (6-panel reference)
  ├─ Step 2 → 16-Panel Motion Reference Sheet
  ├─ Step 3 → Seedance 2.0 Prompt (Prompt A + Prompt B)
  ├─ Step 4 → Media Upload to Higgsfield
  └─ Step 5 → Seedance 2.0 Video Generation
  │
OUTPUT: 15-second dance video (16:9 @ 720p)
```

---

## Step 1 — Character Sheet Creation

**Goal:** Produce a 6-panel character reference sheet that locks identity
across all angles for downstream consistency.

**When to run:** User provides a character reference image and triggers
the dance-motion pipeline.

**Action:** Generate an image using the character sheet prompt.

Read `references/character-sheet-prompt.md` for the exact prompt text.

**Generation method:** Use Higgsfield MCP `generate_image` tool:
- Model: `gpt_image_2` (preserves any art style faithfully)
- Prompt: the full character sheet prompt from the reference file
- Media: attach the user's uploaded reference image with role `image`
- Aspect ratio: `16:9` (landscape to fit the 6-panel layout)

**Delivery:** Present the generated character sheet to the user.
Ask: *"Does this character sheet look accurate? Should I adjust
anything before we move to the motion reference?"*

**Do NOT proceed to Step 2 until the user confirms.**

---

## Step 2 — 16-Panel Motion Reference Sheet

**Goal:** Produce a 16-panel motion reference sheet showing the character
performing 16 distinct dance positions from a specific dance style.

**When to run:** User confirms Step 1 character sheet is approved.

**Action:** Two sub-steps:

### Step 2a — Outline the Routine

First, write a 16-count dance routine outline. Ask the user for the
dance style if not already specified. Default styles to offer:
- 90s Hip-Hop (groove, bounce, isolations, swagger)
- K-Pop Girl Crush (sharp, fierce, attitude)
- Contemporary/Lyrical (fluid, emotional, extensions)
- Latin/Reggaeton (hips, body rolls, footwork)
- Street/Breaking (power, freezes, footwork)
- Afrobeats (body rolls, leg work, shoulder movements)

Read `references/motion-reference-prompt.md` for the prompt template
and an example outline.

**Rules for the outline:**
- Exactly 16 panels, numbered 1–16
- Each panel: a named move with full body position description
- Include direction arrows description for each panel
- Moves must be physically connected — each position flows logically
  from the previous one
- First panel is always a ready/entry position
- Last panel is always a final pose/freeze
- Build intensity: simple → complex → peak → resolve
- Every panel must show FULL BODY (head to toe, no cropping)

Present the outline to the user for approval. Adjust if requested.

### Step 2b — Generate the Motion Reference Image

Once the outline is approved, generate the 16-panel sheet.

**Generation method:** Use Higgsfield MCP `generate_image` tool:
- Model: `gpt_image_2`
- Prompt: Combine the approved outline with the motion reference
  prompt template from `references/motion-reference-prompt.md`
- Media: attach the Step 1 character sheet (use its job ID) with
  role `image`
- Aspect ratio: `16:9` (landscape for the grid layout)

**Delivery:** Present the generated motion reference sheet.
Ask: *"Does the motion reference look good? Are all 16 panels clear
with full-body poses? Ready to write the Seedance prompt?"*

**Do NOT proceed to Step 3 until the user confirms.**

---

## Step 3 — Seedance 2.0 Prompt Authoring

**Goal:** Write a complete Seedance 2.0 dual-prompt set (Prompt A +
Prompt B) with Director's Note, following the Seedance prompt framework.

**When to run:** User confirms Step 2 motion reference is approved.

**Action:** Read `references/seedance-prompt-framework.md` for the
complete prompt structure and rules.

### Prompt Construction Rules

1. **Detect the motion category** from the dance style chosen in Step 2.
   State it at the top of the output.

2. **Analyze @image1** (the character sheet from Step 1):
   Write the full physical description exactly as seen — body type,
   art style, skin tone, hair, face, outfit with fabric/texture,
   accessories, footwear, demeanor. This is the consistency anchor.

3. **Analyze @image2** (the motion reference from Step 2):
   Reference it as body mechanics guide only. All motion is driven
   by the 16 SHOT blocks.

4. **Write all 16 SHOT blocks** following these rules:
   - Every shot starts with `@image1 [action]`
   - Never write "She", "He", or "the character"
   - Shot 1 is always a HOOK — mid-action, never neutral
   - Include one visible character detail every 3–4 shots
   - Camera uses exact Seedance native syntax only
   - SFX on every shot — name every sound precisely
   - Speed expressed descriptively: real-time / light slow /
     medium slow / heavy slow / extreme slow
   - Hold/freeze shots: "complete freeze — zero movement"
   - Max 2 camera movements per shot
   - NO timestamps or time codes anywhere

5. **Choose environment and lighting** that complement the dance style:
   - Hip-Hop → urban rooftop, parking garage, concrete
   - K-Pop → studio, neon stage, rooftop at night
   - Contemporary → open field, empty theater, warehouse
   - Latin → beach sunset, club interior, courtyard
   - Street → subway station, alley, basketball court
   - Afrobeats → outdoor market, terrace, festival ground

6. **Write the negative prompt** fresh — based on the actual art style
   of @image1 and the specific motion category. Never hardcoded.

7. **Write the Director's Note** with all six fields:
   - MOTION CATEGORY SELECTED
   - SIGNATURE MOMENT
   - GENERATE FIRST
   - WHAT TO WATCH FOR
   - IF IT FAILS
   - SEEDANCE TIP

### Output Format

Always output in this exact order:
```
── PROMPT A ──
[full text]

── PROMPT B ──
[full text with all 16 SHOT blocks]

── DIRECTOR'S NOTE ──
[all six fields]
```

**Delivery:** Present the complete prompt set to the user.
Ask: *"Prompt set is ready. Want me to proceed with upload and
generation?"*

**Do NOT proceed to Step 4 until the user confirms.**

---

## Step 4 — Media Upload to Higgsfield

**Goal:** Upload both reference images (character sheet + motion
reference) to Higgsfield and confirm them for generation.

**When to run:** User confirms Step 3 prompt is approved.

**Action:**

1. Call `Higgs:media_upload` with both images:
   - `character_sheet.jpeg` (from Step 1)
   - `motion_reference_sheet.jpeg` (from Step 2)
   - Content type: `image/jpeg`

2. Upload each file using the returned presigned URLs via `curl`:
   ```bash
   curl -s -X PUT -H "Content-Type: image/jpeg" \
     --data-binary @<local_path> '<upload_url>' \
     -w "\n%{http_code}"
   ```

3. Call `Higgs:media_confirm` with both media IDs, type `image`.

4. Store both confirmed media IDs for Step 5.

**Note on file paths:**
- If images were generated via Higgsfield MCP in Steps 1–2, use the
  job IDs directly as media references in Step 5 (no re-upload needed).
- If images were generated externally and saved to disk, upload from
  the saved file paths.

**This step auto-advances to Step 5 — no user confirmation needed.**

---

## Step 5 — Seedance 2.0 Video Generation

**Goal:** Submit the generation job to Seedance 2.0 and deliver the
rendered video.

**When to run:** Step 4 upload is confirmed.

**Action:**

Call `Higgs:generate_video` with these parameters:
```json
{
  "model": "<seedance_2_0 or seedance_2_5 — ask which the user is on>",
  "aspect_ratio": "16:9",
  "duration": 15,   // 16 counts fit 15s comfortably. On 2.5 a longer
                    // routine can run in one generation, up to 30s.
  "medias": [
    {"role": "image", "value": "<character_sheet_media_id_or_job_id>"},
    {"role": "image", "value": "<motion_reference_media_id_or_job_id>"}
  ],
  "prompt": "<full Prompt B text from Step 3>"
}
```

**Default generation settings:**
- Aspect ratio: `16:9`
- Duration: `15` seconds
- Resolution: `720p` (Seedance 2.0 default)
- Mode: `std` (standard)

**If the user requests different settings**, override accordingly:
- Aspect ratio options: `16:9`, `9:16`, `1:1`, `4:3`, `3:4`.
  Seedance 2.5 also accepts any ratio in [0.4, 2.5] plus `adaptive`.
- Duration: up to **15 seconds on Seedance 2.0, 30 on 2.5**. Whole seconds only.
  8-10s is the sweet spot for coherence on a shorter routine; a full 16-count
  routine sits comfortably at 15s.
- The user may request `9:16` for social/mobile — honor it

**Delivery:** The Higgsfield widget renders automatically. Tell the
user: the job ID, what to watch for (from the Director's Note), and
estimated render time (typically 2–5 minutes for 15s at 720p; longer for a
30s generation on 2.5).

---

## Post-Generation Options

After the video renders, offer these follow-up options:
- **Re-generate:** Same prompt, new seed — for variation
- **Adjust prompt:** Modify specific shots or environment
- **New dance style:** Return to Step 2a with the same character
- **Different character:** Return to Step 1 with a new reference image
- **Extend:** on Seedance 2.0, split the routine into two 15-second clips for a
  30-second sequence. On 2.5, prefer either a single 30s generation or the
  extension task, which reads the input clip and continues it — name what must
  not change (hand position, wardrobe, floor mark) rather than re-describing the
  whole scene

---

## Hard Rules

1. Never skip steps. Each step produces a visible deliverable.
2. Always wait for user confirmation before advancing (except Step 4→5).
3. The character sheet and motion reference MUST use the same character.
4. Art style detected in Step 1 must be preserved through every step.
5. Default generation: 16:9 aspect ratio, 720p. Duration follows the routine —
   15s suits a full 16-count; do not pad a shorter routine to fill a ceiling.
6. Prompt B is always the full prompt passed to Seedance — never a
   summary or truncated version.
7. All 16 shots must be written out fully — no shortcuts, no
   placeholders, no "repeat as above."
8. The negative prompt is always generated fresh per output.
9. Shot 1 is always a hook — character already in motion.
10. @image2 is body mechanics reference only — never instruct the
    model to follow panel order sequentially.

## Manifest Integration

This skill's pipeline (character sheet -> 16-panel motion reference ->
Seedance prompt authoring -> media upload -> Seedance 2.0 generation)
touches the manifest at two different points when the shot belongs to a
Greenlight-Local production (a `project.json`-backed project — see the
`production-manifest` skill):

1. **Character sheet step**: if the character doesn't already exist in
   `entities.characters`, register it per `production-manifest`'s "Register
   an entity" operation (resource-first — the character and its
   `ref_images` must exist before the shot references it). If it already
   exists, skip this step.
2. **16-panel motion reference**: treat this as a `storyboard-panel` style
   asset if it's being kept as its own reviewable artifact on the shot
   (log it the way `storyboard-generator` logs panels); if it's purely an
   intermediate working file consumed by the final generation step, it
   doesn't need its own manifest entry — only note it in that generation's
   `notes`.
3. **Final generation step**: once Seedance 2.0 produces the dance video,
   log it per `production-manifest`'s "Log a generation" operation —
   `kind: "motion"`, `model` set to the Seedance version actually used, `prompt_file` pointing at the
   authored prompt, `output` pointing at the generated video, and
   `inputs[]` listing the character reference, motion reference, audio, and
   anchor video actually attached to the job.
4. If the shot's `status` was `todo`, bump it to `in-motion`.

`verdict`/`selected` are set later during review, not by this skill.

See `production-manifest/SKILL.md` and `references/manifest-operations.md`
for the exact JSON shapes.
