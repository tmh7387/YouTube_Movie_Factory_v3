# Seedance 2.5 — capabilities and practitioner findings

Drop-in reference for `seedance2-director/references/`. Sourced from the
2026-08-19 Content Intelligence ingest of two field breakdowns:

- JOEY (CTRL / noisygroup), *The Cheat Codes to Prompting for True Realism with
  Seedance 2.5* — https://www.youtube.com/watch?v=5dWgZDka3Ww
- GenAI with Keera, *How I Made a 1-Minute AI Film With Only 2 Prompts* —
  https://www.youtube.com/watch?v=OFD9blyx204

Model id `dreamina-seedance-2-5-260628`, served through BytePlus ModelArk and
resold via Higgsfield and CometAPI.

## What changed from 2.0

| | 2.0 | 2.5 |
|---|---|---|
| Timestamps | ignored — shot numbers only | integer-second timestamps honoured |
| Max duration | ~15s | **30s** |
| Reference assets | a handful | up to 50 (≤30 images, ≤10 videos, ≤10 audio) |
| Aspect ratios | six fixed | any ratio in [0.4, 2.5] |
| Multi-view subject refs | discouraged | supported |
| Editing / extension | — | instruction editing, forward/backward extension |
| Output | up to 4K | 1080p as observed in both sources |

BytePlus positions this as a production-workflow upgrade rather than a
generational leap — the 2.0→2.5 step is smaller than 1.5→2.0.

Beyond straight generation: 3D clay-model reference (grey-box animatic rendered
into finished style), multi-panel storyboard reference, strict keyframe
reference, instruction-based video editing, forward/backward extension, seamless
transition between two clips, and one-click assembly from a set of stills.

**Locked-parameter rules.** Editing pins both ratio and duration; first-frame and
extension tasks pin ratio. Violating these rejects the request outright.

## Prompt ordering — top-load what must be honoured

What sits at the head of the prompt is held to most reliably, in both image and
video models. Anything you cannot afford to lose belongs at the top, not buried
after three paragraphs of scene description.

Order:

1. Shot count
2. Total runtime, and seconds per shot
3. What happens in each shot — one line each
4. Style — photorealism, organic film grain, halation, high dynamic range, shot
   on large format film
5. Texture — matte non-reflective surfaces, lived-in worn materials
6. Explicit negations of the wrong register — not a 3D render, not a game engine,
   not a game-cutscene aesthetic

Then the scene body underneath.

**If a constraint is being ignored, move it up before rewording it.** Reported
case: background music bleeding into generations unasked; the suggested fix is
positional — put `NO MUSIC WHATSOEVER` / `NO BGM (Background Music)` on the first
line rather than the last. Offered untested by the creator, but consistent with
official 2.5 guidance that negative control is reliable specifically for
subtitles and audio.

## Killing the plastic look

"Plastic" is the tell that a clip was generated rather than photographed:
surfaces too clean, light too even, motion that reads as an image being animated
rather than a scene being filmed.

**Causes.** Pinning a literal first frame; a sanitised scene plate; opening on a
held pose; no texture vocabulary, which defaults surfaces to glossy.

**Counters:**

- **Ask for optical imperfection.** Organic film grain, halation around hot light
  sources, high dynamic range, large-format film. Overexposure in the source
  plate is a feature — it carries through into the generation.
- **Ask for material honesty.** Matte non-reflective surfaces, lived-in worn
  materials. Say what things are made of and how used they are.
- **Negate the wrong register explicitly.** Naming the right look is not enough;
  name the wrong one — not a 3D render, not a game engine, not a game cutscene.
- **Never open or close on stasis.** Start the shot with the character already
  mid-action; don't end on them coming to rest.
- **Name costumes as costumes.** If a character is in a suit or creature costume,
  say so, or the model may render the creature as real — and the physics and skin
  response go with it.

## Scene plate first

Build the environment as a still **before** generating any video and before
building characters into it. Ask the image model for the empty set: the room, the
angle, the practical light sources, the signage, the state of the props. No hero
character in it.

That still is the visual bible for everything downstream — lighting, palette and
lens character are all inherited, so errors here compound.

Specify explicitly: interior/exterior, time of day, camera angle, the state of
individual props, and which direction signage faces relative to camera.

Counter-intuitively, a technically *flawed* plate often produces better video. An
overexposed plate with visible halation reads as photographed; a clean,
evenly-lit one reads as CG.

**Split image models by job.** Seedream 5.0 Pro for scene plates — better
cinematic image character. Nano Banana Pro for faces and wardrobe — face fidelity
is what Seedream doesn't hold.

## Spatial geometry lock — do not pin a first frame

**The problem.** Three clips of a character leaning on a washing machine gives
three different washing machines, in three different parts of the room, with
three different neighbouring props. Each clip is individually fine; cut together
they don't read as one location.

**The instinctive fix backfires.** Feeding a fixed start frame to every
generation does lock position — but it produces the plastic look, because the
motion inherits a still's stiffness.

**Lock the space in description instead:**

1. Establish the room once as a scene plate.
2. Carry the same spatial anchors into every prompt — which wall, which machine,
   what's to camera-left, what's visible through the window, where the practical
   lights are.
3. State where in the frame the subject sits and which direction they face.
4. Let the shot open mid-motion rather than from a held pose.

The distinction that matters: a reference image used as a *description of the
space* behaves differently from the same image used as a *literal first frame*.

## Extension as a continuity tool

2.5 grows an existing clip out to 30 seconds in either direction — sequel or
prequel. The model reads the whole input clip, so it already knows where subjects
are placed and what they look like. You are describing what happens next, not
re-establishing the world.

**The step that makes it work:** don't write the continuation prompt from memory.
Put the clip into Claude and ask it to analyse each frame — what's happening,
where everything sits — then write the continuation from that reading.

> "He looks down, takes the chocolate bar out of his pocket, starts eating, looks
> up at the mirror — his hand stays where it is on the side of the washing
> machine."

The hand note is the point. Without frame analysis you don't know the hand was
there to preserve. **Name the things that must not change, not only the new
action.** Reported as visually seamless at the join.

## Storyboard gate before video spend

Once the video prompt exists, render **one image from it** and look at that before
spending video credits. If the direction is wrong, fix the prompt — an image
costs a fraction of a video generation.

It is not a prediction of the final frame; image and video models are different
models and won't agree on detail. It is a cheap read on direction: is the
character where you thought, is the environment the one you described, does the
framing carry the idea.

Treat it as a gate, not an optional extra.

## Reference-image moderation

2.5 applies strict copyright moderation to reference images and can reject an
original design that merely resembles a known character, even when deliberately
changed. Observed: an original superhero outfit — hoodie and skirt rather than a
bodysuit — rejected as a reference image.

**Workaround:** move the design from the image channel to the text channel.
Describe the outfit in the prompt, supply a body reference in plain clothing, and
let the model layer the described outfit onto the referenced body. What tripped
the filter was the reference image, not the concept.

This is a route around an over-eager similarity filter on genuinely original
work, not a way to launder someone else's character design. If the design isn't
yours, describing it in text instead of showing it changes nothing about whether
you should be generating it.

## Observed pricing

Via Higgsfield: ~250 credits per generation at ~$0.04/credit. A one-minute
project ran to roughly 800 credits ≈ $32. An unlimited-but-serialised promo was
available at the time of the source videos — treat the credit figures as a
snapshot, not a rate card.
