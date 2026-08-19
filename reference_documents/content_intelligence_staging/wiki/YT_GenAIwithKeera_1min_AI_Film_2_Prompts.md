---
title: "GenAI with Keera — How I Made a 1-Minute AI Film With Only 2 Prompts"
type: source
domain: [ai-video]
tags: [seedance, seedance-2-5, claude-skills, higgsfield, storyboard, workflow, character-consistency]
created: 2026-08-19
updated: 2026-08-19
sources: []
---

# GenAI with Keera — How I Made a 1-Minute AI Film With Only 2 Prompts

- **URL**: https://www.youtube.com/watch?v=OFD9blyx204
- **Channel**: GenAI with Keera
- **Published**: 2026-08-16 · **Duration**: 8:26
- **Sponsored by**: Higgsfield (disclosed)
- **Resources**: skill file on Google Drive; prompts and references on Notion
  (both linked from the video description)

A one-minute superhero short assembled from **two 30-second Seedance 2.5 clips,
generated from two prompts**. The video is mostly about the workflow that made
that possible rather than the film itself.

## The workflow

1. **Build a prompting skill first.** Rather than prompting from scratch each
   time, the creator built a Claude skill for Seedance 2.5 — see
   [[Technique_Build_A_Prompting_Skill_From_Vendor_Docs]].
2. **Run the skill on the idea.** The skill interviews the user (and will
   propose ideas if the user has none), then emits a full script.
3. **Design wardrobe separately** from the character, as its own asset.
4. **Generate a storyboard image** before spending video credits, as a cheap
   direction check — composition, character, environment. Explicitly *not* a
   prediction of the final frame, since image and video models differ.
5. **Generate in Higgsfield** with Seedance 2.5, uploading face and outfit
   references and tagging them inline in the prompt where each is mentioned.
6. **Assemble** in DaVinci Resolve, score from a stock music library, export.

Two-act structure across the two clips: struggle (powers not yet controlled),
then payoff (control, used to save someone).

## The copyright-filter workaround

Seedance rejected an outfit that was only *loosely* inspired by an existing
character design. The workaround that got it through: **describe the outfit in
the prompt text**, and supply a body reference wearing plain clothing, letting
the model layer the described outfit on top — rather than supplying a reference
image of the outfit itself. See [[BP_Working_Around_Model_Content_Filters]].

## Settings used

30 seconds · 720p · audio on.

## Related Pages

- [[Tool_Seedance_2_5]]
- [[Technique_Build_A_Prompting_Skill_From_Vendor_Docs]] — the core idea of this video
- [[Technique_Storyboard_Before_Video_Credits]]
- [[YT_JOEY_Seedance_25_Realism_Cheat_Codes]] — same model, same week, complementary approach
