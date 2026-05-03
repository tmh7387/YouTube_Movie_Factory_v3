---
name: content-intelligence-scraper
description: "Extract reusable public resources from a YouTube video's metadata before deeper video analysis. Use when the user asks to analyze this video, analyze a YouTube video, extract prompts/resources from a video, harvest links/comments/chapters, or prepare a video for downstream technical analysis."
metadata:
  version: '1.0'
  author: tmh7387
---

# Content Intelligence Scraper

## When to Use This Skill

Use this skill when the user provides a YouTube URL and asks to analyze the video, prepare for video analysis, extract reusable resources, summarize resources, mine public comments, or capture prompts, templates, links, chapters, or metadata before reviewing the video content itself.

This skill is a Stage 0 resource-harvesting pass. Run it before transcript analysis, visual video analysis, prompt reconstruction, tutorial synthesis, or creation of reusable skill cards from a video.

Do not use this skill for private or authenticated content unless the user explicitly grants access through an available connector or browser session. Do not bypass paywalls, membership gates, private communities, or access controls.

## Objective

Act as a Content Intelligence Scraper. Extract every reusable public resource from the YouTube video's public metadata before the video itself is analyzed.

The output should help later analysis stages understand:

- The creator's own structural map of the video
- External resources linked by the creator
- Corrections, updates, or bonuses in pinned comments
- Community-sourced technical tips
- Public metadata that identifies the video, channel, tools, models, and topic

## Required Inputs

The minimum input is a YouTube video URL. If the user supplies additional context, such as the intended use case, target tool, or desired output format, preserve that context and include it in the final handoff notes.

## Extraction Procedure

### Description Scan

Inspect the video's public description and extract every URL. Include links to:

- Tools and products
- Prompt packs
- Templates
- GitHub repositories
- Notion documents
- Google Drive files or folders
- Discord, Patreon, or community links
- Course pages or landing pages
- Asset downloads
- Related videos or playlists

For each link, record the visible anchor text or surrounding description and infer what the link appears to offer. Use cautious wording when the destination is not opened or cannot be verified.

### Pinned Comment Capture

Check whether the creator has a pinned comment. If present, capture it first because it may include:

- Corrected settings
- Bonus prompts
- Updated links
- Errata
- Clarifications
- Additional files or templates
- Workflow changes after publication

If comment access is unavailable, blocked, disabled, or requires login, state that clearly.

### Top Comment Mining

Review up to the top 50 public comments sorted by Top when accessible. Flag comments that contain:

- URLs
- Prompt text
- Technical tips
- Settings, parameters, seeds, model versions, or workflow corrections
- Tool alternatives
- Creator replies
- Highly upvoted hacks or implementation notes

Prioritize comments with strong evidence of usefulness, such as high upvotes, creator replies, or concrete technical detail. Do not include unrelated opinions, generic praise, or speculation unless they contain actionable information.

### Chapter Marker Extraction

List all available YouTube chapter timestamps and labels verbatim. Preserve the creator's wording because the chapter map is a useful structure for later timestamp anchoring.

If no chapters are present, state that none were found.

### Video Metadata Capture

Capture public metadata when available:

- Title
- Channel name
- Channel URL
- Video URL
- Upload date
- Duration
- View count
- Like count, if visible
- Tags, if visible from public page data or metadata
- Category, if visible
- Language or captions availability, if visible

Do not fabricate unavailable metadata. Use `null`, `unknown`, or a short note explaining the limitation.

### Tool and Topic Signals

From the title, description, tags, chapters, and comments, identify likely tools, models, frameworks, and techniques mentioned. Examples include:

- Veo, Kling, Runway, Higgsfield, Seedance, Sora, Midjourney, ComfyUI, n8n, Blender, CapCut, DaVinci Resolve
- Model versions, workflow names, or feature names
- Prompting methods, camera directives, audio workflow, character consistency methods, reference-image workflows, seed usage, or multi-shot techniques

Flag whether each signal is directly observed in metadata or inferred from context.

## Output Format

Return structured JSON by default unless the user asks for a human-readable summary. Use this schema:

```json
{
  "metadata": {
    "title": "",
    "channel_name": "",
    "channel_url": "",
    "video_url": "",
    "upload_date": "",
    "duration": "",
    "view_count": "",
    "like_count": "",
    "tags": [],
    "category": "",
    "captions_available": "",
    "metadata_limitations": []
  },
  "description_links": [
    {
      "url": "",
      "label_or_context": "",
      "appears_to_offer": "",
      "verified": false,
      "notes": ""
    }
  ],
  "pinned_comments": [
    {
      "author": "",
      "text": "",
      "urls": [],
      "technical_value": "",
      "notes": ""
    }
  ],
  "top_community_tips": [
    {
      "author": "",
      "text": "",
      "upvotes": "",
      "urls": [],
      "tip_type": "",
      "technical_value": "",
      "notes": ""
    }
  ],
  "chapter_map": [
    {
      "timestamp": "",
      "label": ""
    }
  ],
  "tool_and_topic_signals": [
    {
      "signal": "",
      "type": "tool|model|workflow|technique|resource|other",
      "evidence": "",
      "inferred": false
    }
  ],
  "handoff_notes": {
    "recommended_next_analysis": "",
    "important_resources_to_open": [],
    "possible_black_box_leads": [],
    "access_limitations": []
  }
}
```

## Quality Rules

- Preserve exact URLs and timestamps.
- Quote prompt text or settings exactly when visible.
- Separate directly observed facts from inference.
- Never claim a linked resource is free, official, safe, or current unless verified.
- Do not include private personal information beyond what is publicly displayed on the YouTube page.
- Do not download or redistribute paid assets, private files, or membership-only resources.
- If the page, comments, tags, or like counts are unavailable, record the limitation instead of guessing.
- If multiple sources disagree, prefer visible YouTube page metadata over inferred or third-party metadata.

## Handoff to Deeper Video Analysis

After completing this scrape, recommend the next stage based on the user's request:

- For visual tutorial analysis, use the chapter map to anchor video timestamps.
- For prompt reconstruction, pass `description_links`, `pinned_comments`, `top_community_tips`, and `tool_and_topic_signals` into the analysis context.
- For skill-card creation, include extracted resources in the final `Resources Extracted` section.
- For tool-specific workflow synthesis, treat creator comments and pinned corrections as higher-priority than ordinary community comments.

## Example User Requests

- "Analyze this video: https://www.youtube.com/watch?v=..."
- "Before analyzing this tutorial, scrape all links and resources."
- "Extract prompts, templates, comments, and chapters from this YouTube video."
- "Find all reusable resources from this video before we build a workflow."
- "Turn this video into a skill card, starting with metadata and resources."
