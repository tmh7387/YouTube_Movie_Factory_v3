---
name: controlnet-guided-environment-replacement
description: Replaces or transforms the background/environment of a video while preserving the original subject and camera movement using ControlNet signals (depth, canny edges, pose). Use this when you need to place a subject into a completely different environment — e.g., turning an office into a lava field, a street into a flooded zone, or a room into a spaceship interior — without re-shooting. Applies to any scene requiring dramatic environment changes with intact foreground subjects.
---

# ControlNet-Guided Environment Replacement

Replaces or transforms the background and environment of a video while keeping the original subject perfectly intact, using ControlNet guidance signals to anchor the generation to the source footage's structure.

## When to use
- You need to place a real subject into a fantastical or completely different environment (lava, space, underwater, sci-fi interior, etc.)
- You want to change the setting of a scene without re-shooting
- A music video, brand film, or short film scene needs a dramatic environment transformation
- You need the camera movement and subject position to remain consistent with the original shot

## Core technique
ControlNets work by encoding structural information from the source video — depth, edges, and pose — and injecting that structure as constraints into the generation process. This forces the model to respect the spatial layout and subject position of the original footage even while replacing the visual content. The subject mask further isolates the foreground so the model focuses its creativity on the background region only.

The most critical quality step is the final compositing pass: rather than trusting the AI to reproduce the subject accurately, you paste the original subject pixels back on top using the same mask. This guarantees a sharp, artifact-free foreground regardless of generation quality.

## Prompt template
```
{environmental_transformation_description}. {atmospheric_details_lighting_and_mood}. Do not change the composition. Do not change the look of the {subject_description}.
```

## Example
```
The floor is on fire, the ground is burning. flowing lava and molten rock surround the person. Do not change the composition. Do not change the look of the blonde man.

New cinematic sci-fi movie. A man standing at a control console inside a futuristic space station. The interior is constructed from brushed stainless metal panels with glowing blue and white accents. A holographic screen floats with data readouts. Through the large window behind him, space is vast and twinkling stars and distant nebulas. Volumetric moody lighting with cool blue ambient fill and warm orange rim light from the console.
```

## Workflow
1. Extract control signals (depth, canny edges, pose, subject mask) from the source video via an automated preprocessor.
2. Generate style reference images for the desired environment using a frame from the source video as compositional reference.
3. Load the control signals, source video, subject mask, reference images, and text prompt into a ControlNet-guided video-to-video pipeline.
4. Write the prompt describing the new environment in detail: materials, lighting, atmospheric effects. Add explicit subject-preservation instructions (e.g., "Do not change the look of the [subject].").
5. After generation, composite the result: use the mask to replace the subject region with the original footage, preserving every detail of the foreground subject.

## Pro tip
Never rely on the AI generation alone for the foreground subject — always composite the original masked subject back on top of the AI output as the final step. This single step eliminates AI artifacts on the person and produces results that are indistinguishable from a traditional VFX composite.

## Tool compatibility
Works with any video-to-video model that supports ControlNet inputs (depth, canny, pose). Final compositing works with any compositing software.
Verified with: VACE + Skyreels V3 (merged model), ComfyUI, After Effects, Blender, Nano Banana, Qwen Image Edit