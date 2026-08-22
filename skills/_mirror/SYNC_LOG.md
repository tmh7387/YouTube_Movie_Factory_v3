# Sync log

One line per upload to claude.ai. **A copy with no entry here is not trusted.**

This exists because `seedance2-director` drifted into seven divergent builds
across the workstation, the vault and the account, and nothing recorded which was
current. Every upgrade session read whichever copy it found, improved it, and
ended with "upload this manually" — with no record of whether anyone did.

## How to add a row

```bash
python skills/_mirror/build_skill.py <repo-folder> [--as <account-slug>]
```

Upload the resulting `.skill` through claude.ai skill settings or Customize in
the Desktop app, then add a row with the commit sha the package was built from.

| Date | Skill | Built from | sha256[:12] | Uploaded | Notes |
|---|---|---|---|---|---|
| 2026-08-22 | `seedance2-director` | *(pending commit)* | `(rebuilt — see below)` | ☐ | First mirror after completing the master. 915 lines + 5 references. Replaces the 2026-07-24 account build, which had 532 lines and no references. Description trimmed 1130 -> 876 chars to fit the 1024 platform limit; all 31 trigger phrases kept, including `storyboard mode` and `bridge to video` recovered from the live export. |
| 2026-08-22 | `higgsfield-creator` | *(pending commit)* | `856a11c62ae9` | ☐ | Unpacked from the stale in-folder zip so the app can load it. Content unchanged. |
| 2026-08-22 | `music-video-producer` | *(pending commit)* | `0c14adb595ed` | ☐ | Renamed to `SKILL.md` so the app can load it. Content unchanged. |

Tick the Uploaded box and fill in the commit sha once each upload is done.

## Exports pulled down

Recorded in `exports/{slug}/` as evidence of what the account actually held, so a
push can be diffed before it overwrites anything. Never edited.

| Date | Skill | Lines | Note |
|---|---|---|---|
| 2026-07-24 | `seedance2-director` | 532 | Exported 2026-08-22. A seventh distinct build — matched no copy on the workstation. Its content is folded into the master. |

## Not mirrored

`claude-movie-director` is not a skill. It is a plugin manifest listing eight
skills that live elsewhere in `skills/general/`. Moved to
`plugins/claude-movie-director/` on 2026-08-22 so it stops presenting as a broken
skill folder.
