# Claude Movie Director — Skills Index
**Plugin Version:** 1.0.0 | **Author:** Aviation Synergy Co., Ltd. | **Last Updated:** 2026-04-30

## 8 Skills — Complete AI Video Production Pipeline

### Agentic Workflow (NEW — inspired by invideo Agent One)

| Skill | Purpose | Trigger Phrases |
|---|---|---|
| **project-bible** | Persistent character/environment/style memory across sessions | "create a project bible", "define characters", "visual identity", "production context" |
| **ripple-edit** | Change one element → propagate across all clip prompts | "change her hair in every shot", "update all prompts", "global change", "ripple edit" |

### Core Production Skills

| Skill | Purpose | Trigger Phrases |
|---|---|---|
| **music-video-producer** | Full music video production pipeline: intake → shot list → FFmpeg assembly | "music video", "video prompts", "Kling prompts", "lyric video", "sync video to music" |
| **higgsfield-creator** | Higgsfield Cinema Studio 2.5 direction with real optics | "Higgsfield", "cinema studio", "moodboard", "soul cast", "brand video" |
| **seedance2-director** | Seedance 2.0 prompt engineering in viral creator formats | "Seedance", "video prompt", "animate this", "shot list", "cinematic short" |

### Technique Skills (from YouTube Movie Factory)

| Skill | Purpose | Trigger Phrases |
|---|---|---|
| **audio-driven-lip-sync** | Character lip-sync via audio-conditioned video generation | "lip sync", "character speaking", "singing character", "dialogue scene" |
| **multi-shot-camera-coverage** | Multiple camera angles from one reference image | "camera coverage", "multiple angles", "storyboard from image" |
| **style-reference-transplant** | Place character in new environment while preserving visual style | "same style different location", "character transplant", "match color grade" |

## Reference Files

The Higgsfield and Seedance skills include detailed reference files:

- `higgsfield-creator/references/cinema-studio.md` — Camera bodies, lenses, 50+ movements
- `higgsfield-creator/references/prompt-library.md` — Prompt formulas for all Higgsfield tools
- `higgsfield-creator/references/brand-prompts.md` — Aviation Synergy visual language
- `seedance2-director/references/camera-bible.md` — Seedance camera vocabulary
- `seedance2-director/references/prompt-examples.md` — Real viral prompt formats
- `seedance2-director/references/seedance2-capabilities.md` — Model specs and limits

## Project Bible Convention

Each video project should have a `project_bible.json` in its root:

```
Claude_Movie/
├── claude-movie-director/          ← This plugin (skills live here)
├── Amara_2026/
│   ├── project_bible.json          ← Project Bible for Chrome Runway
│   ├── Chrome_Runway_Production_Package.md
│   └── ...
├── Ashes_in_the_orchard/
│   ├── project_bible.json          ← Create one for this project next
│   ├── PRODUCTION_PACKAGE_v3.md
│   └── ...
└── [future projects]/
```

## Installation

To install as a Cowork plugin, add `claude-movie-director/` to your Cowork plugin directory, or reference it from your project's connected folders.
