import asyncio
import base64
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy import select, update
from app.db.session import AsyncSessionLocal as async_session_factory
from app.models import (
    CurationJob,
    GenerationOutcome,
    PreProductionBible,
    ProductionJob,
    ProductionScene,
)
from app.services.media_gen_service import media_gen_service
from app.services.assembly_service import assembly_service
from app.services.audio_analysis import (
    MAX_CLIP_SECONDS,
    MIN_CLIP_SECONDS,
    audio_analysis_service,
)
from app.services.gpt_image_service import gpt_image_service
from app.services.memory_service import memory_service
from app.services.qa_service import qa_service
from app.services.skill_loader_service import skill_loader_service
from app.core.config import settings
from app.services.model_router import recommend_model

logger = logging.getLogger(__name__)

# Local cache dir for scene images (prevents pre-signed URL expiry)
IMAGE_CACHE_DIR = Path("env/tmp/scene_images")
IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Local cache dir for bible reference sheets. gpt_image_service.generate_with_character
# posts real image bytes as multipart, so it needs local paths — not URLs.
REFERENCE_CACHE_DIR = Path("env/tmp/reference_images")
REFERENCE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI's /images/edits accepts at most a handful of reference images per request.
MAX_SCENE_REFERENCES = 3

# Local cache dir for the uploaded music track (beat analysis needs a local file)
MUSIC_CACHE_DIR = Path("env/tmp/music")
MUSIC_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Fallback clip length when a job has no music and the brief gives no duration.
DEFAULT_CLIP_SECONDS = 5


async def _download_image(url: str, dest_path: Path) -> bool:
    """Download an image URL to a local file. Returns True on success."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(url)
            if r.status_code == 200:
                dest_path.write_bytes(r.content)
                return True
            logger.warning(f"Image download failed HTTP {r.status_code}: {url[:80]}")
    except Exception as e:
        logger.warning(f"Image download error: {e}")
    return False


async def _image_url_alive(url: str) -> bool:
    """Quick HEAD check — returns False if URL returns 403/404."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.head(url)
            return r.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


async def _log(job_id: str, message: str):
    """Append a timestamped entry to the job's progress_log array."""
    logger.info(f"[{job_id[:8]}] {message}")
    async with async_session_factory() as db:
        result = await db.execute(select(ProductionJob).where(ProductionJob.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            current = list(job.progress_log or [])
            current.append(f"[{_ts()}] {message}")
            await db.execute(
                update(ProductionJob)
                .where(ProductionJob.id == job_id)
                .values(progress_log=current)
            )
            await db.commit()


async def _count_qa_failures(job_id: str) -> int:
    """Scenes this job failed QA on. Only "fail" counts — "skipped" is not a failure."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(ProductionScene).where(
                ProductionScene.job_id == job_id,
                ProductionScene.qa_status == "fail",
            )
        )
        return len(result.scalars().all())


async def _update_status(job_id: str, status: str, error: Optional[str] = None):
    async with async_session_factory() as db:
        vals = {"status": status}
        if error:
            vals["error_message"] = error
        await db.execute(update(ProductionJob).where(ProductionJob.id == job_id).values(**vals))
        await db.commit()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def run_production_pipeline(
    job_id: str,
    animation_mode: str = "std",
):
    """
    Full 5-phase production pipeline:
      Phase 1 — Initialize scene rows
      Phase 2 — Generate still images
      Phase 3 — Animate each still (Kling Pro or Seedance 2.0)
                 If beat_sync_enabled + .mp4 uploaded → passed as input_reference
      Phase 4 — Assemble final video with ffmpeg (mixes music if music_url present)
    """
    await _log(job_id, "Pipeline started")

    async with async_session_factory() as db:
        result = await db.execute(
            select(ProductionJob, CurationJob)
            .join(CurationJob, ProductionJob.curation_job_id == CurationJob.id)
            .where(ProductionJob.id == job_id)
        )
        row = result.one_or_none()
        if not row:
            logger.error(f"Job {job_id} not found")
            return

        job, curation = row
        brief = curation.user_approved_brief or curation.creative_brief or {}
        storyboard_data = brief.get("storyboard") or brief.get("scenes", [])
        music_url: Optional[str] = job.music_url
        beat_sync_enabled: bool = bool(job.beat_sync_enabled)
        music_filename: Optional[str] = job.music_filename or ""
        # Only use as Seedance input_reference if it's a .mp4 file
        is_video_reference = music_filename.lower().endswith(".mp4") if music_filename else False
        seedance_audio_ref: Optional[str] = music_url if (beat_sync_enabled and is_video_reference) else None

        if not storyboard_data:
            await _update_status(job_id, "failed", "No storyboard in brief")
            await _log(job_id, "No storyboard found — aborting")
            return

        # -----------------------------------------------------------------------
        # Phase 1: Initialize DB rows
        # -----------------------------------------------------------------------
        await _update_status(job_id, "initializing")
        await _log(job_id, f"Phase 1: Creating {len(storyboard_data)} scene rows")

        scenes = []
        for scene_data in storyboard_data:
            scene_num = scene_data.get("scene_index") or scene_data.get("scene_number") or 0
            description = scene_data.get("narration") or scene_data.get("description", "")

            # Smart model routing — analyze prompt to choose best model
            recommendation = recommend_model(
                visual_prompt=scene_data.get("visual_prompt", ""),
                motion_prompt=scene_data.get("motion_prompt", ""),
                preferred_model=None,
            )
            scene_anim = recommendation["mode"]
            resolved_model = recommendation["model"]

            new_scene = ProductionScene(
                job_id=job.id,
                scene_number=scene_num,
                description=description,
                image_prompt=scene_data.get("visual_prompt", ""),
                motion_prompt=scene_data.get("motion_prompt", ""),
                animation_model=resolved_model,
                image_model=settings.DEFAULT_IMAGE_MODEL,
                animation_status="pending",
                bible_character=scene_data.get("bible_character"),
                bible_environment=scene_data.get("bible_environment"),
                # The brief's per-scene "duration" lands here so _animate_scene can
                # reach it without re-reading the brief. Beat mapping overrides it.
                target_duration_sec=scene_data.get("target_duration_sec")
                or scene_data.get("duration"),
            )
            db.add(new_scene)
            scenes.append(new_scene)

        # No music track rows needed — music comes from the user-uploaded file
        await db.commit()
        for s in scenes:
            await db.refresh(s)

        scene_ids = [str(s.id) for s in scenes]

    await _log(job_id, f"Phase 1 done — {len(scene_ids)} scenes initialized")

    # Phase 1.5: Beat mapping — only when a music track was uploaded
    if music_url:
        await _update_status(job_id, "mapping_beats")
        await _log(job_id, "Phase 1.5: Mapping scenes to the beat grid...")
        summary = await _map_beats_to_scenes(job_id, scene_ids, music_url, music_filename)
        await _log(job_id, f"Phase 1.5 done — {summary}")

    # Phase 2: Images
    await _update_status(job_id, "generating_images")
    await _log(job_id, "Phase 2: Generating still images...")
    for i, sid in enumerate(scene_ids, 1):
        await _generate_scene_image(sid)
        await _log(job_id, f"  Image {i}/{len(scene_ids)} done")
    await _log(job_id, "Phase 2 done")

    # Phase 3: Animation
    await _update_status(job_id, "animating")
    beat_ref_note = f" with audio reference ({music_filename})" if seedance_audio_ref else ""
    await _log(job_id, f"Phase 3: Animating scenes (mode={animation_mode}){beat_ref_note}...")
    for i, sid in enumerate(scene_ids, 1):
        await _animate_scene(sid, audio_reference_url=seedance_audio_ref)
        await _log(job_id, f"  Animation {i}/{len(scene_ids)} done")
    await _log(job_id, "Phase 3 done")

    # Phase 3.5: QA gate — a failed clip stops the job rather than being assembled in.
    failed = await _count_qa_failures(job_id)
    if failed:
        await _update_status(job_id, "qa_review")
        await _log(
            job_id,
            f"⏸ QA gate: {failed} scene(s) failed review — job held at qa_review. "
            f"POST /api/production/{job_id}/assemble-anyway to override.",
        )
        # A held job is still a finished production as far as learning goes — the
        # failures are exactly the part worth remembering.
        await _close_the_loop(job_id)
        return

    # Phase 4: ffmpeg assembly
    await _update_status(job_id, "assembling")
    await _log(job_id, f"Phase 4: Assembling video{' + mixing audio' if music_url else ''}...")
    await _assemble_video(job_id, scene_ids, music_url)


# ---------------------------------------------------------------------------
# Phase 1.5 — Beat mapping
# ---------------------------------------------------------------------------

async def _download_music(job_id: str, music_url: str, music_filename: Optional[str]) -> Optional[Path]:
    """Fetch the uploaded track to a local file — librosa cannot read a URL."""
    ext = os.path.splitext(music_filename or "")[-1].lower() or ".mp3"
    dest = MUSIC_CACHE_DIR / f"{job_id}{ext}"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    try:
        async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as client:
            async with client.stream("GET", music_url) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as fh:
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        fh.write(chunk)
        return dest
    except Exception as e:
        logger.warning(f"Music download failed for job {job_id}: {e}")
        return None


async def _map_beats_to_scenes(
    job_id: str,
    scene_ids: list,
    music_url: str,
    music_filename: Optional[str] = None,
) -> str:
    """
    Analyse the uploaded track and write the beat grid onto the job and its scenes.

    Every failure path is non-fatal: the beat_* columns simply stay null and the
    pipeline falls back to target_duration_sec / DEFAULT_CLIP_SECONDS. A job with no
    music never reaches this function at all.

    Returns a short human-readable summary for the progress log.
    """
    music_path = await _download_music(job_id, music_url, music_filename)
    if music_path is None:
        return "music download failed — clip durations fall back to the brief"

    # librosa is CPU-bound and blocking; keep it off the event loop.
    analysis = await asyncio.to_thread(audio_analysis_service.analyze_beats, str(music_path))
    if "error" in analysis:
        logger.warning(f"Beat analysis failed for job {job_id}: {analysis['error']}")
        return f"beat analysis failed ({analysis['error']}) — durations fall back to the brief"

    beat_times = analysis.get("beat_intervals") or []
    audio_duration = float(analysis.get("duration") or 0.0)
    tempo = float(analysis.get("tempo") or 0.0)
    interval = audio_analysis_service.mean_beat_interval(beat_times)

    rows = audio_analysis_service.map_scenes_to_beats(
        beat_times=beat_times,
        scene_count=len(scene_ids),
        audio_duration=audio_duration,
    )

    async with async_session_factory() as db:
        await db.execute(
            update(ProductionJob)
            .where(ProductionJob.id == job_id)
            .values(
                tempo_bpm=tempo or None,
                beat_timestamps=beat_times,
                beat_interval_sec=interval,
                audio_duration_sec=audio_duration or None,
            )
        )

        for scene_id, row in zip(scene_ids, rows):
            await db.execute(
                update(ProductionScene)
                .where(ProductionScene.id == scene_id)
                .values(
                    beat_start_sec=row["beat_start_sec"],
                    beat_end_sec=row["beat_end_sec"],
                    beat_duration_sec=row["beat_duration_sec"],
                    beat_drift_ms=row["beat_drift_ms"],
                )
            )
        await db.commit()

    if not rows:
        return f"{tempo:.1f} BPM, {len(beat_times)} beats — no scene windows derived"

    worst = max(abs(r["beat_drift_ms"]) for r in rows)
    return (
        f"{tempo:.1f} BPM, {len(beat_times)} beats over {audio_duration:.1f}s — "
        f"{len(rows)} scene windows, worst drift {worst:.0f}ms"
    )


def _resolve_clip_duration(scene: ProductionScene) -> int:
    """
    Integer clip length asked of the generator, in priority order:
      beat_duration_sec (the beat-quantised window) -> target_duration_sec
      (which carries the brief's per-scene duration) -> DEFAULT_CLIP_SECONDS.
    Always clamped to the model's legal range.
    """
    for candidate in (scene.beat_duration_sec, scene.target_duration_sec):
        if candidate is None:
            continue
        try:
            value = float(candidate)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return max(MIN_CLIP_SECONDS, min(MAX_CLIP_SECONDS, int(round(value))))
    return max(MIN_CLIP_SECONDS, min(MAX_CLIP_SECONDS, DEFAULT_CLIP_SECONDS))


def _scene_beat_window(scene: ProductionScene) -> Optional[float]:
    """The scene's musical window in seconds, or None when it was never beat-mapped."""
    if scene.beat_start_sec is None or scene.beat_end_sec is None:
        return None
    window = float(scene.beat_end_sec) - float(scene.beat_start_sec)
    return window if window > 0 else None


# ---------------------------------------------------------------------------
# Phase 2 — Image generation
# ---------------------------------------------------------------------------
#
# Two paths, recorded per scene in ProductionScene.reference_inputs:
#
#   "reference" — the scene is tagged with a bible character/environment that carries
#                 a ref_sheet_url. The sheets are downloaded and posted as real image
#                 bytes to GPT-Image-2's /images/edits endpoint, which anchors the
#                 character's appearance instead of re-describing it in prose.
#   "text"      — no reference resolved (or no OpenAI key). Prompt-only generation via
#                 CometAPI, exactly as before.


def _match_bible_entry(entries: Optional[list], name: Optional[str]) -> Optional[dict]:
    """Match a scene's bible_character / bible_environment tag to a bible entry by name."""
    if not name or not entries:
        return None
    target = str(name).strip().lower()
    if not target:
        return None

    candidates = [e for e in entries if isinstance(e, dict)]
    for entry in candidates:
        if str(entry.get("name", "")).strip().lower() == target:
            return entry
    # Claude sometimes writes "The Diver (close-up)" where the bible says "The Diver".
    for entry in candidates:
        entry_name = str(entry.get("name", "")).strip().lower()
        if entry_name and (entry_name in target or target in entry_name):
            return entry
    return None


async def _load_scene_bible(db, scene: ProductionScene) -> Optional[PreProductionBible]:
    """Walk ProductionScene -> ProductionJob -> CurationJob -> PreProductionBible."""
    result = await db.execute(
        select(CurationJob)
        .join(ProductionJob, ProductionJob.curation_job_id == CurationJob.id)
        .where(ProductionJob.id == scene.job_id)
    )
    curation = result.scalar_one_or_none()
    if not curation:
        return None

    if curation.bible_id:
        bible_res = await db.execute(
            select(PreProductionBible).where(PreProductionBible.id == curation.bible_id)
        )
        bible = bible_res.scalar_one_or_none()
        if bible:
            return bible

    # Bibles auto-generated during curation are linked the other way round.
    fallback = await db.execute(
        select(PreProductionBible).where(PreProductionBible.curation_job_id == curation.id)
    )
    return fallback.scalars().first()


def _collect_reference_urls(
    bible: Optional[PreProductionBible],
    scene: ProductionScene,
) -> tuple[list[str], Optional[dict]]:
    """
    Resolve up to MAX_SCENE_REFERENCES reference sheet URLs for a scene.

    Character references come first — character identity is what drifts. Per-entity
    ref_sheet_url wins; the bible-level character_sheet_urls / environment_sheet_urls
    lists are the fallback when an entity carries no sheet of its own.

    Returns (urls, matched_character_entry).
    """
    if bible is None:
        return [], None

    character = _match_bible_entry(bible.characters, scene.bible_character)
    environment = _match_bible_entry(bible.environments, scene.bible_environment)

    urls: list[str] = []

    def _add(candidate) -> None:
        if isinstance(candidate, str) and candidate.strip() and candidate not in urls:
            urls.append(candidate.strip())

    if character and character.get("ref_sheet_url"):
        _add(character["ref_sheet_url"])
    else:
        for url in (bible.character_sheet_urls or [])[:MAX_SCENE_REFERENCES]:
            _add(url)

    if environment and environment.get("ref_sheet_url"):
        _add(environment["ref_sheet_url"])
    else:
        for url in (bible.environment_sheet_urls or [])[:MAX_SCENE_REFERENCES]:
            _add(url)

    return urls[:MAX_SCENE_REFERENCES], character


def _character_description(character: Optional[dict]) -> str:
    if not character:
        return ""
    parts = [str(character.get("physical", "")).strip(), str(character.get("wardrobe", "")).strip()]
    return " | ".join(p for p in parts if p)


async def _download_references(scene_id: str, urls: list[str]) -> list[str]:
    """Download reference sheets to local paths. generate_with_character needs files."""
    paths: list[str] = []
    for i, url in enumerate(urls):
        dest = REFERENCE_CACHE_DIR / f"{scene_id}_ref{i}.png"
        if dest.exists() and dest.stat().st_size > 0:
            paths.append(str(dest))
            continue
        if await _download_image(url, dest):
            paths.append(str(dest))
        else:
            logger.warning(f"Scene {scene_id}: reference download failed for {url[:80]}")
    return paths


async def _generate_scene_image(scene_id: str):
    async with async_session_factory() as db:
        result = await db.execute(select(ProductionScene).where(ProductionScene.id == scene_id))
        scene = result.scalar_one_or_none()
        if not scene:
            return

        local_path = IMAGE_CACHE_DIR / f"{scene_id}.jpg"

        bible = await _load_scene_bible(db, scene)
        ref_urls, character = _collect_reference_urls(bible, scene)
        ref_paths = await _download_references(scene_id, ref_urls) if ref_urls else []

        if ref_paths and settings.OPENAI_API_KEY:
            res = await gpt_image_service.generate_with_character(
                prompt=scene.image_prompt,
                character_description=_character_description(character),
                reference_image_paths=ref_paths,
            )
            b64 = res.get("b64_json") if "error" not in res else None
            if b64:
                saved = await gpt_image_service.save_b64_to_file(b64, str(local_path))
                if saved:
                    # image_url stays null on this path — there is no remote URL. The
                    # animation step reads local_image_path and base64-encodes it.
                    scene.local_image_path = saved
                    scene.reference_inputs = {
                        "mode": "reference",
                        "refs": ref_urls,
                        "service": "gpt_image_2",
                    }
                    logger.info(
                        f"Scene {scene_id} image generated from {len(ref_paths)} reference(s)"
                    )
                    await db.commit()
                    return
                logger.warning(f"Scene {scene_id}: could not write GPT-Image-2 output — falling back")
            else:
                logger.warning(
                    f"Scene {scene_id}: reference generation failed "
                    f"({res.get('error', 'no image returned')}) — falling back to text prompt"
                )

        res = await media_gen_service.generate_image(
            scene.image_prompt,
            model=scene.image_model or settings.DEFAULT_IMAGE_MODEL,
        )

        if "error" in res:
            logger.error(f"Image gen failed for scene {scene_id}: {res['error']}")
            scene.animation_status = "image_failed"
            scene.reference_inputs = {"mode": "text", "refs": [], "service": "cometapi"}
        else:
            remote_url = res["url"]
            scene.image_url = remote_url
            scene.reference_inputs = {"mode": "text", "refs": [], "service": "cometapi"}

            # Download and cache locally to survive pre-signed URL expiry
            ok = await _download_image(remote_url, local_path)
            if ok:
                scene.local_image_path = str(local_path)
                logger.info(f"Scene {scene_id} image cached: {local_path}")
            else:
                logger.warning(f"Scene {scene_id} image cache failed — will use remote URL")

        await db.commit()


# ---------------------------------------------------------------------------
# Phase 3 — Animation
# ---------------------------------------------------------------------------

async def _animate_scene(scene_id: str, audio_reference_url: Optional[str] = None):
    async with async_session_factory() as db:
        result = await db.execute(select(ProductionScene).where(ProductionScene.id == scene_id))
        scene = result.scalar_one_or_none()
        # A reference-generated scene has no image_url — GPT-Image-2 returns base64,
        # which is written to local_image_path. Either source is enough to animate.
        if not scene or not (scene.image_url or scene.local_image_path):
            logger.warning(f"Skipping animation for scene {scene_id} — no image available")
            return

        # Skip scenes that already have a video (idempotent retry safety)
        if scene.animation_status == "completed" and scene.local_video_path:
            logger.info(f"Scene {scene_id} already completed — skipping")
            return

        scene.animation_status = "animating"
        await db.commit()

        # Use model_router's recommendation stored on the scene, or fallback
        anim_model_key = (scene.animation_model or settings.SEEDANCE_VIDEO_MODEL).lower()
        # Map known models to CometAPI model names + modes
        model_mode_map = {
            "kling-v2-master": (settings.DEFAULT_VIDEO_MODEL, "pro"),
            "kling-v1-6": (settings.DEFAULT_VIDEO_MODEL, "std"),
            "doubao-seedance-2-0": (settings.SEEDANCE_VIDEO_MODEL, "std"),
            "wan-pro": ("wan_pro", "std"),
        }
        video_model, mode = model_mode_map.get(anim_model_key, (settings.SEEDANCE_VIDEO_MODEL, "std"))

        # Pass audio_reference_url to Seedance for beat-sync (only if .mp4 provided)
        extra_kwargs = {}
        if audio_reference_url and mode == "std":
            extra_kwargs["input_reference"] = audio_reference_url
            logger.info(f"Scene {scene_id}: using audio reference for Seedance beat-sync")

        # Resolve best image source: prefer cached local file as base64 data URI
        # (avoids pre-signed URL expiry on remote CDNs)
        image_source = scene.image_url
        local_path = Path(scene.local_image_path) if scene.local_image_path else IMAGE_CACHE_DIR / f"{scene_id}.jpg"

        if local_path.exists():
            # Use base64 data URI — always available, no expiry
            img_bytes = local_path.read_bytes()
            b64 = base64.b64encode(img_bytes).decode()
            image_source = f"data:image/jpeg;base64,{b64}"
            logger.info(f"Scene {scene_id}: using local cached image ({local_path.stat().st_size // 1024}KB)")
        elif image_source and not await _image_url_alive(image_source):
            # Remote URL expired — re-generate the image
            logger.warning(f"Scene {scene_id}: image URL expired (403), re-generating...")
            async with async_session_factory() as regen_db:
                regen_result = await regen_db.execute(select(ProductionScene).where(ProductionScene.id == scene_id))
                regen_scene = regen_result.scalar_one_or_none()
                if regen_scene:
                    regen_res = await media_gen_service.generate_image(
                        regen_scene.image_prompt,
                        model=regen_scene.image_model or settings.DEFAULT_IMAGE_MODEL,
                    )
                    if "error" not in regen_res:
                        image_source = regen_res["url"]
                        regen_scene.image_url = image_source
                        # Cache locally for future use
                        ok = await _download_image(image_source, local_path)
                        if ok:
                            regen_scene.local_image_path = str(local_path)
                            img_bytes = local_path.read_bytes()
                            b64 = base64.b64encode(img_bytes).decode()
                            image_source = f"data:image/jpeg;base64,{b64}"
                        await regen_db.commit()
                        logger.info(f"Scene {scene_id}: image re-generated successfully")
                    else:
                        logger.error(f"Scene {scene_id}: image re-generation failed: {regen_res['error']}")

        if not image_source:
            # Reference path wrote local_image_path, but the file has since gone.
            logger.error(f"Scene {scene_id}: no usable image source — marking failed")
            scene.animation_status = "failed"
            scene.error_message = "No usable image source at animation time"
            await db.commit()
            return

        # Use skill-aware default motion prompt instead of generic fallback
        motion_prompt = scene.motion_prompt or scene.description or ""
        if not motion_prompt or motion_prompt.strip() == "":
            motion_prompt = skill_loader_service.build_motion_prompt_default(video_model)

        clip_duration = _resolve_clip_duration(scene)
        if scene.beat_duration_sec is not None:
            logger.info(
                f"Scene {scene_id}: beat window {float(scene.beat_duration_sec):.2f}s "
                f"-> requesting {clip_duration}s (drift "
                f"{float(scene.beat_drift_ms or 0):.0f}ms, corrected at assembly)"
            )

        res = await media_gen_service.animate_image(
            image_url=image_source,
            prompt=motion_prompt,
            model=video_model,
            duration=clip_duration,
            mode=mode,
            **extra_kwargs,
        )

        if "error" in res:
            logger.error(f"Animation failed for scene {scene_id}: {res['error']}")
            scene.animation_status = "failed"
        else:
            scene.local_video_path = res.get("url", "")
            scene.cometapi_task_id = res.get("task_id", "")
            scene.animation_status = "completed"
            logger.info(f"Scene {scene_id} animated: {res.get('url', '')}")

        await db.commit()

        if scene.animation_status == "completed":
            await _qa_review_scene(db, scene)
            await db.commit()
            await _record_generation_outcome(db, scene, motion_prompt, video_model)
            await db.commit()


async def _qa_review_scene(db, scene: ProductionScene) -> str:
    """
    Judge one finished clip and record the verdict on the scene.

    qa_status is always written — pass, fail or skipped — so no scene ever leaves the
    pipeline with an unknown QA state. qa_notes carries the serialized verdict.
    """
    bible = await _load_scene_bible(db, scene)
    character = _match_bible_entry(bible.characters, scene.bible_character) if bible else None
    style_lock = (bible.style_lock if bible else None) or {}

    result = await qa_service.review_scene(
        video_source=scene.local_video_path,
        image_prompt=scene.image_prompt or "",
        style_lock=style_lock,
        character=character,
    )

    scene.qa_status = result["status"]
    scene.qa_notes = json.dumps(result.get("verdict") or {})
    logger.info(f"Scene {scene.id} QA: {result['status']}")
    return result["status"]


def _qa_scores(scene: ProductionScene) -> dict:
    try:
        verdict = json.loads(scene.qa_notes or "{}")
    except (TypeError, ValueError):
        return {}
    return {
        key: verdict[key]
        for key in ("character_match", "style_match", "prompt_adherence", "artifacts")
        if key in verdict
    }


async def _record_generation_outcome(
    db,
    scene: ProductionScene,
    prompt: str,
    model: str,
) -> None:
    """
    One generation_outcome row per scene: what was asked for, what came back, and what
    QA thought of it. The human half (user_approved) is filled in later by the approve
    endpoint. This is the only signal the learning loop has to work from.

    The skills credited are recomputed from the scene's animation model with the same
    selection rules the brief used, so nothing has to be threaded through the pipeline
    to keep them in sync.
    """
    existing = await db.execute(
        select(GenerationOutcome).where(GenerationOutcome.scene_id == scene.id)
    )
    row = existing.scalar_one_or_none()

    skill_slugs = skill_loader_service.select_skill_slugs(
        animation_model=scene.animation_model or ""
    )
    values = {
        "job_id": scene.job_id,
        "model": model,
        "prompt": prompt,
        "reference_mode": (scene.reference_inputs or {}).get("mode"),
        "beat_aligned": scene.beat_start_sec is not None,
        "qa_pass": scene.qa_status == "pass" if scene.qa_status in ("pass", "fail") else None,
        "qa_scores": _qa_scores(scene),
        "skill_slugs": skill_slugs,
    }

    if row is None:
        db.add(GenerationOutcome(scene_id=scene.id, **values))
    else:
        # Re-animating a scene replaces its outcome rather than adding a second one.
        for key, value in values.items():
            setattr(row, key, value)

    await memory_service.increment_usage(skill_slugs)


# ---------------------------------------------------------------------------
# Phase 4 — ffmpeg assembly
# ---------------------------------------------------------------------------
#
# There is deliberately no music-generation phase. _generate_music_track() used to
# live here calling suno_service.create_track() without ever importing the module —
# unreachable, because api/production.py hardcodes num_tracks=0. Music is
# user-upload-only (ProductionJob.music_url), so the dead function is gone rather
# than half-wired.

async def _assemble_video(job_id: str, scene_ids: Optional[list] = None, music_url: Optional[str] = None):
    async with async_session_factory() as db:
        # Fetch music_url from job if not provided (API-triggered assembly)
        if music_url is None:
            job_res = await db.execute(select(ProductionJob).where(ProductionJob.id == job_id))
            job_row = job_res.scalar_one_or_none()
            if job_row:
                music_url = job_row.music_url

        if scene_ids:
            result = await db.execute(
                select(ProductionScene)
                .where(ProductionScene.id.in_(scene_ids))
                .order_by(ProductionScene.scene_number)
            )
        else:
            # API-triggered: assemble all completed scenes for this job
            result = await db.execute(
                select(ProductionScene)
                .where(
                    ProductionScene.job_id == job_id,
                    ProductionScene.animation_status == "completed",
                )
                .order_by(ProductionScene.scene_number)
            )
        scenes = result.scalars().all()
        playable = [s for s in scenes if s.local_video_path]
        video_clips = [s.local_video_path for s in playable]
        # Each clip is trimmed back to its musical window so the cut lands on the beat
        # even though generation could only be asked for whole seconds.
        clip_windows = [_scene_beat_window(s) for s in playable]


    if not video_clips:
        await _update_status(job_id, "failed", "No video clips generated to assemble")
        await _log(job_id, "❌ Phase 4 failed — no clips available")
        return

    res = await assembly_service.assemble_video(
        job_id=job_id,
        clip_urls=video_clips,
        music_url=music_url,
        clip_windows=clip_windows,
    )

    if "error" in res:
        await _update_status(job_id, "assembly_failed", res["error"])
        await _log(job_id, f"❌ Phase 4 failed: {res['error']}")
    else:
        async with async_session_factory() as db2:
            await db2.execute(
                update(ProductionJob)
                .where(ProductionJob.id == job_id)
                .values(
                    status="completed",
                    assembled_video_path=res.get("output_path"),
                    total_duration_sec=res.get("duration"),
                    file_size_bytes=res.get("file_size_bytes"),
                )
            )
            await db2.commit()
        await _log(job_id, f"✅ Phase 4 complete — {res.get('duration', 0):.1f}s video assembled")
        await _close_the_loop(job_id)


async def _close_the_loop(job_id: str) -> None:
    """
    Feed the finished job back into memory: write the project log and re-derive skill
    confidence from this job's outcomes. Never fatal — a job is not un-produced because
    the memory write failed.
    """
    try:
        await memory_service.write_project_log(job_id)
    except Exception as e:
        logger.warning(f"Project log failed for {job_id}: {e}")

    try:
        async with async_session_factory() as db:
            rows = await db.execute(
                select(GenerationOutcome).where(GenerationOutcome.job_id == job_id)
            )
            slugs = sorted({
                slug
                for row in rows.scalars().all()
                for slug in (row.skill_slugs or [])
            })
        if slugs:
            await memory_service.update_skill_confidence(slugs)
    except Exception as e:
        logger.warning(f"Skill confidence update failed for {job_id}: {e}")
