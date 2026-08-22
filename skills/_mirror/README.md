# Mirroring skills to claude.ai

There is **one** skill set. It lives in `skills/`. It has two delivery targets.

```
skills/{category}/{slug}/SKILL.md          ← the only source of truth
        │
        ├──▶ YTMF app          SkillLoaderService reads these off disk and
        │                      injects them into generation prompts over API.
        │                      Provider-agnostic — the skill body is plain
        │                      Markdown, not tied to any one LLM.
        │
        └──▶ claude.ai account packaged as a .skill zip and uploaded, so
                               working outside the app produces the same
                               output quality as working inside it.
```

Both targets get the **same content**. Differences between them are limited to
packaging and to genuinely pipeline-specific detail (the app resolves model ids
through `video_models.py`; a chat session does not). Nothing that changes what a
prompt says may differ between the two.

## This directory is machinery, not source

```
skills/_mirror/
  README.md                       # this file
  SYNC_LOG.md                     # what was pushed where, and when
  exports/{slug}/SKILL-<date>.md  # pulled DOWN from claude.ai — evidence only
  build/{slug}.skill              # generated packages, for upload
```

`_mirror/` is not scanned by `SkillLoaderService` — `SKILL_ROOTS` covers
`skills/general`, `skills/music_video`, `skills/product_brand` and `skills/asmr`
only. Nothing here is ever loaded as a skill.

`exports/` records what the account actually held at a point in time, so a push
can be diffed against it first. **Never edit an export.** It is a receipt.

## Direction of travel

**Normal case — repo first.**

1. Edit `skills/{category}/{slug}/SKILL.md` and its references. Commit.
2. Build `_mirror/build/{slug}.skill`.
3. Upload via claude.ai skill settings, or Customize in the Desktop app.
4. Record it in `SYNC_LOG.md`: slug, date, commit sha, target.
5. Refresh the Content_Intelligence vault copy from the same commit.

**Exception — something is born online, or in the wiki.**

A skill tested in a chat session, or a technique ingested into the
Content_Intelligence wiki, is allowed to exist there first. It becomes real when
it lands in the repo:

1. Export it from claude.ai into `_mirror/exports/{slug}/SKILL-<date>.md`.
2. Diff it against `skills/{category}/{slug}/SKILL.md`.
3. Review, then fold the new material into the repo copy.
4. Publish back out per the normal case, so both sides match again.

The rule is not "the repo is edited first". The rule is **the repo is where a
change becomes canonical**, and nothing stays divergent past review.

## Why this exists

Before this, `seedance2-director` had drifted into seven builds across the
workstation, the vault and the account, with no record of which was current. The
cause was that every session read whichever copy it found, improved it, and ended
with "upload this manually" — and nobody wrote down what was uploaded.

`SYNC_LOG.md` is the fix. One line per push. A copy with no log entry is not
trusted.

See `docs/SKILL_ARCHITECTURE_REVIEW.md` for the full history.

## Current status

| Skill | Repo master | Last export | Mirrored |
|---|---|---|---|
| `seedance2-director-v2` | complete as of 2026-08-22 | 2026-07-24 | pending |
| `minimax-h3-director` | complete | — | pending |
| others | see `SYNC_LOG.md` | | |

Three skill folders still carry no loadable `SKILL.md` and are invisible to the
app: `higgsfield-creator`, `music-video-producer`, `claude-movie-director`. They
are tracked as follow-ups in `docs/REVIEW_video-generation-models-q6c3yp.md`.
