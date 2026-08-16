# Functional Wiring Pass — implementation brief for Claude Code

**Repo:** `github.com/tmh7387/YouTube_Movie_Factory_v3`
**Base commit:** `77764fb` on `main`
**Branch to create:** `wiring/functional-pass`
**Prepared:** 16 August 2026

---

## 0. Read this first

This is a **wiring pass**, not a feature build. Every capability below already exists in the repo as written, tested-in-isolation code that nothing calls. Your job is to connect it, prove it runs, and add the guards that stop it silently disconnecting again.

**Prime directive:** prefer wiring existing code over writing new code. If you find yourself authoring a new service, stop and check whether one already exists unimported.

**Hard constraints**

- Do not refactor `backend/tasks/production.py` wholesale. Add to it surgically. A previous merge lost work exactly this way.
- Do not rename database columns. A prior migration (`d1e2f3a4b5c6`) already reconciled `kling_*` → `animation_*`; leave that settled.
- Do not change the Alembic chain topology. Current single head is `d1e2f3a4b5c6`. New migrations append to it.
- Do not touch `gamma_deck_toolkit/`, `skills/` content (filenames only — see Item 1), `reference_documents/`, or `prior_versions/`.
- Keep both feature flags (`STEM_SEPARATION_ENABLED`, `UPSCALING_ENABLED`) defaulting to `false`.

**Definition of done for the whole pass:** all four gates in §8 pass, and the smoke test in §8.4 completes a full research → brief → approve → production run against stubbed external APIs.

**Work item order matters.** Item 1 is independent. Items 2–4 depend on nothing but each other's absence. Item 5 depends on Item 4. Item 6 is independent and can be done first if you prefer a warm-up.

---

## Item 1 — Reconnect the disk skill loader

**Why:** 14 craft skills — camera grammar, character consistency, lip-sync, storyboard — are unreachable. Every disk-skill lookup currently returns an empty list, so `SkillLoaderService.build_compact_block()` produces DB-only output, which is empty on a fresh database.

**Current state**

`backend/app/services/skill_loader_service.py:22`

```python
AGENT_SKILLS_ROOT = Path(__file__).parent.parent.parent.parent / ".agent" / "skills"
```

That resolves to `<repo>/.agent/skills`, which does not exist. `.agent/` contains only `music-video-director/memory/`. The skills live at `<repo>/skills/{category}/{slug}/SKILL.md`, which is the same root `skill_synthesis_service.py:13` writes newly synthesized skills into.

`load_disk_skill()` at line ~114 also assumes a flat tree (`ROOT / slug / "SKILL.md"`), but the real layout has a category directory in between.

**Changes**

1. Repoint the constant at `<repo>/skills` and update the two docstrings that still say `.agent/skills`.
2. Rewrite `load_disk_skill(slug)` to resolve in three passes: exact `ROOT/slug/SKILL.md`; then glob `ROOT/*/slug/SKILL.md`; then a prefix glob `ROOT/*/slug*/SKILL.md` taking the last sorted match, so `seedance2-director` resolves the versioned folder `seedance2-director-v2`.
3. Normalize three files that can never load under any lookup:
   - `git mv "skills/general/seedance2-director-v2/SKILL (1).md" skills/general/seedance2-director-v2/SKILL.md`
   - `git mv skills/general/music-video-producer/music-video-producer.md skills/general/music-video-producer/SKILL.md`
   - `skills/general/higgsfield-creator/higgsfield-creator.skill` is a zip containing `higgsfield-creator/SKILL.md`. Extract that member to `skills/general/higgsfield-creator/SKILL.md` and keep the `.skill` archive in place.
4. `skills/general/claude-movie-director/SKILLS_INDEX.md` advertises 8 skills and lists paths that no longer exist. Regenerate it from the actual tree or delete it.

**Acceptance**

- A test asserts every slug in `MODEL_SKILL_MAP` and `CONTEXT_SKILL_MAP` resolves to a readable file. There are 9 distinct slugs; all 9 must pass.
- `SkillLoaderService().build_compact_block(animation_model="doubao-seedance-2-0")` returns a string containing the literal `SEEDANCE NATIVE CAMERA CONTROLS` with an empty database.

---

## Item 2 — Put reference images on the generation path

**Why:** this is the single biggest lever on output consistency. Today no user-supplied or bible-supplied image reaches any generator. Character consistency depends entirely on Claude re-describing the character in prose each scene.

**Current state**

- `backend/tasks/production.py::_generate_scene_image()` calls `media_gen_service.generate_image(scene.image_prompt, model=...)`. That method takes `prompt`, `model`, `size` — it has no reference parameter and cannot accept one.
- `backend/app/services/gpt_image_service.py::generate_with_character(prompt, character_description, reference_image_paths: List[str], size)` already posts real image bytes as multipart to OpenAI `/v1/images/edits` and returns `character_consistent: True`. **Zero importers.**
- `PreProductionBible.characters` / `.environments` are JSONB lists whose entries carry `ref_sheet_url`. `character_sheet_urls` and `environment_sheet_urls` are JSONB lists on the bible. All are written by upload and read by nothing.
- `ProductionScene.bible_character` and `.bible_environment` are populated in Phase 1 and read by nothing.

**Changes**

1. In `_generate_scene_image()`, resolve references before generating:
   - Load the `CurationJob` → `PreProductionBible` for the job.
   - Match `scene.bible_character` against `bible.characters[].name` and `scene.bible_environment` against `bible.environments[].name`.
   - Collect up to 3 `ref_sheet_url` values (character first, then environment). Fall back to `character_sheet_urls` / `environment_sheet_urls` when the per-entity field is empty.
2. Download each URL to a local cache directory (reuse the `IMAGE_CACHE_DIR` pattern and `_download_image`). `generate_with_character` takes local paths, not URLs.
3. Branch: when at least one reference resolves and `settings.OPENAI_API_KEY` is set, call `gpt_image_service.generate_with_character(prompt=scene.image_prompt, character_description=<matched character's `physical` + `wardrobe`>, reference_image_paths=<paths>)`. Otherwise call the existing `media_gen_service.generate_image()` exactly as today.
4. `generate_with_character` returns base64, not a URL. Use `gpt_image_service.save_b64_to_file()` to write it into the same cache path the current code uses, and set `scene.local_image_path`. Leave `scene.image_url` null in this branch — the animation step already prefers `local_image_path` and base64-encodes it.
5. Record which path was taken. Add a new JSONB column `ProductionScene.reference_inputs` via a new migration, storing `{"mode": "reference"|"text", "refs": [urls], "service": "gpt_image_2"|"cometapi"}`. This is what makes the choice auditable later.
6. Fix the Image Board key mismatch: `frontend/src/components/ResearchIntake.tsx` posts `urls`; `backend/app/services/intake_normalizer.py` reads `image_urls`. Align on `image_urls` and make the normalizer actually carry them into the research context rather than dropping them.

**Acceptance**

- Unit test: given a bible with one character carrying `ref_sheet_url` and a scene tagged with that character's name, `_generate_scene_image` calls `gpt_image_service.generate_with_character` with exactly that reference path. Mock the HTTP layer.
- Unit test: with no bible and no refs, the same function calls `media_gen_service.generate_image` and does not touch `gpt_image_service`.
- Every scene row after a run has non-null `reference_inputs.mode`.

---

## Item 3 — Wire the beat engine

**Why:** every clip is currently hardcoded to 5 seconds (`backend/tasks/production.py:313`) and concatenated end to end. The brief's per-scene `duration` and `ProductionScene.target_duration_sec` are both ignored. Eight `beat_*` columns exist and are never written. A real beat-tracking service exists and is never imported.

**Current state**

- `backend/app/services/audio_analysis.py` exposes a module-level singleton `audio_analysis_service` with `analyze_beats(audio_path) -> {tempo, beat_count, beat_intervals[], duration}` and `extract_segments(audio_path, top_db)`. Uses librosa. **Zero importers.**
- Dead columns on `ProductionJob`: `audio_duration_sec`, `beat_timestamps` (JSONB), `beat_interval_sec`, `tempo_bpm`. Dead on `ProductionScene`: `beat_start_sec`, `beat_end_sec`, `beat_duration_sec`, `beat_drift_ms`.
- `ProductionJob.music_url` holds a Supabase URL; `music_filename` the original name. Today `beat_sync_enabled` only matters when the file ends `.mp4`, and then only as an opaque `input_reference` passthrough to Seedance.

**Changes**

1. Add a new **Phase 1.5 — Beat mapping**, between scene-row initialization and image generation in `run_production_pipeline`. Run it only when `job.music_url` is set.
2. Download the music to a local temp path, call `audio_analysis_service.analyze_beats()`, and persist `tempo_bpm`, `beat_timestamps`, `beat_interval_sec`, `audio_duration_sec` on the job.
3. Distribute scenes across the beat grid. Write `beat_start_sec`, `beat_end_sec`, `beat_duration_sec` per scene, and `beat_drift_ms` as the signed error between the beat-quantised duration and the integer clip duration actually requested.
4. **The quantisation rule — make this explicit in code and comments.** Generators take integer seconds. Musical durations are not integers: at 128 BPM one bar is 1.875s, so a 5s clip is 2.67 bars and always lands off-grid. Implement: compute the ideal beat-aligned duration, round to the nearest integer within the model's legal range, record the residual in `beat_drift_ms`, and carry the accumulated drift forward so error does not compound across a 20-scene sequence. Cut points are corrected at assembly, not by warping generation.
5. Replace the hardcoded `duration=5` in `_animate_scene` with, in priority order: `scene.beat_duration_sec` rounded per the rule above → `scene.target_duration_sec` → the brief's per-scene `duration` → 5. Clamp to the model's legal range (Seedance 2.0 accepts 4–15 integer seconds).
6. In `assembly_service.assemble_video`, trim each clip to its `beat_end_sec - beat_start_sec` window on the concat timeline so cuts land on beats even though generation was integer-rounded.

**Acceptance**

- Unit test with a synthetic 120 BPM click track: `analyze_beats` returns tempo within ±2 BPM, and after the pipeline every scene has non-null `beat_start_sec` and `beat_end_sec`.
- Property test: across 20 scenes, accumulated `beat_drift_ms` stays bounded — the last scene's start must be within one beat interval of its ideal position. This is the test that catches naive per-scene rounding.
- A job with no music completes with all `beat_*` columns null and no exception raised.

---

## Item 4 — Add a real QA gate

**Why:** nothing currently distinguishes a good clip from a garbled one. `qa_status` and `qa_notes` exist as columns with zero assignments anywhere. Without this, "correct the first time" is unmeasurable, and Item 5 has no signal to learn from.

**Current state**

- The only success criterion in the pipeline is that an HTTP call returned and a URL was extracted (`_extract_video_url`).
- A working vision pattern already exists in `backend/app/services/video_inspiration_service.py`: `_frames_to_content_blocks()` base64-encodes frames into Anthropic image blocks, and `_analyze_with_claude()` posts them via `AsyncAnthropic` with `settings.CLAUDE_CREATIVE_MODEL`. Copy this pattern; do not invent a new one.

**Changes**

1. New service `backend/app/services/qa_service.py`. Given a scene, extract a frame with ffmpeg at the clip midpoint (`assembly_service` already shells ffmpeg — reuse its invocation style).
2. Send that frame to Claude with the scene's `image_prompt`, the bible `style_lock` (`color_palette`, `visual_rules`, `negative_prompt`), and the matched character's `physical` + `wardrobe`. Require a strict JSON response: `{"pass": bool, "character_match": 0-1, "style_match": 0-1, "prompt_adherence": 0-1, "artifacts": [str], "notes": str}`.
3. Call it at the end of `_animate_scene` for every scene that reached `animation_status == "completed"`. Write `qa_status` (`pass` | `fail` | `skipped`) and `qa_notes` (the JSON, serialized).
4. Gate assembly on it. In `run_production_pipeline` before Phase 4, count `qa_status == "fail"`. If any, set job status to `qa_review` and stop rather than assembling. Add `POST /api/production/{job_id}/assemble-anyway` as the explicit human override — the existing `POST /{job_id}/assemble` becomes that override's implementation.
5. Add `settings.QA_ENABLED: bool = True` and `settings.QA_FAIL_THRESHOLD: float = 0.6`. Scores below the threshold on `character_match` or `style_match` mark a fail.

**Non-goal:** do not auto-regenerate on failure in this pass. Detect, record, stop. Automatic remediation is a later decision.

**Acceptance**

- Integration test with a stubbed Claude client returning a failing verdict: the job halts at `qa_review`, no assembly runs, and `qa_status == "fail"` is persisted.
- Same test with a passing verdict: assembly runs and `qa_status == "pass"` on every scene.
- With `QA_ENABLED=False`, the pipeline behaves exactly as it does today and `qa_status` is `skipped`.

---

## Item 5 — Persist approvals and close the learning loop

**Why:** the platform currently has no memory and no signal to build one from. Scene approvals live in a React `useState` Set and are never sent to the server. The backend assembles unconditionally at the end of Phase 3, so the approval gate is decorative. Skill `confidence_score` is set once by Claude and never updated by an outcome. The five memory files in `.agent/music-video-director/memory/` are read by no code.

**Depends on Item 4** — QA verdicts are the objective half of the signal; human approvals are the subjective half.

**Changes**

1. **Persist approvals.** Add `ProductionScene.user_approved` (Boolean, nullable — null means "not reviewed") and `user_feedback` (Text, nullable) via migration. Add `PUT /api/production/scene/{scene_id}/approve` accepting `{approved: bool, feedback: str|null}`. Rewire `frontend/src/pages/Production.tsx` — the approval `useState` Set becomes a mutation, and approval state loads from the server on mount so it survives reload.
2. **Remove the false gate.** The amber "Preview and approve each scene before assembling" copy currently sits on top of a pipeline that already assembled. With Item 4 in place, assembly genuinely waits, so the copy becomes true. Verify this rather than assuming it.
3. **Record outcomes.** New table `generation_outcome` via migration: `scene_id`, `job_id`, `model`, `prompt` (the actual text sent), `reference_mode` (from Item 2), `beat_aligned` (bool), `qa_pass` (bool), `qa_scores` (JSONB), `user_approved` (bool, nullable), `created_at`. Write one row per scene at the end of `_animate_scene`, update it when a human approves.
4. **Feed it back.** Add `backend/app/services/memory_service.py` with two responsibilities:
   - `update_skill_confidence()` — for each skill injected into a brief, adjust `VideoProductionSkill.confidence_score` from the `generation_outcome` rows of jobs that used it. Simple and defensible: a rolling mean of `qa_pass` weighted by `user_approved` where present. Also increment `usage_count` from the pipeline, not only from a human opening the detail page.
   - `write_project_log(job_id)` — on job completion, append a markdown summary to `.agent/music-video-director/memory/PROJECT_LOG/<job-slug>.md` and a distilled rule to `LESSONS.md` when a pattern repeats (same failure category on 3+ scenes). Read the existing files first; these are append-and-distil, not overwrite.
5. **Read memory at brief time.** In `tasks/curation.py::_build_brief_context()`, load `LESSONS.md`, `PATTERNS.md` and `PREFERENCE_PROFILE.md` from the memory directory and inject them into the Claude system prompt alongside the skill block. Cap the injection at ~2,000 tokens, newest lessons first.

**Acceptance**

- Approving a scene, reloading the page, and re-reading it shows the approval persisted.
- After a completed job, `generation_outcome` has exactly one row per scene, each with a non-null `qa_pass`.
- A second job run shows the memory block present in the assembled system prompt — assert on the prompt string, not on model output.
- `write_project_log` is idempotent: running it twice for the same job produces one log file, not two.

---

## Item 6 — Clear the landmines

**Why:** these are cheap, and two of them will produce confusing runtime failures for whoever touches the adjacent code next.

| # | Defect | Location | Action |
|---|---|---|---|
| 6.1 | `suno_service.create_track` called; module never imported | `backend/tasks/production.py:345` inside `_generate_music_track` | The function is currently unreachable (`num_tracks=0` is hardcoded in `api/production.py`). Either add the import and wire it, or delete `_generate_music_track` outright. Deleting is preferred — music is user-upload-only today. Do not leave it as-is. |
| 6.2 | `bible_service.build_bible_constraint_block` raises `NotImplementedError` | `backend/app/services/bible_service.py:171` | The inline bible injection in `claude_service.py` already does this job. Delete the stub, or implement it and route `claude_service` through it. Pick one. |
| 6.3 | `inspiration_aggregator_service.aggregate_inspiration` raises `NotImplementedError`; endpoint returns HTTP 501 | `backend/app/services/inspiration_aggregator_service.py:23`, `api/bible.py:412` | Out of scope to implement. Remove the endpoint and the service, or leave both and document the 501 in the API docstring. Do not silently keep a dead route. |
| 6.4 | `ytdlp_service` orphaned | `backend/app/services/ytdlp_service.py` | `youtube_service` supersedes it. Delete unless you find a caller. |
| 6.5 | `camera_specs` never reaches Claude | Loaded into the bible dict in `tasks/curation.py:104`; 0 references in `claude_service.py` | Render `camera_specs` into the `bible_block` in `claude_service.generate_creative_brief()` alongside characters and environments. Three lines. Restores camera direction to the brief. |
| 6.6 | `stem_service` and `upscale_service` orphaned | `backend/app/services/` | Both flags default false. Either wire them behind their flags or add a module docstring stating they are staged for a later pass. The orphan gate in §8.2 must not fail on them, so whichever you choose, make it explicit. |

**Acceptance:** the orphan gate (§8.2) passes with an explicit allowlist containing only services you have consciously deferred, each carrying a docstring saying so.

---

## 7. Suggested commit sequence

One commit per item, in this order. Each must leave the repo green under all four gates.

1. `wiring: reconnect disk skill loader and normalize skill filenames`
2. `wiring: clear dead imports, stubs and orphaned services` (Item 6 — do it early, it cleans the field)
3. `wiring: route bible reference images into scene image generation`
4. `wiring: map beats to scenes and derive clip duration from the grid`
5. `wiring: add QA gate on generated clips and block assembly on failure`
6. `wiring: persist approvals, record outcomes, feed memory back into briefs`

---

## 8. Acceptance gates — all four must pass

Add these to `backend/tests/` and wire them into a single `make verify` or `npm run verify` entry point. **These are the deliverable, as much as the code is.** The previous pass shipped green on `tsc`, `npm run build`, `compileall` and an Alembic head count — none of which executes a code path, which is how an unresolvable import and six orphaned services got through.

### 8.1 Import resolution

Static check that every `from app.X import Y` and `from tasks.X import Y` names something actually defined in that module. Walk the AST; do not import third-party packages. Fail the build on any unresolved name.

This is the check that would have caught `run_briefing_pipeline`.

### 8.2 Orphan detector

Fail on any module in `backend/app/services/` with zero importers outside itself, unless listed in an explicit `ALLOWED_ORPHANS` set. The allowlist must be short, and each entry must correspond to a module whose docstring states why it is staged.

This is the check that would have caught the six unwired services.

### 8.3 Migration/usage coherence

For every column added by an Alembic migration, assert it is either read or written somewhere in `backend/app` or `backend/tasks` outside the model definition and the migration itself. Fail on columns that exist only on paper.

This is the check that would have caught the eight dead `beat_*` columns and the two dead `qa_*` columns.

### 8.4 End-to-end smoke run

The one that actually matters. With external APIs stubbed — CometAPI, Anthropic, OpenAI, Supabase, YouTube — boot the FastAPI app and drive:

```
POST /api/research/start        (text_brief source)
  -> poll to completion
POST /api/curation/start
  -> poll to brief ready
PUT  /api/curation/{id}/approve
POST /api/production/start
  -> poll through phases
```

Assert at the end: job status is `completed` or `qa_review`; every scene has non-null `animation_status`, `qa_status` and `reference_inputs.mode`; `generation_outcome` has one row per scene; and if music was supplied, `tempo_bpm` is non-null and every scene has `beat_start_sec`.

Use a real Postgres (testcontainers or a scratch database) so migrations run for real. SQLite will not exercise JSONB.

---

## 9. What to report back

For each of the six items: what you changed, which acceptance tests you added, and anything you found that this brief got wrong. That last part matters — this brief was written from a read-only audit of `77764fb` without running the application, so treat its claims about runtime behaviour as strong hypotheses rather than verified fact. If reality differs, the brief is wrong, not you.

Flag explicitly if any item turns out to be substantially larger than described. Items 4 and 5 are the most likely to expand.
