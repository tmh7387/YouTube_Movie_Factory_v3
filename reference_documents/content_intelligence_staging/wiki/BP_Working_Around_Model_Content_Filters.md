---
title: Working Around Model Content Filters
type: best-practice
domain: [ai-video]
tags: [seedance, moderation, wardrobe, references, character-design]
created: 2026-08-19
updated: 2026-08-19
sources: [[YT_GenAIwithKeera_1min_AI_Film_2_Prompts]]
---

# Working Around Model Content Filters

Seedance applies strict copyright moderation to **reference images**, and it can
reject an original design that merely resembles a known character — even when
the design has been deliberately changed.

## The pattern observed

An original superhero outfit, loosely inspired by an existing character and
visually distinct from it (hoodie and skirt rather than a bodysuit), was
rejected when supplied as a reference image.

## The workaround

Move the design from the image channel to the text channel:

1. **Describe the outfit in the prompt** rather than showing it.
2. **Supply a body reference in plain clothing.**
3. Let the model layer the described outfit onto the referenced body.

The generation then goes through, because what triggered the filter was the
reference image, not the concept.

## Caveats

This is a route around an over-eager *similarity* filter on genuinely original
work, not a way to launder someone else's character design. If the design isn't
yours, describing it in text instead of showing it changes nothing about whether
you should be generating it.

Note also that both hosted and self-hosted paths for most current video models
moderate submitted assets *and* rewritten prompts, so expect occasional false
positives on ordinary creative briefs.

## Related Pages

- [[Tool_Seedance_2_5]]
- [[Technique_Build_A_Prompting_Skill_From_Vendor_Docs]]
