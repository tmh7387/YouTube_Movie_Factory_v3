# The Shot Spine — a fixed slot order for Seedance prompts

A production-grade Seedance prompt is a **document with a fixed section order**,
not a paragraph. Same slots, same sequence, every time. When a generation comes
back wrong you can point at the slot that failed, fix that slot, and re-run —
which you cannot do with a prose blob.

**Adapted from Joey's `cinema-director-v3` skill** (CTRL / noisygroup, free
release, August 2026 build — see `docs/JOEY_SKILLS_REVIEW.md`). The slot
architecture and the "write the visible" discipline are his; the wording here is
ours, and the version-routing and asset-binding details are reconciled with the
official BytePlus guidance in `seedance2-5-capabilities.md`.

---

## Why order matters

Two independent reasons, both load-bearing:

1. **Position is priority.** What sits at the head of a prompt is what the model
   holds to. Constraints you cannot afford to lose go early.
2. **Overlay text is decided early.** The no-on-screen-text instruction has to
   sit near the top or it arrives after the decision it was meant to prevent.

## The slots

| # | Slot | Carries |
|---|---|---|
| 1 | Header | shot count · total runtime · per-shot timecodes · cut policy · speed policy |
| 2 | Style prefix | the invariants — capture stack, texture, skin, technical cadence |
| 3 | No on-screen text | the overlay ban, always here, never lower |
| 4 | Critical blocks | scene-specific must-nots; cap at four or they stop reading as critical |
| 5 | Assets | one line per reference: tag = identity + what it does *in this scene* |
| 6 | Geometry map | absolute frame position and depth plane for every subject |
| 7 | First frame | what is already in motion at frame one |
| 8 | Optics | lens lock, stated as a field of view in degrees, per shot |
| 9 | Camera | how the camera behaves and how physical it feels |
| 10 | Light & colour | direction, quality, temperature, and how much of the frame each accent owns |
| 11 | Atmosphere | air density and named depth planes — every particle traced to a source |
| 12 | Action timing | timecoded beats, hard cuts inline |
| 13 | Physics | mass, deformation, rebound, lag, contact |
| 14 | Acting | face, eyes, brow, liveness |
| 15 | Audio | diegetic by default, or the attached track as sole source |
| 16 | Locks | the ordered chain of what must not drift, stated positively |

No prose between blocks. No mode label. No aspect ratio in the prompt body —
that is an API parameter, and on Seedance 2.5 sending the wrong one against a
locked task is a rejection.

---

## The discipline underneath the slots

### Write the visible
The model renders what it can see, count and weigh. Mood words evaporate.
**If a phrase produces no pixel and no sound, cut it.**

| Instead of | Write |
|---|---|
| she looks stressed | shoulders lift, jaw sets, exhales through the nose, eyes fix on the door |
| the alley feels dangerous | one buzzing bulb 30 m back, wet brick, standing water, no other figures |
| fast chase | 110 km/h through traffic, inside leg out over the lane line on turn-in |
| he's much taller | 183 cm to her 168 cm |
| heavy machine | five tonnes, cratering the ground on landing |

Quantities the model actually reads: speed in km/h · height in cm · mass in kg
or tonnes · atmosphere as a density plus named depth planes · direction as
screen-relative *or* character-relative, always labelled · emotion rendered as
muscle · contact rendered as deformation.

### One fact, one slot
Wardrobe lives in Assets and is never re-described in Action Timing — Action
Timing names a garment only when it is *doing* something visible, a hem swinging
clear, hair whipping across the face. Light lives in slot 10, atmosphere in 11.
A prompt that repeats itself reads long without reading specific, and each
duplicate dilutes the original.

### Length
A four-shot sequence with four assets lands around **900–1,400 words**. Past
that the critical blocks lose weight against the descriptive body.

### Every particle has a source
Haze, steam, dust and smoke each need an origin in frame — a vent, a fire, a
kicked floor. Sourceless atmosphere renders as a flat filter over the whole
image instead of as air with depth.

### Never open on stasis
Frame one should already be in motion. A character who starts still and then
begins to move reads as an animated photograph; one already mid-action reads as
photographed. This is the same anti-plastic rule as in
`seedance2-5-capabilities.md`, expressed as a slot.

---

## Version routing feeds the spine

Step 0.5 of `SKILL.md` decides 2.0 vs 2.5. Two ceilings change the *architecture*
of the prompt, not just its trim:

| | Seedance 2.0 | Seedance 2.5 |
|---|---|---|
| Image references | 9 | 30 (50 assets total) |
| Runtime | ~15s | 30s |
| Timestamps | ignored | honoured, integer seconds |

**On 2.0**, reference slots are scarce and contested. Order them: characters in
narrative order → one shared wardrobe sheet → props → environment plate →
video/audio last. Collapse where you must — a prop that only needs to read
approximately can live inside a character's Asset line instead of taking a slot.
Anything past 15 seconds splits into two prompts.

**On 2.5**, slots stop being scarce, which changes strategy rather than just
raising a number: a character can carry a front reference, a profile and a
detail plate instead of one composite; wardrobe, props and environment separate
cleanly; every member of a group gets their own reference.

But **more references is not automatically better.** Near-duplicates blend into
an averaged face. If two references would teach the model the same thing, ship
one.

**Long 2.5 takes (16–30s) need extra anti-drift weight**, because drift
compounds with runtime:
- one anchor reference, held and named in every beat
- the lens lock restated at the top of every beat, not only at the head
- the geometry map restated wherever staging materially resets
- Locks carrying the full ordered chain, every link, no abbreviation

And **runtime available is not runtime required.** Two camera vantages on the
same action are two prompts on 2.5 just as they were on 2.0 — that split is
about coverage, not about the cap. Long sequences also hold better built as a
chain of 2.5–4 s beats than as one unbroken take, so past 15 s the header should
declare the shot budget explicitly: `9 shots across 24 seconds` reads very
differently to the model than `24 seconds`.

---

## Runtime guide

| Beat type | Seconds |
|---|---|
| High-energy cutting | 1.5–2.5 per shot |
| Narrative / dialogue | 2.5–4 |
| A held lipsync line | 4–7 |
| Continuous take | 8–15 |

Timings must sum exactly to the declared total.

---

## Delivery format

1. A bolded title carrying the runtime — `**Underground garage — entry walk — 8s**`
2. A numbered reference list in attach order
3. One fenced code block containing the whole prompt, English only

No preamble, no post-amble. Flag a conflict in a line or two above the title if
one exists. A negative-prompt block ships as an optional second code block, only
when the scene carries a known drift risk or the user asks — grouped by failure
category, comma-separated, no sentences.

Iterations ship as the **revised full prompt**, not as "replace this line",
unless a targeted patch was asked for.

---

## Mapping to this platform

The spine is a Seedance construct. Where it meets our pipeline:

- Slots 5 and 6 (Assets, Geometry Map) are what `seedance2-composition` already
  does — use that skill for the blocking, then place its output in these slots.
- Slot 2's invariants are the natural home for a Project Bible's style rules;
  see the handoff contract in `skills/general/project-bible/SKILL.md`.
- Slots 1 and 12 are where the 2.5 timestamp grammar lands. On 2.0 they degrade
  to shot numbers — the model will ignore the clock times.
- The API-level parameters (ratio, duration, output format) never go in the
  prompt body. They are set by the adapter from the registry — see
  `docs/VIDEO_MODEL_SELECTION.md`.

**MiniMax H3 does not use this spine.** Its grammar is
`integrated_multimodal_description` plus the two audio fields — see
`skills/general/minimax-h3-director/`. Route by the model's dialect.
