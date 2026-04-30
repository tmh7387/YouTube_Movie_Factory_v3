---
name: agent-driven-music-video-workflow
description: Uses a persistent conversational AI agent to manage the entire music video production pipeline — from audio upload through character sheets, storyboarding, scene-by-scene generation, clip selection, and final stitching — while maintaining project context throughout. Use this when producing a full-length music video with multiple characters, a defined visual style, and the need for consistency across all scenes. Ideal for K-pop, pop, or any music video requiring coordinated shot coverage mapped to song structure.
---

# Agent-Driven Full Music Video Workflow

Orchestrate an entire music video production pipeline through a persistent conversational AI agent that maintains character consistency, visual style, and song structure across all scenes.

## When to use
- Producing a full-length music video (60 seconds or longer) with multiple characters
- When character consistency across many shots is critical
- When you need a storyboard mapped to song structure (intro/verse/chorus/bridge/outro)
- When you want an iterative, approval-gated workflow that prevents wasted compute

## Core technique
The key insight is treating the AI agent as a stateful project manager, not just a prompt executor. By establishing the visual style, character identities, and workflow rules in an initial setup prompt, the agent carries that context forward into every subsequent task — storyboarding, scene generation, and final assembly — without you having to repeat yourself. The approval-gate rule (`stop after each step and wait for my approval`) is especially important: it prevents cascading errors where a bad character sheet or storyboard gets baked into dozens of generated clips before you notice.

The workflow is structured in phases:
1. **Identity phase** — define characters and style
2. **Pre-viz phase** — storyboard mapped to song structure
3. **Generation phase** — scene-by-scene clip creation with cost visibility
4. **Assembly phase** — clip selection and final stitching
5. **Revision phase** — global changes propagated automatically

## Prompt template
```
Create a full {genre} music video synced to this track. {number_of_characters} {character_description}. Visual style: {visual_style_description}. Stop after each step and wait for my approval before continuing.
```

## Example
```
create a full K-pop music video synced to this track
4 girls. Dark luxe -- high fashion, moody, mirrored rooms, deep shadows. Stop after each step and wait for my approval before continuing
```

## Workflow
1. Upload the audio track and send the setup prompt defining genre, characters, and visual style
2. Review and approve character sheets, requesting revisions for consistency
3. Review the agent-generated storyboard mapped to song sections; approve or adjust panel by panel
4. For each scene, review the proposed animation prompt and compute cost before approving generation
5. Select best clips per song section and instruct the agent to stitch the final video
6. Apply global revisions (e.g., outfit changes) with a single prompt; agent propagates updates automatically

## Pro tip
Always include an explicit approval-gate instruction in your very first prompt (`stop after each step and wait for my approval`). Without it, the agent may generate all scenes in one run, locking in early mistakes — like a flawed character design or wrong visual style — across every clip before you have a chance to intervene.

## Tool compatibility
Works with any AI video platform that supports a persistent conversational agent with project memory.
Verified with: invideo AI Agent One, Seedance 2.0, Seedance 2.0 Fast, Nano Banana Pro