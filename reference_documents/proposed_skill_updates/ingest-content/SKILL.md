---
name: ingest-content
description: Ingest a single YouTube video (or article URL) into the Content_Intelligence wiki. Runs the full pipeline — scrape metadata, download transcript, create wiki pages (source, tools, techniques, concepts, best practices), update index/log/manifest. Use this skill whenever the user says "ingest this video", "add this to content intelligence", "wiki this", provides a YouTube URL and wants it added to the knowledge base, or mentions adding a source to the Content_Intelligence vault. Also trigger when the user pastes a URL and says "learn from this" or "extract knowledge from this".
---

You are the Content Intelligence Ingest Agent. Your job is to take a single YouTube video (or article) URL and run the full ingest pipeline into the Content_Intelligence wiki.

## The vault

```
VAULT = C:\Users\Admin\Documents\Claude\Projects\Content_Intelligence
```

Every path in this skill is relative to `VAULT`:

| Purpose | Path |
|---|---|
| Conventions and schema | `VAULT\CLAUDE.md` |
| Wiki pages | `VAULT\wiki\` |
| Index | `VAULT\wiki\index.md` |
| Log | `VAULT\wiki\log.md` |
| Manifest | `VAULT\wiki\ingest_manifest.json` |
| Raw scraper output | `VAULT\raw\youtube\` |

## Step 0: Preflight — do this before anything else

The vault lives on a Windows workstation. This skill only works in a session that
can reach that filesystem — a local Claude Code session on that machine. It does
**not** work from a cloud session, a container, or any remote environment.

Check three things, in order, and report the result before doing any other work:

1. **Vault reachable.** Confirm `VAULT\CLAUDE.md` exists and is readable.
2. **Index readable.** Confirm `VAULT\wiki\index.md` exists and read it. You need
   its contents for the duplicate check in Step 4.
3. **Manifest readable.** Confirm `VAULT\wiki\ingest_manifest.json` exists and read
   it. Check whether this URL or video ID is already under `processed_files` — if it
   is, stop and tell the user this source has already been ingested, and ask whether
   they want it re-ingested before continuing.

**If the vault is not reachable, stop.** Do not improvise a destination, do not
write pages somewhere else and carry on as if the pipeline ran. Tell the user:

> This skill writes into the Content_Intelligence vault on your Windows
> workstation, which this session can't reach. Start a local session on that
> machine and re-run, or tell me to run in staging mode.

Only if the user explicitly asks for **staging mode** do you continue without the
vault, and then under these rules:

- Write to a staging folder in the current repository, structured to mirror the
  vault exactly: `wiki/` holding only pages, `raw/youtube/` holding only JSON.
- Put index and log entries in a **separate** `merge/` folder — never as
  `wiki/index.md` or `wiki/log.md`, which makes a bulk copy destroy the vault's
  real files.
- Do not attempt Step 7. The manifest cannot be updated without the vault.
- Write a `README.md` in the staging folder recording: which steps were skipped,
  that the duplicate check in Step 4 could not run, and where each folder is meant
  to land.
- In your completion report, state plainly that this was a partial run and the
  vault has not been updated.

## Pipeline Steps

### Step 1: Extract Metadata
Run the `/content-intelligence-scraper` skill on the provided URL. This extracts:
- Video metadata (title, channel, date, duration, views)
- Description links (tools, repos, templates)
- Pinned comment content
- Top community tips
- Chapter markers
- Tool and topic signals

### Step 2: Save Raw JSON
Save the scraper output to:
```
VAULT\raw\youtube\[video-id].json
```
The filename should be the YouTube video ID (the part after `v=` or the short URL slug).

### Step 3: Get Full Transcript
Run the `/watch` skill on the same URL to download and transcribe the video. This
gives you the full content to analyze — not just metadata but what was actually said
and shown.

**If `/watch` fails** — yt-dlp unavailable, YouTube blocked at an egress proxy, no
Whisper API key — do not silently fall back to scraped auto-captions and proceed as
though nothing happened. Auto-captions mangle exactly the words this vault is about:
model names, tool names, version numbers. If you have no option but to use them:

- Tell the user before you start writing pages.
- Normalise proper nouns by hand and list the corrections you made.
- Record `transcript: auto-captions (unverified)` in the log entry for this ingest.

### Step 4: Analyze & Create Wiki Pages
Read through the transcript and metadata. Identify every significant element:

**For each element, create the appropriate wiki page type:**

| What you find | Page type | Naming convention |
|---|---|---|
| The video itself | Source page | `YT_[Channel]_[Short_Title].md` |
| A tool or platform mentioned | Tool page | `[Domain]_[Tool_Name].md` |
| A workflow or method | Technique page | `Technique_[Name].md` |
| A concept or framework | Concept page | `Concept_[Name].md` |
| A person or channel | Person page | `Person_[Name].md` or `Channel_[Name].md` |
| Actionable advice | Best practice page | `BP_[Short_Name].md` |
| Comparison between tools | Comparison page | `Compare_[X]_vs_[Y].md` |

**Duplicate check — this is a gate, not a suggestion.**

Before writing any page, list every page name you intend to create and check each
one against both `VAULT\wiki\index.md` and the actual contents of `VAULT\wiki\`.
Check the directory as well as the index: a page can exist on disk without being
indexed, and the index is what the old version of this skill trusted alone.

Then, for each name:

- **Not present** → create it.
- **Already present** → do **not** overwrite. Read the existing page, ADD the new
  source to its `sources:` frontmatter, ADD only information that isn't already
  there, and UPDATE the `updated:` date.

Never overwrite an existing page in `VAULT\wiki\`. If you believe a page needs
replacing rather than extending, ask the user first.

Record the split — created vs updated — as you go. Steps 6 and 8 both need it.

**Page format** (follow CLAUDE.md conventions):
```markdown
---
title: Page Title
type: source|tool|technique|concept|person|comparison|best-practice
domain: [ai-coding|ai-image|ai-video|ai-automation]
tags: [relevant, tags]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [[YT_Channel_Title]]
---

# Page Title

[Content]

## Key Takeaways
- Actionable points

## Related Pages
- [[Related_Page]] — relationship description
```

### Step 5: Update Index
Add all new pages to `VAULT\wiki\index.md` under their appropriate category headings.

Append to the existing file. Never rewrite it wholesale, and never write a fresh
`index.md` containing only this ingest's entries. Pages you extended rather than
created are already indexed — don't add them a second time.

### Step 6: Update Log
Append to `VAULT\wiki\log.md`:
```markdown
## [YYYY-MM-DD] ingest | [Video Title]
- Source: [URL]
- Channel: [Channel Name]
- Transcript: whisper | auto-captions (unverified)
- Pages created: [count] — [list page names]
- Pages updated: [count] — [list page names]
- Key topics: [brief summary of what was covered]
```

Both counts must equal the length of the list beside them. Count the names before
you write the number.

### Step 7: Update Manifest
Add the source to `VAULT\wiki\ingest_manifest.json` under `processed_files` with the
video ID, URL, and current timestamp. Read the file first and match the shape of the
existing entries.

This step is what stops the same video being ingested twice months from now. It is
not optional, and it is the step most likely to be quietly dropped when something
earlier in the pipeline goes wrong. If you cannot complete it, say so explicitly in
the completion report — never let it fail silently.

### Step 8: Verify before reporting
Confirm all of the following, and state each one in your report:

- Every page you created exists on disk in `VAULT\wiki\`.
- No pre-existing page was overwritten.
- `VAULT\wiki\index.md` and `VAULT\wiki\log.md` are both **longer** than they were
  before this run. Shorter means you replaced instead of appending — restore them.
- `VAULT\wiki\ingest_manifest.json` now lists this source.
- The raw JSON is in `VAULT\raw\youtube\`.

## Quality Standards

- Every tool mentioned should get its own page (or update an existing one)
- Use [[wikilinks]] for ALL cross-references between pages
- Tag taxonomy must follow CLAUDE.md (domain tags, type tags, platform tags, maturity tags)
- If the video covers a tool you've never seen before, mark it `#emerging` or `#experimental`
- If multiple sources disagree on best practices, document both perspectives
- Note version-specific advice with the version number and date

## Completion Report

When done, report:
- Total pages created and updated, listed by name
- The Step 8 verification results
- Transcript source (Whisper or auto-captions), and any proper nouns you normalised
- Key knowledge extracted (2-3 sentence summary)
- Any gaps or items needing manual review
- Any step that did not complete, and why
