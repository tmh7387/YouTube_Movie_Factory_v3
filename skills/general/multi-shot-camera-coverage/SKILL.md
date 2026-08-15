---
name: multi-shot-camera-coverage
description: Generate multiple camera angles of the same subject from a single reference image by prompting a video model with a numbered shot list. Use when you need scene coverage, consistent character across angles, or want to build a storyboard from one image. Apply for any video type where continuity and multiple perspectives are needed.
---

# Multi-Shot Camera Coverage

Generate comprehensive scene coverage from a single reference image by directing a video model through multiple camera angles in one pass.

## When to use
- You need multiple camera angles of the same subject without re-generating separate images
- You want a consistent character or object across different framings
- You need to build a storyboard quickly from a single strong image
- You want source frames for further scene generation that share the same lighting and style

## Core technique
Most img2video models respond to structured, numbered shot descriptions. By listing shots with explicit numbering — `[1]`, `[2]`, `[3]` — the model treats each numbered entry as a distinct camera position and transitions through them in sequence. The output is a single video that moves between all your shots, giving you multiple usable frames from one generation.

This works because video models interpret structure in prompts: numbered lists signal a sequence of states, not a single held frame.

## Prompt template
```
[1] {shot_type_1}, {subject_description}, {movement_instruction}.
[2] {shot_type_2}, {angle_or_framing}, {movement_instruction}.
[3] {shot_type_3}, {detail_focus}, {movement_instruction}.
[4] {shot_type_4}, {extreme_detail}, {movement_instruction}.
```

## Example
```
[1] Wide living room shot, you centered on the couch, completely still.
[2] Slight left angle, natural sitting posture, still.
[3] Close-up of face, soft expression and ambient light, still.
[4] Extreme close-up of eyes, reflecting the room, still.
[5] Hands resting on lap, no movement, still.
[6] Low angle from floor level, couch and posture emphasised, still.
```

## Workflow
1. Generate or select one high-quality reference image of your subject
2. Write a numbered shot list — be explicit about framing, angle, and movement (or lack of it)
3. Submit the reference image alongside the numbered prompt to your img2video model
4. Import the resulting clip into an NLE
5. Export individual frames at each shot transition as PNG/JPEG files
6. Use these frames as consistent storyboard references or as input images for higher-fidelity individual scene generation

## Pro tip
The exported frames are the real output. The video itself is just the transport mechanism — use it to extract a set of consistently-lit, consistently-styled frames that can feed the next stage of your pipeline. This sidesteps the hardest problem in AI video: getting the same character to look identical across separately-generated images.

## Tool compatibility
Works with any img2video model that accepts image + text prompt input.
Verified with: Seedance 2.0
