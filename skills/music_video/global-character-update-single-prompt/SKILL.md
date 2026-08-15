---
name: global-character-update-single-prompt
description: Applies a visual change — such as an outfit swap, hair color shift, or accessory update — to a recurring character across all scenes in a project by issuing one natural-language prompt to a context-aware agent, which then propagates the change through all relevant character sheets and regenerates affected clips automatically. Use this whenever a character's appearance needs to be revised after clips have already been generated, or when you want to A/B test a visual direction without manually re-prompting every scene. Eliminates the error-prone process of hunting down and individually updating each scene.
---

# Global Character Update via Single Agent Prompt

Propagates a visual change to a recurring character across every scene in a project with one natural-language instruction, rather than manually re-prompting each affected clip.

## When to use
- A character's outfit, hair, or accessory needs to change after clips have already been generated
- You want to A/B test two visual directions for the same character without duplicating work
- A stakeholder or creative director requests a global appearance revision late in production
- You realize early character design decisions are inconsistent with the overall aesthetic

## Core technique
This technique only works when the production pipeline is managed by a stateful agent that holds a **character sheet** — a canonical reference document for each character's appearance. When you issue a global update prompt, the agent:
1. Updates the character sheet with the new visual description
2. Uses the updated sheet as the reference for all subsequent regeneration tasks
3. Identifies which already-generated clips feature that character and queues them for regeneration

The critical enabler is that the agent has project memory — it knows which scenes include the character and can cross-reference the character sheet without you providing that mapping manually. This is why establishing strong, named character sheets at the start of production (during the identity phase) pays dividends at revision time.

## Prompt template
```
I want to see {character_name} in {new_appearance_description} instead of {old_appearance_description} across all {his/her/their} sequences.
```

## Example
```
I want to see the edge in a white leather outfit instead of black across all her sequences.
```

## Workflow
1. Identify the character by their established name and the specific visual element to change
2. Issue the global update prompt, naming the character, the new look, and the old look being replaced
3. Confirm the agent has understood the full scope before it starts generating
4. Review the updated character sheet first — approve it before clips are regenerated
5. Spot-check clips across multiple song sections to verify the change was applied consistently

## Pro tip
Always name your characters explicitly at project setup (e.g., "Edge", "Spark") rather than describing them generically. A named character maps cleanly to a specific character sheet, making global updates unambiguous — the agent knows exactly which clips to update and which to leave alone.

## Tool compatibility
Requires an AI production system with persistent project memory and named character sheet management.
Verified with: invideo AI Agent One