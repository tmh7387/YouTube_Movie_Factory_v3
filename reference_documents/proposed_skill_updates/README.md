# Proposed skill updates

Revisions drafted here for review before being applied to the live skill. These
files are **not** loaded by anything — copy an approved version into the skill's
real source.

## ingest-content

`~/.claude/skills/synced/ingest-content/SKILL.md` on the Windows workstation. The
`synced/` path means it comes from the claude.ai account, so a local edit may be
overwritten on the next sync — check where the authoritative copy lives (Customize
in the Desktop app, or claude.ai skill settings) and apply it there.

### Why

The 2026-08-19 ingest of two Seedance 2.5 videos ran in a cloud container that
could not reach the vault. The skill has no precondition on the vault existing, so
instead of stopping it improvised: pages were written to a repo staging folder,
and steps 5-7 (index, log, manifest) silently did not happen against the vault.
The manifest still has no record of either video, so a future run has no way to
know they were processed.

Three failure modes, all still live:

1. **No vault precondition.** Any cloud session running this skill fails the same
   way. Nothing checks the vault is reachable before work starts.
2. **De-duplication was advisory.** "Check if it already exists in `wiki/index.md`"
   sat under Step 4 as a note, and it trusted the index alone — a page can exist on
   disk without being indexed.
3. **Manifest is the last step and the easiest to drop.** Nothing verifies it ran.

### What changed

- **New Step 0 preflight.** Verifies the vault, index, and manifest are reachable
  and readable, and checks whether the URL was already ingested. Hard-stops with a
  clear message when the vault is unreachable, instead of improvising a
  destination. Adds an explicit opt-in "staging mode" so a degraded run is
  predictable — mirrored folder structure, index/log entries kept in a separate
  `merge/` folder so a bulk copy can't destroy the vault's real files, and a
  README recording what was skipped.
- **`VAULT` defined once** at the top with a path table, instead of the same
  Windows path hardcoded into five separate steps.
- **De-duplication is now a gate**, checked against the directory as well as the
  index, with an explicit never-overwrite rule and ask-first escalation.
- **Steps 5 and 6 say append, not replace**, and require the page counts to match
  the lists beside them. (Correction, 2026-08-20: the review of this proposal
  re-counted the 2026-08-19 log entries and both counts were in fact correct —
  10 claimed against 10 listed, and 4 against 4. The append-not-replace rule stands
  on its own; the count rule is cheap insurance rather than a fix for an observed
  fault.)
- **Step 3 handles `/watch` failing** — tell the user, normalise proper nouns by
  hand, and record transcript provenance in the log rather than passing
  auto-captions off as a real transcript. That run silently produced "Sea Dance"
  for Seedance and "Higgs Field" for Higgsfield.
- **New Step 8 verification** before reporting, including the check that index.md
  and log.md got longer rather than shorter.
- **Completion report** now names any step that did not finish.

### Added after review (2026-08-20)

Three gaps in the draft, all of which this ingest actually hit:

- **The duplicate gate compared filenames, not subjects.** It would not have caught
  the drafted `Tool_Nano_Banana_Pro` against the vault's existing `Tool_NanoBananaPro`.
  Step 4 now requires a subject-level match and lists the variant forms to check
  (spacing, case, prefix, alternate product names), while keeping genuine version
  differences — Seedance 2.5 vs 2.0 — as separate pages.
- **Nothing required the new pages to link into the existing vault.** All 14 drafted
  pages linked only to each other. Step 4 now requires at least one wikilink from each
  new page to a page that predates the ingest, and Step 8 verifies it.
- **The naming table still gave `[Domain]_[Tool_Name].md` for tool pages.** The vault
  runs 26 `Tool_*` pages against 3 `Video_*`, and that split already produced the
  `Tool_Seedance_2.0` / `Video_Seedance_2` duplicate the manifest flags. The table now
  says `Tool_[Tool_Name].md` and notes that `CLAUDE.md` is the stale one.

### Where the live skill actually lives

Not on the workstation. There is no `~/.claude/skills/synced/` directory and no
`ingest-content/SKILL.md` anywhere under the user's home. The only local copies are
two zip archives of the May 2026 build — `Content_Intelligence/ingest-content.skill`
and `Content_Intelligence/skills/ingest-content.skill` — which are upload packages,
not the running source. The skill is served from the claude.ai account, so the
approved file has to be pasted in via claude.ai Settings → Capabilities → Skills. A
local file edit would change nothing.
