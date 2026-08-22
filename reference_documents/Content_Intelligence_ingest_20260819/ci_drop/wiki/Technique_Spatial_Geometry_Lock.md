---
title: Spatial Geometry Lock
type: technique
domain: [ai-video]
tags: [seedance, consistency, continuity, blocking, multi-shot]
created: 2026-08-19
updated: 2026-08-19
sources: [[YT_JOEY_Seedance_25_Realism_Cheat_Codes]]
---

# Spatial Geometry Lock

Keeping successive generations set in the **same physical space**, so a
character doesn't teleport between shots.

## The problem

Generate three clips of a character leaning on a washing machine in a laundromat
and you get three different washing machines, in three different parts of the
room, with three different neighbouring props. Each clip is individually fine;
cut together they don't read as one location.

## The obvious fix, and why it backfires

The instinctive answer is to feed a fixed start frame to every generation. It
does lock position — but it also tends to produce the **plastic look**: the
motion reads as an image being animated rather than a scene being filmed.

## The technique instead

Lock the space in *description* rather than by pinning the first frame:

1. Establish the room once as a [[Technique_Scene_Plate_First]].
2. Carry the same spatial anchors into every prompt — which wall, which
   machine, what's to camera-left, what's visible through the window, where the
   practical lights are.
3. Say where in the frame the subject sits and which direction they face.
4. Let the shot open mid-motion rather than from a held pose.

The distinction that matters: a reference image used as a *description of the
space* behaves differently from the same image used as a *literal first frame*.

## Key Takeaways

- Character teleportation is a spatial-description failure, not a model failure.
- A pinned start frame trades one artefact for a worse one.
- Repeat the same spatial anchor words in every shot of a sequence.

## Related Pages

- [[BP_Anti_Plastic_Realism]]
- [[Technique_Extend_Video_Continuation]] — the other route to continuity in 2.5
