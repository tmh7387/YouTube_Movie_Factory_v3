# Video Production Skills Repository

This directory is the global skills repository for YouTube Movie Factory.

Each skill is a tool-agnostic, reusable production technique synthesized from
AI video tutorial analysis. Skills are created automatically when tutorials are
ingested via `POST /api/knowledge/ingest`.

## Structure

```
skills/
├── general/           # Techniques applicable across all video types
├── music_video/       # Beat-sync, mood-to-visual, lyric treatment, etc.
├── product_brand/     # Product prompting, brand consistency, lifestyle context
└── asmr/              # Texture prompts, macro framing, satisfying loops
```

Each skill lives in its own directory:

```
skills/{category}/{skill-slug}/
└── SKILL.md           # Frontmatter (name, description) + skill body
```

## Skill format

Skills follow the Antigravity Kit SKILL.md format:

```markdown
---
name: skill-slug
description: What the skill does and when to use it. 2-4 sentences.
---

# Skill Name

One-line summary of what this technique achieves.

## When to use
## Core technique
## Prompt template
## Example
## Workflow
## Pro tip
## Tool compatibility
```

## Usage in production

The curation pipeline queries skills via `GET /api/skills?category=music_video`
and injects relevant techniques into Claude's storyboard generation prompt,
ensuring every production benefits from accumulated tutorial knowledge.
