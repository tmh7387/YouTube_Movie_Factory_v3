---
title: Build a Prompting Skill from Vendor Docs
type: technique
domain: [ai-video, ai-automation]
tags: [claude-skills, prompt-engineering, seedance, workflow, meta]
created: 2026-08-19
updated: 2026-08-19
sources: [[YT_GenAIwithKeera_1min_AI_Film_2_Prompts]]
---

# Build a Prompting Skill from Vendor Docs

Turn a model vendor's own documentation into a reusable prompting skill, instead
of prompting the model freehand every time.

## The method

1. **Collect the vendor's official material** — the prompt guide *and* the
   worked examples. For Seedance 2.5 that meant reference-to-video, keyframes,
   storyboards, editing and extension.
2. **Ask the LLM to analyse the examples, not summarise the guide.** The
   specific framing used: what information keeps recurring, how are the prompts
   structured, and how can that be turned into a reusable skill? Summarising
   documentation yields prose; analysing examples yields a template.
3. **Refine over several rounds** against real briefs.
4. **Package it as a skill file** so it loads the same way every session.

## Why it beats prompting from scratch

The skill front-loads the interview: it asks the questions that determine the
prompt (which model version, how long, how many clips, what's the idea, what
references exist) before writing anything. That turns a blank box into a
structured intake, and makes the resulting prompts comparable across projects.

It also travels — the same skill file was reported working across Claude,
ChatGPT and Gemini, since it's instructions plus references, not tool calls.

## The general lesson

This is the same pattern the platform's own `seedance2-director` and
`minimax-h3-director` skills follow: encode the vendor's grammar once, then
route briefs through it. When a model ships a new version with a different
grammar, the update is to the skill, not to every prompt.

## Key Takeaways

- Analyse the vendor's *examples*; don't summarise their prose.
- Have the skill interview the user before it writes.
- Version the skill against the model version — grammars change between releases.

## Related Pages

- [[Technique_Storyboard_Before_Video_Credits]]
- [[Tool_Seedance_2_5]]
