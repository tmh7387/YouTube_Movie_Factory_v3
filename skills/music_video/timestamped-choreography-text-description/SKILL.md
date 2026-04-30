---
name: timestamped-choreography-text-description
description: Drives precise, frame-accurate character movement in AI-generated video clips by providing a second-by-second text breakdown of body position, motion direction, and momentum rather than relying on vague action keywords. Use this whenever a scene requires specific dance choreography, athletic movement, or any body motion that generic prompts would render inconsistently. Especially valuable for music videos, dance reels, or performance content where movement quality is central to the scene.
---

# Timestamped Choreography Text Description for Video Generation

Drives precise, frame-accurate character movement in AI video clips by providing a second-by-second narrative breakdown of body position, motion, and momentum instead of relying on vague action keywords.

## When to use
- A scene requires specific dance choreography, athletic movement, or performance gesture
- Generic action prompts (e.g., "she dances") produce inconsistent or generic motion
- You are recreating or referencing a specific movement sequence from real footage
- Music video scenes where movement quality and timing are central to the shot

## Core technique
AI video models respond to motion described as a causal physical sequence, not just a label. By narrating what the body is doing at each second — including the starting position, the mechanical action, the direction of force, and the resulting secondary effects (like hair following through on a head snap) — you give the model enough physical grounding to generate plausible motion.

The technique has three key elements:
1. **Temporal anchoring** — timestamps (00:00, 00:01, etc.) tell the model when each phase of motion begins, preventing the movement from blurring into one generic gesture.
2. **Biomechanical causality** — phrases like "using the momentum from the hair flip, she pops upward" link actions together, making the motion feel physically continuous rather than disconnected.
3. **Exclusivity framing** — opening with "focusing exclusively on the subject's motion and choreography" signals the model to prioritize movement accuracy over environment or style rendering.

## Prompt template
```
Here is the breakdown focusing exclusively on the subject's motion and choreography:
{timestamp_1}: {body_position_and_action_1}
{timestamp_2}: {body_position_and_action_2}
{timestamp_3}: {body_position_and_action_3}
{timestamp_4}: {body_position_and_action_4}
```

## Example
```
Here is the breakdown focusing exclusively on the subject's motion and choreography:
00:00 The dancer begins in a low, deep squat. She executes a sharp, aggressive upward snap of her head, throwing her upper body slightly back and launching her long hair straight up into the air in a dramatic hair flip.
00:01 Using the momentum from the hair flip, she pops upward out of the squat into a wide-legged, bent-knee stance. Her hands push downward toward her upper thighs in a sharp, rhythmic, bouncing motion.
00:02 She fluidly twists her torso and hips to her right, keeping her legs planted in the wide stance.
00:03 She executes a rapid, explosive pivot back to the center. As she turns forward, she drops her left knee downward and inward.
```

## Workflow
1. Break the desired movement into 1-second intervals; note starting body position for each
2. For each timestamp, describe the mechanical action, direction of force, and any secondary physical effects
3. Link actions with causal language ("using the momentum from X") to create physical continuity
4. Open the full prompt with the exclusivity framing header
5. Paste into the animation prompt field; review and add sub-second granularity if motion is still imprecise

## Pro tip
Describe momentum and secondary effects explicitly — hair, clothing, and weight shifts are what make AI-generated movement feel real rather than robotic. A phrase like "launching her long hair straight up into the air" gives the model a secondary physics cue that elevates the whole clip.

## Tool compatibility
Works with any text-to-video or image-to-video model that accepts long-form animation prompts.
Verified with: invideo AI Agent One, Seedance 2.0