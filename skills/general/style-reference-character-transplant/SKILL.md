---
name: style-reference-character-transplant
description: Places a consistent character into a new environment while preserving the original color grading, lighting, and cinematic style by supplying a style reference image alongside the new scene prompt. Use this whenever a character needs to appear in multiple locations across a project, when you must match a pre-established visual look, or when continuity of aesthetic between scenes is required — common in narrative films, music videos, brand spots, and multi-scene productions.
---

# Style-Reference Character and Environment Transplant

Place a character into a new environment while maintaining consistent color grading, lighting, and cinematic style by supplying a reference image and explicitly prompting for style preservation — preventing the visual drift that plagues multi-scene AI productions.

## When to use
- A character must appear in multiple distinct locations across a project
- You have an established visual look (color grade, lighting mood) that all scenes must match
- Cutting between scenes that were generated separately and need to feel like the same film
- Brand or narrative consistency is a hard requirement
- You need to change background or setting without regenerating the character from scratch

## Core technique
Image generation models are sensitive to the full context of their input — including reference images. When you upload a reference image and explicitly describe the stylistic properties you want preserved (color grading, lighting temperature, depth of field, cinematic quality), the model uses that image as a style anchor, not just a character template. The critical move is to be explicit in the prompt about *what to keep* (style) and *what to change* (environment), rather than letting the model infer it. This separation of concerns — character/style versus setting — gives the model clear, unambiguous instructions and dramatically improves consistency.

## Prompt template
```
A {shot_type} of {character_description} in {new_environment}. Use the same color grading, lighting, and cinematic style as the reference image, but change the environment to {new_environment_detail}.
```

## Example
```
a cinematic still of a character sitting at a park. Use the same color grading, lighting, and cinematic style as image 1, but change the environment to be a park in los angeles.
```

## Workflow
1. Identify or generate a hero reference image that locks in both the character's appearance and the desired visual style.
2. Write a new prompt that explicitly instructs the model to preserve color grading, lighting, and cinematic style while changing only the environment.
3. Upload the reference image alongside the prompt as a combined character and style anchor.
4. Review the output for color palette, lighting quality, and character fidelity against the original.
5. If drift is detected, reinforce specific style descriptors in the prompt (lighting temperature, depth of field, film grain) and regenerate.
6. Chain outputs: use each approved image as the reference for the next scene to accumulate consistency across a full production.

## Pro tip
Explicitly name the stylistic properties you want preserved rather than just saying 'same style'. Prompts like 'identical warm amber color grade', 'match the soft side-lighting', or 'preserve the shallow depth of field and lens quality' give the model precise anchors. Generic instructions like 'same look' are too vague and produce more drift.

## Tool compatibility
Works with any image generation model that accepts image references or style inputs alongside text prompts.
Verified with: Freepik, Midjourney, Adobe Firefly