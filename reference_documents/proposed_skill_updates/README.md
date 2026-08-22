# Proposed skill updates

Revisions drafted here for review before being applied to the live skills. These
files are **not** loaded by anything — copy an approved version into the skill's
real source.

The skills concerned are account-synced (`~/.claude/skills/synced/`, each with a
`skillId` in `manifest.json`). A cloud or container session gets a read-only
copy, so nothing here can be applied from one. Apply via Customize in the Desktop
app or claude.ai skill settings, whichever holds the authoritative copy — and
check for stale `.skill` upload packages, which will silently revert a fix if
anyone re-uploads one.

Delete a folder once its revision is live.

## Outstanding

| Folder | Target skills | Status |
|---|---|---|
| `seedance-2-5-rollout/` | seedance2-director, seedance2-composition, storyboard-generator, credit-calculator, higgsfield-generate, chain consumers | Drafted, unreviewed |

## Applied and removed

- **ingest-content** — revision applied to the live skill and both vault `.skill`
  upload packages rebuilt from it (commits 33c86e8, 51c8732).
