# Skill architecture review — why the updates keep going wrong

Written 2026-08-22, after four attempts to apply the Seedance 2.5 findings ended
up in the wrong file, on the wrong branch, or against a build that does not exist.

The findings are fine. The delivery is broken. This document explains why, and
what a coherent set looks like.

---

## 1. The core problem: two different skill systems share one name

There are **two entirely separate things** called "skills" in this project. They
have overlapping names, different formats, different consumers, and no
relationship to each other. Every session that "updated the skill" picked one of
them, effectively at random.

### System A — Application skills

**Consumer:** the YTMF backend, at runtime.

`backend/app/services/skill_loader_service.py` reads `SKILL.md` files off disk
and injects them into Claude prompts during storyboard and production generation.

```
SKILL_ROOTS = [
    REPO_ROOT / "skills" / "general",
    REPO_ROOT / "skills" / "music_video",
    REPO_ROOT / "skills" / "product_brand",
    REPO_ROOT / "skills" / "asmr",
    REPO_ROOT / ".agent" / "skills",     # legacy fallback
]
```

The contract is exact: `skills/{category}/{slug}/SKILL.md`. Disk skills override
DB rows. **A file not named `SKILL.md` is invisible to the application.**

This is production code. It ships. It is version controlled. It is the thing that
actually affects generated video.

### System B — Assistant skills

**Consumer:** you, in a Claude conversation.

These are the account-synced skills — `seedance2-director`, `ingest-content`,
`credit-calculator` — that you invoke by name in chat. They live in the claude.ai
account, are delivered as `.skill` zip packages, and **cannot be edited from this
machine**. A local edit changes nothing.

They are not version controlled. There is no diff, no history, no merge.

### Why this matters

`seedance2-director` exists in **both systems**, as different files, with
different content, updated by different sessions, in different formats. Neither
knows about the other.

Every confusion in this thread traces back to that.

---

## 2. System A is broken in four places right now

Four skill folders in `skills/general/` cannot be loaded by the application,
because none contains a file named `SKILL.md`:

| Folder | What is actually there | Consequence |
|---|---|---|
| `seedance2-director-v2` | `SKILL (1).md` | **Invisible.** Browser download artifact — the ` (1)` was never renamed. |
| `higgsfield-creator` | `higgsfield-creator.skill` + `references/` | **Invisible.** A zip, not a skill folder. |
| `music-video-producer` | `music-video-producer.md` | **Invisible.** Wrong filename. |
| `claude-movie-director` | `SKILLS_INDEX.md` | **Invisible.** An index, not a skill. |

Eleven of the fifteen skills load. Four do not. Nobody noticed, because nothing
fails loudly — the loader simply returns fewer skills.

### The consequence for this session's work

The model-selection gate and derived-duration rule I wrote on 2026-08-22 went into
`skills/general/seedance2-director-v2/SKILL (1).md`.

**The application has never been able to read that file.** The fix was dead on
arrival. It was never going to affect a single generation.

---

## 3. What already exists that we have been rebuilding

Branch `claude/video-generation-models-q6c3yp` has been sitting unmerged since
2026-08-19 with **three commits that already do much of this work**.

### `9bdda12` — Make the video generation model user-selectable; add Seedance 2.5 and MiniMax H3

22 files, +2350 lines. Among them:

- **Renames `SKILL (1).md` → `SKILL.md`** — fixes the invisibility above.
- Adds `skills/general/seedance2-director-v2/references/seedance2-5-capabilities.md` (213 lines).
- Adds an entire `skills/general/minimax-h3-director/` skill with its own reference.
- Adds `backend/app/services/video_models.py` (338 lines) and rewrites `model_router.py`.
- Adds `skill_loader_service.py` (+115 lines).
- Adds a `video_model` column to production jobs, an API, and a frontend selector.
- Adds `docs/VIDEO_MODEL_SELECTION.md`.

Read that commit title again. **"Make the video generation model user-selectable"**
is the exact request made in this session two turns ago. It was built on 2026-08-19,
end to end, through the database, API and UI — and I rebuilt a worse version of it
by hand, in a file the app cannot load, on a different branch.

### `dbea90b` — Adopt the shot spine and narrative canon layer from Joey's skill files

- Adds `references/shot-spine.md` (182 lines) — the locked 16-slot spine.
- Extends `skills/general/project-bible/SKILL.md` (+73 lines).
- Adds `docs/JOEY_SKILLS_REVIEW.md` (141 lines).

That review documents Joey's `cinema-director-v3`, which:

> Opens with a **target version check** — it refuses to guess between 2.0 and 2.5
> because the reference ceiling (9 vs 50) and runtime ceiling (15s vs 30s) change
> the prompt's architecture, not just its length.

The "ask which model first" pattern was already identified, reviewed and adopted
on 2026-08-19. My `STEP 0.5` reinvented it.

### `b3f3ea0` — Ingest two Seedance 2.5 workflow videos

The staging folder, plus `references/seedance2-5-capabilities.md`.

---

## 4. System B: the live assistant skill

Exported from claude.ai on request:

| | |
|---|---|
| Lines | 533 |
| Dated | 2026-07-24 |
| Contents | `SKILL.md` only — **no reference files** |
| Matches | nothing on disk — a seventh distinct build |

**Correction to my earlier audit.** I reported that `PLATFORM CONSTRAINTS`,
`OUTPUT SETTINGS`, `PROMPT DISCIPLINE RULES` and the "zero memory" wording
appeared zero times, and suggested the drafting session invented them. That was
wrong — I only checked local copies. All four exist in the live build, at lines
420, 408, 438 and 444. The rollout spec read the live skill correctly.
`BUILD-AUDIT.md` still carries that error and needs amending.

**What live gained** that no local build has: R2V and V2V modes, Manifest
Integration, phoneme-sensitive articulation for lip-sync, and the
upstream/downstream map, Higgsfield MCP execution and Mode C all together.

**What live lost** that local builds still have: Seedance native camera controls,
Smart Cuts and cut discipline, the double-contrast cut rule, insert shots,
re-anchoring after cuts, duration calibration, creative principles, and all four
craft rules from the 2026-07-15 upgrade (180° line lock, match cut via last frame,
embedded hard cuts, whip pan discipline).

The July 15 upgrade never reached live. Its `.skill` packages are still sitting in
the vault, unopened.

---

## 5. Root cause

Not "no merge step". That was the symptom. Three causes, in order of severity:

1. **Two systems, one vocabulary.** Nobody states which system they are editing,
   so sessions edit whichever they find first. The repo copy and the account copy
   have drifted into unrelated documents that happen to share a name.

2. **The application fails silently on malformed skills.** `SKILL (1).md` has been
   invisible for an unknown length of time and nothing reported it. There is no
   validation, no startup check, no test.

3. **Work is drafted on branches and never merged.** `q6c3yp` has held the real
   Seedance 2.5 work for three days while two further sessions rebuilt parts of it
   from scratch, unaware.

---

## 6. Target architecture

### Rule 1 — Name the two systems differently, and never confuse them again

| | System A | System B |
|---|---|---|
| Name | **production skills** | **assistant skills** |
| Lives in | `skills/{category}/{slug}/SKILL.md` | claude.ai account |
| Consumed by | YTMF backend at runtime | you, in chat |
| Authoritative copy | **this repo** | this repo, exported to claude.ai |
| Format | `SKILL.md` + `references/` | `.skill` zip |

### Rule 2 — The repo is canonical for both

Per your instruction. Assistant skills get a home in the repo too, so they are
diffable and have history:

```
skills/                       # System A — production, loaded by the app
  general/{slug}/SKILL.md
  music_video/{slug}/SKILL.md

assistant_skills/             # System B — canonical source for claude.ai
  {slug}/SKILL.md
  {slug}/references/*.md
  {slug}/.build/{slug}.skill  # generated package, for upload
```

Nothing is edited anywhere else. The vault and the account are both **downstream
copies**, refreshed from the repo, never edited in place.

### Rule 3 — One-way sync, with a record

```
repo (edit here)
  ├─→ assistant_skills/{slug}/.build/{slug}.skill  → upload to claude.ai
  └─→ vault copy                                   → refreshed after every repo change
```

A `SYNC_LOG.md` records, for each push: skill, version, date, destination. That is
the process you asked for. Multiple copies stop being a problem the moment there is
a record of which one is current.

### Rule 4 — Make the app fail loudly

Add a validation step that lists every folder under `SKILL_ROOTS` without a
loadable `SKILL.md`, and fails a test. Four skills have been silently missing;
that must not be possible again.

---

## 7. Plan, in order

**Nothing new should be written until step 3 is done.**

| # | Step | Blocked on |
|---|---|---|
| 1 | Merge `q6c3yp` into `main`. It fixes the `SKILL (1).md` rename, adds the 2.5 capabilities reference, the shot spine, the MiniMax H3 skill and the whole user-selectable model path. | your approval |
| 2 | Fix the other three invisible skills — `higgsfield-creator`, `music-video-producer`, `claude-movie-director`. | — |
| 3 | Add the loader validation test from Rule 4. | — |
| 4 | Re-read the merged `seedance2-director-v2/SKILL.md` and diff it against the 2.5 findings. Establish what is genuinely still missing, rather than assuming. | 1 |
| 5 | Stand up `assistant_skills/`, seed it with the live 7/24 export as the baseline. | — |
| 6 | Merge the lost craft content back into the assistant skill — the July 15 rules and the cut discipline sections. | 5 |
| 7 | Apply whatever of the 2.5 rollout is genuinely outstanding after step 4, to both systems. | 4, 6 |
| 8 | Write `SYNC_LOG.md` and the sync script. | 5 |
| 9 | Retire the duplicate copies once the canonical path works. | 8 |

### What to discard

- My `STEP 0.5` edit to `SKILL (1).md`. Superseded by `q6c3yp`, and in an
  unloadable file. **Do not merge PR #3's skill changes** — take the branch's
  documentation and drop the skill edit.
- `APPLY-ONLINE-PROMPT.md` as currently written. It targets System B, describes
  System A's file layout, and instructs work that step 4 may show is already done.
  Rewrite after step 4.
- `reference_documents/Content_Intelligence_ingest_20260819/` — untracked, and a
  third copy of pages already landed in the vault. Delete once confirmed.

---

## 8. My errors in this session, for the record

1. Patched `SKILL (1).md` without checking whether the application could load it.
   It cannot.
2. Never checked `claude/video-generation-models-q6c3yp`, despite the original
   handover naming it. Rebuilt work that already existed there.
3. Audited only local copies, then reported that the rollout spec described
   sections that "do not exist". They exist in the live build.
4. Wrote three versions of a handover prompt against an unknown baseline instead
   of establishing the baseline first.

The pattern in all four: acting before establishing what was actually there.
