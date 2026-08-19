---
title: Killing the Plastic Look
type: best-practice
domain: [ai-video]
tags: [realism, seedance, texture, lighting, prompt-engineering]
created: 2026-08-19
updated: 2026-08-19
sources: [[YT_JOEY_Seedance_25_Realism_Cheat_Codes]]
---

# Killing the Plastic Look

"Plastic" is the tell that a clip was generated rather than photographed:
surfaces too clean, light too even, motion that reads as an image being animated
rather than a scene being filmed.

## Causes

- **Pinning a literal first frame.** Locks position, but the motion inherits a
  still's stiffness. See [[Technique_Spatial_Geometry_Lock]].
- **A sanitised scene plate.** Even exposure and clean highlights read as CG.
- **Opening on a held pose.** A character who starts still and then starts
  moving looks animated; one already in motion looks filmed.
- **No texture vocabulary.** Absent instructions, surfaces default to glossy.

## The counters

**Ask for optical imperfection.** Organic film grain, halation around hot light
sources, high dynamic range, large-format film. Overexposure in the plate is a
feature — it carries through to the generation.

**Ask for material honesty.** Matte non-reflective surfaces, lived-in worn
materials. Say what things are made of and how used they are.

**Negate the wrong register explicitly.** State that it is *not* a 3D render,
*not* a game engine, *not* a game-cutscene aesthetic. Describing the right look
is not sufficient; name the wrong one.

**Never open or close on stasis.** Start the shot with the character already
mid-action, and don't end on them coming to rest.

**Name costumes as costumes.** If a character is in a suit or a creature
costume, say so — otherwise the model may render the creature as real, and the
physics and skin response go with it.

## Related Pages

- [[Technique_Prompt_Top_Loading]] — where this vocabulary belongs in the prompt
- [[Technique_Scene_Plate_First]]
