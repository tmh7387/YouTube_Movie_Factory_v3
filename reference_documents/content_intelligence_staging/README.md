# Content Intelligence — staging

These pages were produced by the `/ingest-content` pipeline but **could not be
written into the vault**, because the vault lives on a Windows workstation
(`C:\Users\Admin\Documents\Claude\Projects\Content_Intelligence\`) and this run
happened in a remote Linux container with no access to that machine.

They follow the vault's conventions (frontmatter, naming, `[[wikilinks]]`) so
they can be moved across as-is:

```
wiki/*.md          →  Content_Intelligence\wiki\
raw/youtube/*.json →  Content_Intelligence\raw\youtube\
```

`wiki/index.md` and `wiki/log.md` here contain **only the new entries** from
this ingest — merge them into the vault's existing files rather than replacing
them. The manifest step (`wiki/ingest_manifest.json`) was skipped for the same
reason: it needs the vault's current contents to append to.

Two more caveats worth knowing before merging:

- **No de-duplication was possible.** The pipeline normally checks
  `wiki/index.md` before creating a page, so an existing page gets extended
  rather than duplicated. That check couldn't run. Check each page against the
  vault before copying; if one already exists, fold the new material in and add
  the source to its `sources:` list instead of overwriting.
- **Transcripts came from YouTube's auto-captions** via a server-side scrape,
  not from the `/watch` skill's Whisper pass, so proper nouns are unreliable
  ("Sea Dance" for Seedance, "SeaArt Dream 5.0" for Seedream 5.0, "Higgs Field"
  for Higgsfield, "Gen-2.5" for Seedance 2.5). Names have been normalised in
  these pages; timings and figures are as stated by the creators.

Ingested 2026-08-19.
