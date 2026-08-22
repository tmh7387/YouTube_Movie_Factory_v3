# Review — `claude/video-generation-models-q6c3yp`

Reviewed 2026-08-22. Three commits, 44 files, +3728 / −130, unmerged since 2026-08-19.

**Verdict: merge it.** It is better than what this session built by hand, and it
fixes a skill that the application has never been able to load. Four follow-ups
are needed after the merge; one of them is the duration bug that started this
whole thread and it survives on this branch.

---

## What the branch contains

| Commit | Scope |
|---|---|
| `9bdda12` | Video model registry, router rewrite, skill loader, DB migration, API, UI selector, MiniMax H3 skill |
| `b3f3ea0` | The two-video ingest staging folder + a 2.5 capabilities reference |
| `dbea90b` | Joey's 16-slot shot spine, project-bible extension, skills review doc |

---

## What it gets right

### `video_models.py` — one registry, three concerns kept apart

The file states its own discipline up front, and holds to it:

> `capability` — what the model can do · `routing` — what kind of scene it is good
> at · `transport` — which backend runs it

Adding a model is one registry entry plus, only if it speaks a new API, one
adapter. That replaces name-sniffing scattered across `model_router`,
`tasks/production.py` and `media_gen_service`.

### The Seedance 2.5 entry already encodes the ingest findings

```python
"dreamina-seedance-2-5": VideoModel(
    max_duration=30,
    modes=(T2V, I2V, FL2V, R2V, EDIT, EXTEND),
    max_reference_images=30, max_reference_videos=10, max_reference_audio=10,
    supports_timestamps=True,
    notes="Editing/extension tasks lock ratio (must send ratio=adaptive) and "
          "editing also locks duration (send -1); prefer output_format=mov ...",
)
```

The 30s ceiling, the 50-asset limit, integer timestamps and the locked-parameter
rules are all here — the same facts the rollout spec was going to add by hand.

### Duration is bounded, not chosen

```python
def clamp_duration(model, duration):
    return max(model.min_duration, min(model.max_duration, int(duration)))
```

It constrains a *requested* duration to what the model accepts. That is the right
shape: the ceiling bounds, it does not decide. (What actually gets requested is
the problem — see Finding 1.)

### The skill loader branches on dialect, not on name

`DIALECT_SKILL_MAP` maps `seedance-2.0` / `seedance-2.5` / `minimax-h3` to skill
slugs, so a new director skill declares its dialect rather than being
string-matched. It also carries the alias `seedance2-director → seedance2-director-v2`,
resolving the folder-name drift.

### It makes the skill loadable for the first time

`SKILL (1).md` → `SKILL.md`. Until this lands, `SkillLoaderService` cannot see
this skill at all.

### Its version routing is better than mine

The branch's `STEP 0.5 — VERSION ROUTING` does what my version did, plus an
inference table for when the user does not know, plus the grammar difference:

> **2.0** → `SHOT 1 / SHOT 2 …`, `@image1` bindings, no clock times.
> **2.5** → timestamped intervals, asset bindings by upload order, explicit role
> for every asset, locked-parameter rules if the task edits or extends.
>
> **Never mix them.** A 2.0 prompt with timestamps loses the timing silently; a
> 2.5 prompt that omits asset bindings produces character drift.

And `shot-spine.md` already states the derived-duration principle, more sharply
than I did:

> **Runtime available is not runtime required.**

### Small things done properly

`resolve()` falls back to the default rather than raising, so a stale model id on
an old scene row cannot take down a production run. `is_configured()` reports
per-transport credential state to the UI instead of failing at call time.

---

## Findings

### 1. The pipeline still hardcodes a 5-second duration — CONFIRMED

`backend/tasks/production.py:330`

```python
res = await media_gen_service.animate_image(
    ...
    duration=video_models.clamp_duration(spec, 5),
)
```

Every scene animates at **exactly 5 seconds**, on every model. `clamp_duration`
does its job — 5 is inside 4-30 — so nothing corrects it.

`production_scenes.duration_seconds` **exists in the schema** and is never read
when animating. `media_gen_service.animate_image` also defaults `duration: int = 5`.

So the registry knows Seedance 2.5 can do 30 seconds, the skill knows runtime
should follow the scene, and the pipeline asks for 5 regardless. This is the same
defect as the flat 15-second ceiling, one layer down: a constant where a derived
value belongs.

**This is the item to fix after the merge.** Read `scene.duration_seconds`, fall
back to a sensible default only when it is null, and clamp that.

### 2. A per-15-second figure survives in the skill

`skills/general/seedance2-director-v2/SKILL.md:364`

> **Dialogue word budget:** ~25-30 spoken words fit into 15 seconds of Seedance video.

Breaks silently at 30s. Should be a rate — roughly 2 spoken words per second —
budgeted against the shot's actual runtime.

### 3. Seedance 2.5 ships as `status="preview"`

It routes over `TRANSPORT_BYTEPLUS_ARK` and `is_configured()` requires
`ARK_API_KEY`. Until that key is set, 2.5 appears in the UI but cannot run. That
is correct behaviour — just know that merging does not by itself make 2.5 usable.

### 4. The merge resurrects a deleted folder

`b3f3ea0` adds `reference_documents/content_intelligence_staging/`. `main`
deliberately deleted that folder in `33c86e8` once the pages were landed in the
vault. The merge brings back **19 files**.

Needs a delete commit immediately after the merge. Same for the untracked
`reference_documents/Content_Intelligence_ingest_20260819/`, which is a third
copy of the same pages.

### 5. It fixes one invisible skill, not four

`seedance2-director-v2` becomes loadable. These remain invisible to
`SkillLoaderService`:

- `higgsfield-creator` — a bare `.skill` zip, no `SKILL.md`
- `music-video-producer` — file named `music-video-producer.md`
- `claude-movie-director` — only `SKILLS_INDEX.md`

### 6. No test guards the loader contract

Nothing fails when a skill folder has no `SKILL.md`. That is how `SKILL (1).md`
survived. A test listing every folder under `SKILL_ROOTS` without a loadable
`SKILL.md` would have caught it on the day it appeared.

---

## Merge mechanics

`git merge-tree` against **current `origin/main`**: **conflict** in
`skills/general/seedance2-director-v2/SKILL.md` — main carries this session's
model-gate edit in `SKILL (1).md`, the branch renames and rewrites the same file.

`git merge-tree` against **this branch after `873effb`** (which reverts that
edit): **clean, zero conflicts.**

So: land the revert first, then merge. Do not resolve that conflict by hand —
the branch's version wins on every point.

---

## Recommended order

1. Merge the revert (`873effb`) into `main`.
2. Merge `q6c3yp` into `main`. Clean.
3. Delete the resurrected `content_intelligence_staging/` and the untracked
   `Content_Intelligence_ingest_20260819/`.
4. **Fix Finding 1** — read `scene.duration_seconds` instead of the constant 5.
5. Fix Finding 2 — the word budget becomes a rate.
6. Fix Finding 5 — the three remaining invisible skills.
7. Add Finding 6's loader test.
8. Only then re-diff the merged skill against the 2.5 findings to see what, if
   anything, is genuinely still missing. Most of it is already here.
