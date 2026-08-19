---
title: Prompt Top-Loading
type: technique
domain: [ai-video, ai-image]
tags: [prompt-engineering, seedance, structure]
created: 2026-08-19
updated: 2026-08-19
sources: [[YT_JOEY_Seedance_25_Realism_Cheat_Codes]]
---

# Prompt Top-Loading

Put the constraints you most need honoured at the **very top** of the prompt.

## The claim

In both image and video models, what sits at the head of a prompt is held to
most reliably. Anything you can't afford to lose belongs there — not buried
after three paragraphs of scene description.

## What goes at the top

1. **Shot count** — how many shots the generation contains.
2. **Total runtime**, and seconds per shot.
3. **What happens in each shot**, one line each.
4. **Style** — e.g. photorealism, organic film grain, halation, high dynamic
   range, shot on large format film.
5. **Texture** — e.g. matte non-reflective surfaces, lived-in worn materials.
6. **Explicit negations of the wrong register** — not a 3D render, not a game
   engine, not a game-cutscene aesthetic.

Then the scene body underneath.

## Applied case: unwanted music

Reports of background music bleeding into Seedance 2.5 generations even when
unasked. The suggested fix is positional rather than semantic: move
`NO MUSIC WHATSOEVER` / `NO BGM (Background Music)` to the **first line** of the
prompt rather than leaving it at the end. (Offered as an untested suggestion by
the creator, who hadn't hit the issue personally — worth verifying.)

This matches the official Seedance 2.5 guidance that negative control is
reliable specifically for subtitles and audio.

## Key Takeaways

- Structural facts (shot count, runtime, per-shot beats) go first.
- Style and texture vocabulary goes near the top, not the bottom.
- Negate the wrong aesthetic explicitly, don't just describe the right one.
- If a constraint is being ignored, try moving it up before rewording it.

## Related Pages

- [[Tool_Seedance_2_5]]
- [[BP_Anti_Plastic_Realism]]
