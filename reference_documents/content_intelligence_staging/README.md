# Content Intelligence — staging

These pages were produced by the `/ingest-content` pipeline but **could not be
written into the vault**, because the vault lives on a Windows workstation
(`C:\Users\Admin\Documents\Claude\Projects\Content_Intelligence\`) and this run
happened in a remote Linux container with no access to that machine.

## Layout

```
wiki/          14 pages, nothing else — safe to copy wholesale after the
               duplicate check below
raw/youtube/   2 scraper JSON files — safe to copy wholesale
merge/         NOT pages. Entries to merge by hand into the vault's existing
               index.md and log.md. Never copy these into wiki\.
```

`wiki/` and `raw/youtube/` mirror the vault's structure exactly:

```
wiki/*.md          →  Content_Intelligence\wiki\
raw/youtube/*.json →  Content_Intelligence\raw\youtube\
```

`merge/index-entries.md` and `merge/log-entries.md` hold **only this ingest's new
entries**. They were originally named `wiki/index.md` and `wiki/log.md`, which made
a blanket `copy wiki\*.md` overwrite the vault's real index and log with two-video
stubs. They now sit outside `wiki/` so that can't happen.

## Check for duplicates before copying

The pipeline normally reads the vault's `index.md` before creating a page, so an
existing page gets extended rather than duplicated. That check could not run here.

Run this in PowerShell first — it lists which pages the vault already has:

```powershell
$vault = "C:\Users\Admin\Documents\Claude\Projects\Content_Intelligence\wiki"
Get-ChildItem wiki\*.md | Where-Object { Test-Path (Join-Path $vault $_.Name) } |
  Select-Object -ExpandProperty Name
```

Nothing listed → copy all 14 across as-is. Anything listed → do **not** overwrite
those; fold the new material into the existing page and add the new source to its
`sources:` frontmatter list. `Tool_Seedance_2_5.md` is the likeliest collision.

## Other exceptions from this run

- **The manifest step was skipped.** `wiki/ingest_manifest.json` in the vault has
  no record of either video, because updating it needs the vault's current
  contents. Until it's updated, a future `/ingest-content` run has no way to know
  these two sources were already processed. This is step 7 of the skill.
- **Transcripts came from YouTube's auto-captions** via a server-side scrape, not
  the `/watch` skill's Whisper pass — yt-dlp and `/watch` were both unusable in the
  container because YouTube is blocked at its egress proxy. Proper nouns were
  unreliable ("Sea Dance" for Seedance, "SeaArt Dream 5.0" for Seedream 5.0, "Higgs
  Field" for Higgsfield, "Gen-2.5" for Seedance 2.5) and were normalised by hand.
  Timings and figures are as stated by the creators. A local session can re-run
  `/watch` on both URLs to verify quoted prompt text, version numbers, and the
  credit-cost figures.
- **Page frontmatter and tags were never checked against the vault's `CLAUDE.md`.**
  They were written to match its conventions, but that file was not readable from
  the container.

This folder is a transit artifact. Delete it from the repo once the vault copy is
verified.

Ingested 2026-08-19.
