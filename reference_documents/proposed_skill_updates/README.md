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
  the lists beside them. The 2026-08-19 log entry claimed 9 pages against a list
  of 10.
- **Step 3 handles `/watch` failing** — tell the user, normalise proper nouns by
  hand, and record transcript provenance in the log rather than passing
  auto-captions off as a real transcript. That run silently produced "Sea Dance"
  for Seedance and "Higgs Field" for Higgsfield.
- **New Step 8 verification** before reporting, including the check that index.md
  and log.md got longer rather than shorter.
- **Completion report** now names any step that did not finish.
