---
title: "Joey's Cinema Director Skill Set"
type: tool
domain: [ai-video, ai-automation]
tags: [claude-skills, seedance, prompt-engineering, free, #emerging]
created: 2026-08-19
updated: 2026-08-19
sources: [[YT_JOEY_Seedance_25_Realism_Cheat_Codes]]
---

# Joey's Cinema Director Skill Set

A free set of Claude skills for cinematic AI video prompting, published by JOEY
(CTRL / noisygroup) and distributed as a public Dropbox folder linked from the
channel's video descriptions ("Joey's Skill Files", dated builds).

## Contents (as of the 081626 build)

| File | Purpose |
|---|---|
| `cinema-director-v3.zip` | Seedance prompting — the headline skill, updated for 2.5 |
| `banana-pro-director-30.zip` | Nano Banana Pro image direction |
| `character-builder.zip` | Character sheets and consistency |
| `story-bible-builder.zip` | Story/world bible construction |
| `How To Upload Skill.rtf` | Installation instructions |

## How they're used together

All three of `banana-pro-director`, `cinema-director-v3` and `character-builder`
are invoked in a **single Claude chat** at the start of a project, so scene
plates, character sheets and video prompts are all produced in one context.

## Behaviour of cinema-director-v3

- Asks which Seedance version is being targeted (2.0 vs 2.5) before writing,
  because the prompt grammars differ.
- Emits a full pre-flight checklist and confirms which reference images are in
  play before generating prompts.
- Supports Higgsfield element tags optionally — works with or without them.
- Encodes physical plausibility rules: how wings carry weight, what it takes to
  get a large body airborne, how bodies move through frame.
- Top-loads shot count, runtime, per-shot beats, style and texture.

## Licensing / distribution

Free, no course or paywall, explicitly offered to be tweaked and adapted. The
author's framing: the skills encode how *he* shoots, and users should adapt them
to encode how they shoot.

## Related Pages

- [[Technique_Prompt_Top_Loading]]
- [[BP_Anti_Plastic_Realism]]
- [[Technique_Build_A_Prompting_Skill_From_Vendor_Docs]] — the same idea, arrived at independently
