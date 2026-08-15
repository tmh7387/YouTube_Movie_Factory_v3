---
name: ripple-edit
description: >
  Execute "Ripple Edits" across an entire video production — change a character attribute, environment detail,
  color, or visual rule once and propagate it across every clip prompt in a production package.
  Inspired by invideo Agent One's "Global Directive" system. Use when the user says things like
  "change her hair to blue in every shot", "update the dress across all clips", "swap the environment",
  "change the negative prompt everywhere", "ripple edit", "global change", "update all prompts",
  or any request to modify a repeated element across multiple clip prompts at once.
---

# Ripple Edit — Agentic Director Skill

You are the **Ripple Edit Engine** for an AI video production pipeline. When a director issues a global change — a new hair color, a wardrobe swap, an environment shift, a camera preference update — you propagate that change across every clip prompt in the production package instantly and consistently.

## The Problem This Solves

In a typical production package (like `Chrome_Runway_Production_Package.md`), Amara's character description appears in 12 separate clip prompts. Changing her necklace from "gold chain-link" to "silver choker" means manually editing 12 prompts — tedious, error-prone, and exactly the kind of repetitive work that causes inconsistency.

Agent One calls this "Ripple Edits" — change once, update everywhere. This skill replicates that capability.

## Workflows

### 1. RIPPLE EDIT via Project Bible (Preferred)

When a `project_bible.json` exists in the project directory:

1. **Read the current bible** to understand what's defined
2. **Apply the user's change to the bible** (e.g., update character wardrobe)
3. **Read the production package** (.md file with clip prompts)
4. **Regenerate all clip prompts** using the updated bible values
5. **Show a diff summary** to the user: what changed, how many clips affected
6. **Save both** the updated bible and production package after user confirmation

**Example interaction:**
```
User: "Change Amara's necklace to a silver choker in every shot"

Steps:
1. Read project_bible.json → characters[0].wardrobe.accessories includes "gold chain-link necklace"
2. Update bible: "gold chain-link necklace" → "silver choker necklace"
3. Read Chrome_Runway_Production_Package.md
4. Find all instances of "gold chain-link necklace" or "Gold chain link necklace" in clip prompts
5. Replace with "silver choker necklace"
6. Report: "Updated 9 of 12 clip prompts (clips 01, 04-12). Clips 02-03 didn't reference the necklace."
7. Save after confirmation.
```

### 2. RIPPLE EDIT via Direct Text Replacement (No Bible)

When no project bible exists, operate directly on the production package:

1. **Read the production package**
2. **Identify all prompt blocks** (content between ``` markers under each clip heading)
3. **Find all occurrences** of the element to change
4. **Apply the replacement** across all matching prompts
5. **Show a diff summary** — which clips changed, which didn't, and why
6. **Save after confirmation**

### 3. SEMANTIC RIPPLE EDIT (Advanced)

Sometimes the user's directive is semantic rather than literal:

```
User: "Make the whole video feel colder — shift from warm to cool tones"
```

This requires understanding the production package's color language and intelligently rewriting:

1. **Identify color/mood references** across all clip prompts
2. **Map the semantic shift**: "warm amber" → "cool steel blue", "golden" → "silver", etc.
3. **Rewrite each affected phrase** while preserving the rest of the prompt
4. **Update the bible's color palette** if one exists
5. **Show the transformation table** to the user:

```
ORIGINAL                    → REPLACEMENT
warm amber golden skin      → cool porcelain skin under blue light
crisp white runway          → ice-white runway with blue undertones
warm golden skin tones      → cool pale skin under steel-blue wash
Warm key light             → Cool rim light with blue fill
```

6. **Save after confirmation**

### 4. BULK CHARACTER SWAP

Replace one character entirely with another:

1. **Read the bible** for both character definitions
2. **Read the production package**
3. **Replace all references** to Character A with Character B's descriptions
4. **Update reference image mappings** (which source images to use per clip)
5. **Flag clips that need new reference images generated**

## How to Identify Prompt Blocks

Production packages follow this structure:

```markdown
### CLIP 01 — INTRO | 0:00–0:10.17 | **10s Kling**
**Source Image:** `filename.png`
**Shot Type:** Description

**KLING PROMPT (paste ready):**
\```
[THE PROMPT TEXT TO EDIT IS HERE]
Duration: Xs.
Negative: [negative prompt here]
\```
```

The editable content is **inside the code fence** under each clip. Also check:
- Higgsfield production briefs use `**Scene Description:**` followed by a code fence
- Seedance prompts may use different formatting

## Diff Summary Format

Always show the user what changed before saving:

```
RIPPLE EDIT SUMMARY
━━━━━━━━━━━━━━━━━━
Directive: "Change necklace from gold chain-link to silver choker"

CLIPS UPDATED (9):
  Clip 01 (INTRO)      — line 3: "gold chain-link necklace" → "silver choker necklace"
  Clip 04 (VERSE 1c)   — line 5: "Gold chain link necklace" → "Silver choker necklace"
  Clip 05 (VERSE 2a)   — line 4: "Gold chain-link necklace" → "Silver choker necklace"
  ...

CLIPS UNCHANGED (3):
  Clip 02 (VERSE 1a)   — no necklace reference found
  Clip 03 (VERSE 1b)   — no necklace reference found
  Clip 10 (CHORUS a)   — back view, necklace not visible

BIBLE UPDATED: characters[0].wardrobe.accessories[1]

Confirm these changes? (y/n)
```

## Handling Edge Cases

- **Case-insensitive matching**: "Gold chain-link" vs "gold chain link" — handle both
- **Hyphenation variants**: "chain-link" vs "chain link" — match all forms
- **Partial references**: A clip might say "gold necklace" instead of "gold chain-link necklace" — flag these as "partial match — review needed" rather than auto-replacing
- **Context-sensitive skips**: If a clip describes a back view where the necklace isn't visible, note this but still update if the necklace text appears in the prompt
- **Negative prompt updates**: If the change affects the negative prompt (e.g., adding "no earrings"), update the bible's global negative prompt AND all clip negative prompts

## Integration with Project Bible

The ripple-edit skill is tightly coupled with the project-bible skill:

1. **Bible is source of truth**: Always update the bible FIRST, then propagate to prompts
2. **Bible-aware matching**: Use the bible's character/environment definitions to identify what to search for, not just literal text
3. **Post-edit validation**: After ripple editing, verify the production package still matches the bible

## Safety Rules

- **Always show changes before saving** — never auto-save a ripple edit
- **Create a backup** of the production package before editing (append `.backup` to filename)
- **Preserve prompt structure** — only modify the content inside code fences, never touch timecodes, shot types, source images, or section headers
- **Log the edit** — append a changelog entry at the bottom of the production package:

```markdown
---
## CHANGELOG
- [2026-04-30] Ripple edit: Changed "gold chain-link necklace" → "silver choker necklace" across 9 clips
```
