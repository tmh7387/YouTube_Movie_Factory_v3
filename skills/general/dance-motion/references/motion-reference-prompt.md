# 16-Panel Motion Reference Sheet

Use this template when generating the motion reference sheet in Step 2.
The process has two sub-steps: (a) outline the routine, (b) generate
the image.

## Step 2a — Outline the Routine

Write a 16-count dance routine for the specified dance style. The
outline must follow this structure:

### Outline Format

```
Bold title at the top of the sheet:
"[STYLE NAME] SOLO — 16 COUNTS — 15 SECONDS — [MOOD/ENERGY TAG]"

Movement:
Each panel captures one dance move in this order:

1. [MOVE NAME] — [full body position description with weight
   placement, limb angles, torso orientation, expression]
2. [MOVE NAME] — [description]
...through to...
16. [MOVE NAME] — [final pose/freeze description]
```

### Outline Rules

1. Exactly 16 panels, no more, no less.
2. First panel: always a ready/entry position or opening stance.
3. Last panel: always a final pose, freeze, or attitude hold.
4. Build intensity: panels 1–4 simple/foundational → 5–10 build
   complexity → 11–14 peak energy → 15–16 resolve and pose.
5. Every move must be physically achievable from the previous one —
   no teleporting between positions.
6. Include direction arrows description for each panel (which way
   force/energy is directed).
7. Mix move types: isolations, full-body, level changes, directional
   shifts, freezes.
8. At least 2 freeze/hold moments in the 16 panels.
9. All vocabulary must match the dance style (hip-hop uses "bounce",
   "groove", "pop"; K-Pop uses "snap", "cut", "hit"; contemporary
   uses "extend", "release", "fold").

### Dance Style Vocabulary Guide

**90s Hip-Hop:** bounce, groove, drop, isolation, slide, pop, lock,
rock, step, swag, pocket, head nod, chest pop, shoulder roll

**K-Pop Girl Crush:** snap, cut, hit, slice, thrust, lock, whip,
flick, stare, freeze, power pose, attitude, fierce

**Contemporary/Lyrical:** extend, release, fold, contract, reach,
fall, recover, spiral, suspend, breathe, float, ground

**Latin/Reggaeton:** roll, wave, grind, step, pivot, shimmy, pop,
isolate, whine, dip, sway, kick, slide

**Street/Breaking:** drop, freeze, spin, kick, plant, power, sweep,
thread, windmill, flare, stance, lock

**Afrobeats:** shake, roll, step, bounce, wave, lean, kick, pop,
groove, whine, dip, pulse, stomp

## Step 2b — Generate the Motion Reference Image

Once the user approves the outline, generate the 16-panel image.

### Prompt Template

Combine the approved outline with this wrapper:

```
Use the uploaded character sheet as the identity reference.
Create a 16-panel motion reference sheet showing this exact character
performing each of the following dance positions. Maintain perfect
character consistency across all 16 panels — same face, same outfit,
same body proportions, same art style as the character sheet.

[INSERT APPROVED OUTLINE HERE]

FULL BODY RULE — CRITICAL:
Every single panel must show the complete full body from head to toe.
No cropping at waist, stomach, hips, or knees under any circumstance.
Always leave clear space above the head and below the feet in every
panel. This rule applies to all 16 panels without exception.

Include red directional arrows on each panel showing the direction
of force, momentum, or energy for that specific move.

Environment:
Clean white or neutral background. No props, no set, no background
elements. Character only.

Quality:
High detail, sharp composition, balanced grid layout, clean panel
borders, print-ready editorial poster.
```

### Negative Prompt (append to the end)

Generate a custom negative prompt based on:
- The actual art style detected from the character sheet
- The specific dance style and its common failure modes
- Any distinctive character features that must not change

Always include these baseline items plus style-specific additions:
```
blurry, low quality, extra limbs, distorted anatomy, bad proportions,
messy layout, overcrowded panels, text errors, missing arrows, wrong
face, wrong outfit, wrong hair color, changed art style, cropped body,
missing legs, missing feet, cut off at waist, partial body panels,
invented character appearance, [ADD STYLE-SPECIFIC ITEMS HERE]
```

### Generation Parameters

| Parameter      | Value           |
|----------------|-----------------|
| Model          | `gpt_image_2`   |
| Aspect Ratio   | `16:9`          |
| Media Role     | `image` (attach the Step 1 character sheet — use job ID) |

### Quality Checks

After generation, verify:
- [ ] All 16 panels present and numbered
- [ ] Character identity matches the character sheet exactly
- [ ] Full body visible in every panel (head to toe)
- [ ] Red directional arrows present on each panel
- [ ] Art style consistent with the character sheet
- [ ] Moves flow logically from panel to panel
- [ ] Clean neutral background, no props

---

## Example Outline — 90s Hip-Hop

This example is for reference only. Never copy it directly — always
generate a fresh unique routine for each request.

```
"90s REWIND HIP-HOP SOLO — 16 COUNTS — 15 SECONDS — SWAG & GROOVE"

1. (The Drop) — Sharp groove squat, both knees drive down, spine
   straight, arms hang loose at sides, weight through heels
2. (The Bounce) — Rebound upward, hips push forward at peak, chest
   lifts, chin up with attitude, arms relaxed
3. (Left Shoulder Roll) — Left shoulder rolls forward in clockwise
   circle, right shoulder frozen, head centered
4. (Right Shoulder Roll) — Mirror: right shoulder counterclockwise,
   left locked, eyes half-lidded
5. (The Cross-Step) — Right foot crosses over left, torso rotates,
   arms swing in opposition
6. (The Unwind) — Arms extend wide to wingspan, chest opens to
   camera, power stance
7. (Chest Isolation Back) — Ribcage pulls sharply backward, hips
   and head fixed
8. (Chest Isolation Forward) — Ribcage drives forward, hips and
   head stationary
9. (Double Knee In) — Both knees pinch inward, knock-knee position,
   hands on hips
10. (Double Knee Out) — Knees snap outward explosively, wide
    power-squat
11. (Hip Groove Left) — Left hip drives left, ribcage counters
    right, left arm extends
12. (Hip Groove Right) — Mirror: right hip drives right, attitude
    expression
13. (The Kick-Step) — Right leg snaps forward, pointed toe, arms
    trail behind
14. (The Slide) — Smooth lateral slide left, left arm points
    direction
15. (Snap Freeze) — Dead freeze: right hand snaps at ear, left
    hand on neck, zero movement
16. (Final Swag Pose) — Three-quarter stance, hand on hip, direct
    camera stare, complete freeze
```

## Example Outline — K-Pop Girl Crush

```
"K-POP GIRL CRUSH SOLO — 16 COUNTS — 10 SECONDS — FIERCE &
UNAPOLOGETIC"

1. (Ready Stance) — Feet shoulder-width, arms locked at sides, chin
   down, cold intense stare, full body tension
2. (Chest Pop #1) — Explosive chest thrust forward, arms snapped
   behind back, shoulders pulled backward
3. (Arm Isolation Left) — Left arm slices horizontally across chest
   at neck height, right arm rigid at side
4. (Arm Isolation Right) — Right arm mirrors slice, left locks rigid,
   head level
5. (Double Arm Snap Out) — Both arms snap to wide "T", wrists flexed
   down, head tilts right
6. (Chest Pop #2) — Harder chest pop, fists tight to ribs, more force
7. (Body Wave Roll) — Full body ripple chest through hips and knees,
   arms float outward
8. (Hip Cut Left) — Hips snap left, right arm cuts diagonal down,
   left arm 90° bend
9. (Hip Cut Right) — Mirror: hips right, left arm diagonal, right
   arm 90°
10. (Low Lunge Freeze) — Deep slow lunge left, right leg extends
    back, right arm forward, freeze
11. (Rise Snap) — Explosive upward burst, arms cross chest in X,
    feet plant simultaneously
12. (Neck Roll) — Head rolls right to left with attitude, arms wide,
    cold smirk
13. (Chest Pop #3) — Sharpest pop, elbows drive back maximum force,
    chin lifts
14. (Power Reach) — Right arm extends forward-up 45°, left drives
    back, torso leans into reach
15. (Freeze Lock) — Rigid angular hold, right arm extended, left
    bent 90°, full stop
16. (Final Stare Pose) — Upright stance, chin raised, left hand on
    hip, right arm points at viewer
```
