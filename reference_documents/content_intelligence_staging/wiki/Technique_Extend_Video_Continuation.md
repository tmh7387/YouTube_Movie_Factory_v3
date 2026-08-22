---
title: Extend Video Continuation
type: technique
domain: [ai-video]
tags: [seedance, seedance-2-5, continuity, long-form, editing]
created: 2026-08-19
updated: 2026-08-19
sources: [[YT_JOEY_Seedance_25_Realism_Cheat_Codes]]
---

# Extend Video Continuation

Using Seedance 2.5's extension feature to grow a clip in either direction, and
the LLM step that makes the continuation prompt accurate.

## What the feature does

Feed in an existing clip and generate more of it — **out to 30 seconds**, either
as a sequel (after) or a prequel (before). The model reads the whole input clip,
so it already knows where subjects are placed and what they look like; you're
describing what happens next, not re-establishing the world.

## The step that makes it work

Don't write the continuation prompt from memory. Put the clip into Claude and
ask it to *analyse each frame* — what's happening, where everything sits in the
frame — and then write the continuation from that reading.

That analysis is what lets you write continuity-preserving instructions at the
right level of detail:

> "He looks down, takes the chocolate bar out of his pocket, starts eating,
> looks up at the mirror — his hand stays where it is on the side of the washing
> machine."

The hand note is the point. Without frame analysis you don't know the hand was
there to preserve.

## Result quality

Reported as visually seamless at the join, to the extent that the seam wasn't
identifiable in the edit.

## Key Takeaways

- Extension is a continuity tool, not just a length tool.
- Have an LLM read the source clip frame by frame before writing the prompt.
- Name the things that must *not* change, not only the new action.
- Works both directions — you can generate the shot that precedes what you have.

## Related Pages

- [[Tool_Seedance_2_5]]
- [[Technique_Spatial_Geometry_Lock]]
