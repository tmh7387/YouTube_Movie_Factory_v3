# Seedance 2.0 Prompt Framework

This is the complete prompt framework for writing Seedance 2.0 dance
video prompts. Follow it exactly when constructing prompts in Step 3
of the Dance Motion pipeline.

## Output Structure

Every output must be in this exact order:

```
── PROMPT A ──
[full text]

── PROMPT B ──
[full text]

── DIRECTOR'S NOTE ──
[all six fields]
```

---

## Prompt A Template

Prompt A is the short-form identity and intent lock:

```
Use the uploaded @image1 as the character source. Do not invent a
new character. @image2 is a 16-panel motion reference sheet showing
the character across [MOTION CATEGORY] positions. Use as body
mechanics reference for weight distribution, [category-specific
mechanics], and limb angles. Do NOT follow panel numbers as
sequential instructions.

Duration: [routine length in whole seconds — 15 fits a full 16-count on
either version; 2.5 allows up to 30]. Aspect ratio: [aspect_ratio]. Mode:
image-to-video using @image1 as character identity reference and
@image2 as body mechanics motion reference. 16 shots, Smart Cuts ON.

@image1 is the sole character. Animate this character performing
[dance style description — specific energy and vocabulary].
The character's appearance, outfit, face, hairstyle, and body
proportions must remain identical to @image1 in every frame.
The character moves through 16 dance counts in [duration] seconds with
natural [dance style] rhythm and musicality.
```

---

## Prompt B Template

Prompt B is the full production prompt. This is what gets passed
to Seedance 2.0 as the `prompt` parameter.

### Block 1: CHARACTER & SET DETAILS

```
CHARACTER & SET DETAILS
─────────────────────────────────────────

@image1: [Full physical description of the character exactly as
seen in the character sheet — body type, art style, skin tone,
hair color and style, face details, outfit with fabric and texture
specifics, accessories, footwear, any text printed on clothing,
demeanor and energy. State the art style explicitly. This is
Seedance's consistency anchor — every detail is checked against
every frame.]

@image2: 16-panel motion reference sheet showing the character
across [MOTION CATEGORY] positions. Use as body mechanics
reference for weight distribution, limb angles, and recovery
positions. Do NOT follow panel numbers as sequential instructions.
All motion is described explicitly in the SHOT blocks below.
```

### Block 2: VISUAL STYLE LOCK

```
VISUAL STYLE LOCK:
Match the exact rendering style of @image1 in every single frame.
The art style must remain consistent from the first frame to the
last. [List 3–5 specific visual details that must persist:
clothing texture, accessories, distinctive markings, fabric
patterns, etc.]
```

### Block 3: SFX & ENVIRONMENT

```
SFX & ENVIRONMENT:
[Location — specific and appropriate to dance style]
[Time of day + atmosphere + lighting conditions]
[Active environmental elements: breeze, reflections, dust, etc.]
Music: [Specific tempo and feel matching the dance style]
```

**Environment suggestions by dance style:**

| Style | Environments | Music |
|-------|-------------|-------|
| 90s Hip-Hop | Rooftop parking, concrete plaza, basketball court | 85-95 BPM boom-bap, vinyl warmth |
| K-Pop | Neon studio, glass-wall rooftop, LED stage | 110-130 BPM synth-pop, hard snare |
| Contemporary | Empty theater, open field, warehouse | 60-80 BPM piano/strings, ambient |
| Latin/Reggaeton | Beach sunset, courtyard, club interior | 95-105 BPM dembow, congas |
| Street/Breaking | Subway platform, alley, warehouse | 100-110 BPM breakbeat, heavy bass |
| Afrobeats | Outdoor market, terrace, festival ground | 100-115 BPM log drum, shaker |

### Block 4: HOOK RULE

```
HOOK RULE — NON-NEGOTIABLE:
Shot 1 opens mid-action. Never a neutral pose. @image1 snaps INTO
frame on the first hit. The physical event is already happening
when the camera opens.
```

### Block 5: 16 SHOT BLOCKS

Write every shot following this template:

```
SHOT [N] — [MOVE NAME] — [optional: HOOK ENTRY on Shot 1]
@image1 [exact body action — already in motion on first frame if
Shot 1. Describe weight, force direction, limb position, body
axis, and physical intent using correct dance vocabulary.]
Camera: [exact Seedance native syntax — see Camera Syntax below]
Speed: [real-time / light slow / medium slow / heavy slow /
extreme slow]
SFX: [specific sounds matching the motion — name every sound]
```

**Shot block rules:**
- Every shot starts with `@image1 [action]`
- Never write "She", "He", or "the character"
- Include one visible character detail every 3–4 shots (clothing
  texture, accessory, footwear, hair detail)
- Write "complete freeze — zero movement" on all hold/freeze shots
- Max 2 camera movements per shot
- No timestamps or time codes anywhere

### Block 6: TIMING LANGUAGE

```
TIMING LANGUAGE — NO TIMESTAMPS EVER:
Express all duration through descriptive language:

Short explosive action:
"fires in a single explosive beat" /
"one sharp instant" / "single decisive count"

Flowing transition:
"continuous motion through the full arc" /
"weight transfers smoothly into the next position"

Holds and freezes:
"complete freeze — zero movement" /
"holds for the full duration" /
"dead still — no fabric movement, no sway"

Speed within a shot:
real-time / light slow / medium slow /
heavy slow / extreme slow

Smart Cuts handles all rhythm and transitions.
```

### Block 7: FOOTER

```
Smart Cuts: ON
Total duration: [as set above — 15s for a standard 16-count].
```

### Block 8: NEGATIVE PROMPT

Generate fresh for every output. Never hardcode. Base it on:
- The actual art style of @image1
- The detected dance style / motion category
- The specific failure risks of that motion type
- Any props or elements that must appear or must not appear

Always include these baseline items:
```
No face morphing or identity drift between shots. No extra or
missing fingers. No floating — all foot contacts must be grounded
with connected shadows. No exaggerated rubber-body distortion on
isolations. No clothing changes. No additional characters entering
frame. No robotic or mechanical movement — natural human groove
with weight.
```

Then add style-specific items (examples):
- Photorealistic: "No cartoon, anime, cel-shaded, or painted styles"
- Anime: "No photorealistic rendering, no live-action skin texture"
- 3D Stylized: "No flat 2D rendering, no cel-shading"

---

## Camera Syntax Reference

Use ONLY these exact Seedance native camera terms:

| Camera Movement | Syntax |
|----------------|--------|
| No movement | `static camera locked off` |
| Subtle handheld | `handheld subtle` |
| Aggressive handheld | `handheld aggressive camera shake` |
| Move toward subject slowly | `slow dolly in` |
| Move toward subject fast | `fast dolly in` |
| Move away slowly | `slow dolly out` |
| Move left | `pan left` |
| Move right | `pan right` |
| Tilt up | `tilt up` |
| Tilt down | `tilt down` |
| Low angle following | `low-angle tracking shot` |
| Side following | `side-profile tracking shot` |
| Circular movement | `slow orbit` |
| Following movement | `tracking shot` |
| Rise up | `slow crane up` |
| Fast swish | `whip pan` |
| Speed change | `speed ramping: real-time → slow-motion → real-time` |

**Rules:** Max 2 movements per shot. Never write "zoom in" or vague
direction words. Always specify the angle and framing (frontal,
side-profile, low-angle, etc.).

---

## Director's Note Template

Always end with this block:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIRECTOR'S NOTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MOTION CATEGORY SELECTED: [name + one sentence explaining why]

SIGNATURE MOMENT: [The one shot to spend best credits on]

GENERATE FIRST: [Which shot to produce first and why]

WHAT TO WATCH FOR: [One detail confirming it worked]

IF IT FAILS: [One prompt change that fixes the most likely failure]

SEEDANCE TIP: [One practical tip specific to this motion type]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 22 Global Rules

These rules apply to every prompt generated by this skill. Never
violate any of them.

1. Detect motion category BEFORE writing. State it at the top.
2. All vocabulary, SFX, and camera energy must match the detected
   motion category.
3. Write every prompt fully. No summaries. No shortcuts.
4. Prompt A always starts: "Use the uploaded @image1 as the
   character source. Do not invent a new character."
5. Prompt B always starts with @image1 and @image2 blocks.
6. Every SHOT block starts with "@image1 [action]".
7. Shot 1 is always a HOOK — already in motion.
8. Include one visible character detail every 3–4 shots.
9. Always include VISUAL STYLE LOCK block.
10. Always use exact Seedance native camera syntax.
11. Always specify SFX on every single shot.
12. Always state Music on the SFX & ENVIRONMENT line.
13. Never use timestamps or time codes anywhere.
14. Speed is expressed descriptively only.
15. Hold/freeze shots: "complete freeze — zero movement."
16. Max 2 camera movements per shot.
17. @image2 is body mechanics reference only.
18. Pacing reflects physical logic of the motion type.
19. Always end with DIRECTOR'S NOTE.
20. Negative prompts generated fresh per output. Never hardcoded.
21. Multiple characters: separate @image tag per character.
22. Output order: PROMPT A → PROMPT B → DIRECTOR'S NOTE.
