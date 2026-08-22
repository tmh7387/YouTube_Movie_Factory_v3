---
title: Scene Plate First
type: technique
domain: [ai-video]
tags: [seedance, composition, lighting, image-to-video, pre-production]
created: 2026-08-19
updated: 2026-08-19
sources: [[YT_JOEY_Seedance_25_Realism_Cheat_Codes]]
---

# Scene Plate First

Build the **environment** as a still image before generating any video, and
before building characters into it.

## The technique

Ask the image model for the empty set: the room, the angle, the practical light
sources, the signage, the state of the props. No hero character in it. That
still is the "scene plate" — the visual bible for every generation that follows.

Everything downstream inherits its lighting, palette and lens character, so
errors here compound. The rule of thumb offered: **the better the input to the
video model, the better the output.** Fix the plate and everything else improves
for free.

## Why an imperfect plate can be the right plate

Counter-intuitively, a *technically flawed* plate often produces better video.
An overexposed plate with visible halation — the bloom around hot light sources
— carries that look through into the generation, and the result reads as
photographed rather than rendered. A clean, evenly-lit plate reads as CG.

## Prompt shape used

> "Build me a scene plate of an empty laundromat at night from the inside at a
> 3/4 angle, some washing machines running, some doors open on empty machines, a
> neon sign on the window mirrored from our perspective reading CONTROL WASH."

Note what's specified: interior/exterior, time of day, camera angle, the state
of individual props, and the direction the signage faces relative to camera.

## Model choice

Seedream 5.0 Pro for scene plates (better cinematic image character);
Nano Banana Pro for faces and wardrobe, because face fidelity is the thing
Seedream doesn't hold. See [[Tool_Seedream_5_0_Pro]], [[Tool_Nano_Banana_Pro]].

## Key Takeaways

- Generate the empty set before the characters.
- Specify angle, time of day, light sources and prop states explicitly.
- Don't sanitise the plate — overexposure and halation help.
- Split image models by job: environment vs face.

## Related Pages

- [[Technique_Spatial_Geometry_Lock]] — what the plate is protecting against
- [[BP_Anti_Plastic_Realism]] — why a *start frame* is not the same as a plate
