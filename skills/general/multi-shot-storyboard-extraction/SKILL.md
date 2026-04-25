---
name: multi-shot-storyboard-extraction
description: Generates a sequence of varied camera angles and shot sizes from a single reference image using a numbered multi-shot text prompt, then exports individual frames from the resulting video to use as consistent storyboards or reference images for further generation. Use this whenever you need scene coverage, multiple angles of a single subject, or a consistent visual reference sheet — ideal for pre-production planning, establishing continuity, or seeding subsequent high-quality generation passes.
---

# Multi-Shot Video Generation for Storyboard Extraction

Generate a sequence of varied camera angles from a single reference image using a numbered multi-shot prompt, then extract individual frames as consistent storyboards or references — solving the AI continuity problem without manually generating each angle separately.

## When to use
- You need multiple camera angles of a single subject or scene
- Pre-production storyboarding where visual consistency across shots is critical
- Generating a reference sheet to seed subsequent, higher-quality image or video generation
- You want to establish shot coverage (wide, medium, close-up, extreme close-up) for a scene
- Any workflow where re-generating the same character or environment repeatedly causes drift

## Core technique
Video generation models maintain visual consistency across a clip because they are generating a temporally coherent sequence rather than independent images. By structuring your prompt as a numbered list of distinct camera positions and framing instructions, you instruct the model to transition between those angles within the clip — effectively directing a multi-shot scene in a single generation pass. Because all shots originate from the same generation pass conditioned on the same reference image, the subject, lighting, and color grading remain consistent across every frame. Extracting specific frames then gives you ready-made, consistent storyboard panels.

## Prompt template
```
[1] {shot_1_description}, {movement_1}. [2] {shot_2_description}, {movement_2}. [3] {shot_3_description}, {movement_3}. [4] {shot_4_description}, {movement_4}. [5] {shot_5_description}, {movement_5}. [6] {shot_6_description}, {movement_6}. [7] {shot_7_description}, {movement_7}.
```

## Example
```
[1] Wide living room shot, you centered on the couch, completely still. [2] Slight left angle, natural sitting posture, still. [3] Slight right angle, relaxed pose with room depth, still. [4] Close-up of face, soft expression and ambient light, still. [5] Extreme close-up of eyes, reflecting the room, still. [6] Hands resting on lap, no movement, still. [7] Low angle from floor level, couch and posture emphasized, still.
```

## Workflow
1. Generate or select a reference image that locks in your subject, environment, lighting, and color palette.
2. Write a numbered multi-shot prompt — each bracketed number describes a unique camera angle or framing, plus a movement instruction (use 'still' if you want clean freeze-frame extraction).
3. Submit the reference image and numbered prompt together to a video generation model.
4. Review the output clip for consistency and shot variety.
5. Import the clip into a non-linear editor; scrub to the cleanest frame within each shot.
6. Export those frames as high-resolution stills for use as storyboard panels or as new reference inputs for higher-quality generation.

## Pro tip
Specifying 'still' or 'no movement' as the camera instruction for each numbered shot dramatically improves frame extraction quality — you get a clean, sharp hold on each angle rather than a motion-blurred mid-transition frame. Use movement instructions (slow push, orbit) only when the motion itself is the deliverable.

## Tool compatibility
Works with any video generation model that accepts image references and supports multi-shot or scene-transition prompting.
Verified with: Seedance 2.0, Premiere Pro (frame export), DaVinci Resolve (frame export)