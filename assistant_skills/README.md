# Assistant skills — canonical source

Skills you invoke **in a Claude conversation** (`seedance2-director`,
`ingest-content`, `credit-calculator`, …). They are delivered to claude.ai as
`.skill` zip packages.

This directory is their canonical source. Nothing is edited in claude.ai
directly — an edit made there is invisible to git and will be overwritten by the
next publish.

**Do not confuse these with `skills/`.** That directory holds *production*
skills, which the backend loads at runtime via `SkillLoaderService` and injects
into generation prompts. Same names, different consumers, different content. See
`docs/SKILL_ARCHITECTURE_REVIEW.md`.

## Layout

```
assistant_skills/{slug}/
  SKILL.md              # canonical body — edit this
  references/*.md       # canonical references
  _live_export/         # what was last pulled DOWN from claude.ai, for diffing
  .build/{slug}.skill   # generated package, for upload
```

`_live_export/` is evidence, not source. It records what the account actually had
at a point in time, so a publish can be diffed against it before it overwrites
anything. Never edit it.

## Current state

| Skill | Canonical `SKILL.md` | Live export | Status |
|---|---|---|---|
| `seedance2-director` | not yet written | 2026-07-24, 532 lines | **reconciliation pending** |

### Why `seedance2-director` has no canonical body yet

The repo's production master (`skills/general/seedance2-director-v2/SKILL.md`,
600 lines) and the live assistant build (532 lines) are **complementary, not
versions of each other**. Neither is a superset.

Present in the production master, absent from live:

- `STEP 0.5` version routing (2.0 vs 2.5)
- `references/shot-spine.md` — the 16-slot spine
- `references/seedance2-5-capabilities.md`
- `DURATION CALIBRATION`
- Smart Cuts and cut discipline
- Seedance native camera controls
- Whip pan discipline
- Creative principles

Present in live, absent from the production master:

- `UPSTREAM / DOWNSTREAM SKILL MAP`
- `HIGGSFIELD MCP EXECUTION`
- `MODE C` — storyboard-driven
- `OUTPUT SETTINGS`
- `PLATFORM CONSTRAINTS`
- `PROMPT DISCIPLINE RULES` (four rules, incl. phoneme articulation)
- `Manifest Integration`
- R2V and V2V modes

**Publishing the production master as-is would delete eight feature areas from
the live skill.** That is the same silent loss that produced seven divergent
builds in the first place. The reconciliation has to happen here, in git, before
anything is published.

See `RECONCILE-PROMPT.md` in this folder for the instruction that performs it.

## Publish process

1. Edit `assistant_skills/{slug}/SKILL.md` and its references. Commit.
2. Build `.build/{slug}.skill`.
3. Upload via claude.ai skill settings, or Customize in the Desktop app.
4. Record it in `SYNC_LOG.md` — skill, date, commit sha, destination.
5. Refresh the Content_Intelligence vault copy from the same commit.

The vault and the account are both downstream. Neither is ever the source.
