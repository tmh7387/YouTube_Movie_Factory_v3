# Panel Format Specifications

Layout and structural rules for 6-panel and 9-panel storyboards generated via GPT Image 2.

---

## 6-Panel Storyboard

### Layout
- 2 rows × 3 columns (or 3 rows × 2 columns for vertical orientation)
- Each panel is a self-contained shot — no bleed between panels
- Panels read left-to-right, top-to-bottom

### Structure Purpose
The 6-panel format is optimized for **Seedance 2.0 Omni Reference** workflow:
- Each panel = one shot block in the final Seedance prompt
- The entire storyboard uploads as a single Image 3 reference
- Seedance bridges between panels to generate seamless motion

### Panel Roles
```
[1: HOOK]        [2: ESTABLISH]    [3: ESCALATE]
[4: PIVOT]       [5: CLIMAX]       [6: RESOLVE]
```

### When to Use 6-Panel
- Precise motion control with Seedance 2.0
- Multi-character scenes where every frame matters
- When using Claude master prompt + Seedance pipeline
- Short sequences (5-15 seconds final video)
- When you need tight control over character spatial positions

---

## 9-Panel Storyboard

### Layout
- 3 rows × 3 columns
- Each panel self-contained
- Reads left-to-right, top-to-bottom

### Structure Purpose
The 9-panel format is optimized for **broader narrative arcs**:
- More panels = more story beats before rendering
- Works well with multi-scene / multi-clip pipelines
- Each panel can become a separate I2V generation

### Panel Roles
```
[1: HOOK]           [2: CHARACTER]    [3: WORLD]
[4: INCITING]       [5: RISING]       [6: COMPLICATION]
[7: CRISIS]         [8: CLIMAX]       [9: RESOLUTION]
```

### When to Use 9-Panel
- Longer narrative sequences (15-60 seconds)
- When using multi-scene / multi-clip generation (Kling, SeeDream)
- Story-driven content where pacing needs many beats
- When each panel becomes its own video clip (not one continuous shot)
- Broader coverage of a complex scene

---

## Panel Prompt Precision Requirements

Every panel description MUST include:

1. **Shot type** — EWS, WS, MS, MCU, CU, ECU (see camera-bible.md)
2. **Who** — Which character(s) are visible, what they're doing physically
3. **Camera angle** — Low, high, eye-level, OTS, Dutch
4. **Composition note** — Where subject sits in frame, what's in foreground/background
5. **Lighting** — Direction, quality, color temperature

### Minimum Panel Description Example:
```
Panel 3: Medium close-up. Sarah faces camera-left, jaw tight, right hand gripping
the metal railing. Low-angle, 35mm. Foreground: blurred smoke wisps. Background:
emergency lights pulsing red. Hard side-light from screen glow, 4500K cool.
```

### Common Panel Failures to Avoid:
- ❌ "Panel 3: Sarah looks worried" — No shot type, no angle, no composition
- ❌ "Panel 3: Wide shot of the room" — No character action, no specifics
- ❌ "Panel 3: Close-up of Sarah, dramatic lighting" — "Dramatic" means nothing
- ✅ "Panel 3: CU, Sarah's eyes dart right, catching something off-frame. Eye-level, 85mm shallow DoF. Split lighting — left side in shadow, right side lit by cold blue monitor glow."

---

## Character Consistency Rules Across Panels

1. **5 Anchor Words per character** — Pick 5 physical identifiers and repeat in EVERY panel containing that character. Example: "tall, silver-haired, black coat, angular jaw, green eyes"

2. **Outfit continuity** — Unless time passes, characters wear the same clothes in every panel. If outfit changes, note it explicitly.

3. **Spatial relationship lock** — If Character A is left of Character B in panel 1, maintain this UNLESS the story motivates a switch (and if it does, show the transition in a panel).

4. **Facing direction consistency** — If a character faces right in panel 3 and the next cut is panel 4, they should still face right UNLESS you've shown them turning.

5. **Lighting direction match** — Key light must come from the same direction across panels set in the same location/time. If sun is camera-left in panel 2, it stays camera-left in panel 5 (same location).

---

## Aspect Ratio Specifications

| Format | Dimensions | Use Case |
|---|---|---|
| 16:9 | 1920×1080 / 2048×1152 | Default cinematic, YouTube, web |
| 9:16 | 1080×1920 | Instagram Reels, TikTok, Shorts |
| 1:1 | 1080×1080 | Instagram feed, square social |
| 21:9 | 2560×1080 | Ultra-wide, conference display |
| 4:3 | 1440×1080 | Retro/nostalgic, some presentations |

When generating a storyboard, the overall image should be in the standard format
(typically 16:9 or square) with panels arranged within it. Individual panel CONTENT
should be composed for the final video's aspect ratio.
