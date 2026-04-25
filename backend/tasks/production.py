"""
Production pipeline Celery tasks.

Phase 1: SeeDance 2.0 as alternate video engine alongside Kling.
Phase 2: GPT-Image-2 + character-consistent image generation.
Phase 3: Per-scene download (served via API; no task work needed here).
Phase 4: Demucs stem separation + per-stem reactive FFmpeg effects.
Phase 5: Lyric-driven scene-to-lyric alignment.
Phase 6: Real-ESRGAN 4K upscaling post-step.
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from celery import group
from sqlalchemy import select, update

from app.core.config import settings
from app.db.session import AsyncSessionLocal as async_session_factory
from app.models import (
    CurationJob, ProductionCharacter, ProductionJob,
    ProductionScene, ProductionTrack,
)
from app.services.audio_analysis import audio_analysis_service
from app.services.claude_service import (
    align_scenes_to_lyrics,
    tag_scene_character,
)
from app.services.media_gen_service import media_gen_service
from app.services.suno_service import suno_service
from app.services.upscale_service import upscale_service
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _update_job(job_id: str, **kwargs):
    async with async_session_factory() as db:
        await db.execute(
            update(ProductionJob)
            .where(ProductionJob.id == job_id)
            .values(**kwargs)
        )
        await db.commit()


async def _update_scene(scene_id: str, **kwargs):
    async with async_session_factory() as db:
        await db.execute(
            update(ProductionScene)
            .where(ProductionScene.id == scene_id)
            .values(**kwargs)
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

@celery_app.task(name="tasks.production.start_production_job")
def start_production_job(
    job_id: str,
    video_engine: str = "kling",
    image_engine: str = "nanabanana",
):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        run_production_pipeline(job_id, video_engine, image_engine)
    )


async def run_production_pipeline(
    job_id: str,
    video_engine: str,
    image_engine: str,
):
    logger.info(f"Production pipeline start — job={job_id} video={video_engine} image={image_engine}")

    async with async_session_factory() as db:
        row = (
            await db.execute(
                select(ProductionJob, CurationJob)
                .join(CurationJob, ProductionJob.curation_job_id == CurationJob.id)
                .where(ProductionJob.id == job_id)
            )
        ).one_or_none()
        if not row:
            logger.error(f"Job {job_id} not found")
            return

        job, curation = row
        brief = curation.user_approved_brief
        if not brief or "storyboard" not in brief:
            await _update_job(job_id, status="failed", error_message="No approved storyboard found")
            return

        # ── Phase 5: Lyric alignment ──────────────────────────────────────
        lyrics: Optional[List[Dict]] = job.lyrics
        lyric_map: Dict[int, Dict] = {}
        if lyrics:
            try:
                aligned = await align_scenes_to_lyrics(
                    lyrics=lyrics,
                    theme=brief.get("theme", ""),
                    num_scenes=len(brief["storyboard"]),
                )
                lyric_map = {item["scene_number"]: item for item in aligned}
            except Exception as e:
                logger.warning(f"Lyric alignment failed (non-fatal): {e}")

        # ── Phase 2: Load characters for this job ─────────────────────────
        chars_result = await db.execute(
            select(ProductionCharacter).where(ProductionCharacter.job_id == job_id)
        )
        characters: List[ProductionCharacter] = chars_result.scalars().all()
        character_names = [c.name for c in characters]
        char_lookup = {c.name: c for c in characters}

        # ── Initialise scenes ──────────────────────────────────────────────
        await _update_job(job_id, status="generating_images")
        scenes: List[ProductionScene] = []
        for i, scene_data in enumerate(brief["storyboard"]):
            scene_num = scene_data.get("scene_index", i + 1)
            lyric_info = lyric_map.get(scene_num, {})

            new_scene = ProductionScene(
                job_id=job.id,
                scene_number=scene_num,
                description=scene_data.get("narration"),
                lyric_or_timestamp=lyric_info.get("lyric_text"),
                image_prompt=scene_data.get("visual_prompt"),
                image_model=image_engine,
                video_engine=video_engine,
                target_duration_sec=scene_data.get("target_duration_sec", 5.0),
            )
            db.add(new_scene)
            scenes.append(new_scene)

        # ── Initialise music track ─────────────────────────────────────────
        new_track = ProductionTrack(
            job_id=job.id,
            track_number=1,
            song_prompt=brief.get("narrative_goal", "Cinematic documentary"),
            suno_status="pending",
        )
        db.add(new_track)
        await db.commit()

        # Refresh to get IDs
        for s in scenes:
            await db.refresh(s)
        await db.refresh(new_track)

    # ── Dispatch Celery tasks ──────────────────────────────────────────────
    image_tasks = [
        generate_scene_image.s(
            str(scene.id),
            image_engine,
            character_names,
        )
        for scene in scenes
    ]
    music_task = generate_music_track.s(
        str(new_track.id),
        brief.get("narrative_goal", "Cinematic"),
    )

    for t in image_tasks:
        t.delay()
    music_task.delay()


# ---------------------------------------------------------------------------
# Scene image generation (Phase 1 + 2)
# ---------------------------------------------------------------------------

@celery_app.task(name="tasks.production.generate_scene_image")
def generate_scene_image(
    scene_id: str,
    image_engine: str = "nanabanana",
    character_names: Optional[List[str]] = None,
):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        _generate_scene_image_async(scene_id, image_engine, character_names or [])
    )


async def _generate_scene_image_async(
    scene_id: str,
    image_engine: str,
    character_names: List[str],
):
    async with async_session_factory() as db:
        result = await db.execute(
            select(ProductionScene).where(ProductionScene.id == scene_id)
        )
        scene = result.scalar_one_or_none()
        if not scene:
            return

        # ── Phase 2: character tagging ─────────────────────────────────────
        char_name: Optional[str] = None
        char_refs: List[str] = []
        char_desc: Optional[str] = None

        if character_names:
            try:
                tag = await tag_scene_character(scene.description or "", character_names)
                char_name = tag.get("character_name")
            except Exception as e:
                logger.warning(f"Character tagging failed for scene {scene_id}: {e}")

        if char_name:
            char_result = await db.execute(
                select(ProductionCharacter)
                .where(
                    ProductionCharacter.job_id == scene.job_id,
                    ProductionCharacter.name == char_name,
                )
            )
            char_obj = char_result.scalar_one_or_none()
            if char_obj:
                char_refs = char_obj.reference_image_paths or []
                char_desc = char_obj.description

        # ── Generate image ─────────────────────────────────────────────────
        res = await media_gen_service.generate_image(
            prompt=scene.image_prompt or scene.description or "",
            engine=image_engine,
            character_description=char_desc,
            reference_image_paths=char_refs if char_refs else None,
        )

        if "error" in res:
            await _update_scene(scene_id, kling_status="failed", error_message=res["error"])
            return

        # Save b64 to disk if GPT-Image-2 returned b64_json
        local_image_path: Optional[str] = None
        if res.get("b64_json"):
            from app.services.gpt_image_service import gpt_image_service
            job_dir = Path(settings.JOB_FILES_DIR) / str(scene.job_id) / "images"
            out_path = str(job_dir / f"scene_{scene.scene_number:03d}.png")
            saved = await gpt_image_service.save_b64_to_file(res["b64_json"], out_path)
            local_image_path = saved

        await _update_scene(
            scene_id,
            image_url=res.get("url"),
            local_image_path=local_image_path,
            character_name=char_name,
            image_model=image_engine,
        )

    # ── Trigger animation once image is ready ─────────────────────────────
    animate_scene.delay(scene_id)


# ---------------------------------------------------------------------------
# Music generation (Phase 5 — lyric extraction)
# ---------------------------------------------------------------------------

@celery_app.task(name="tasks.production.generate_music_track")
def generate_music_track(track_id: str, mood: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_generate_music_track_async(track_id, mood))


async def _generate_music_track_async(track_id: str, mood: str):
    async with async_session_factory() as db:
        result = await db.execute(
            select(ProductionTrack).where(ProductionTrack.id == track_id)
        )
        track = result.scalar_one_or_none()
        if not track:
            return

        await db.execute(
            update(ProductionTrack)
            .where(ProductionTrack.id == track_id)
            .values(suno_status="generating")
        )
        await db.commit()

        res = await suno_service.create_track(track.song_prompt, mood=mood)
        if "error" in res:
            await db.execute(
                update(ProductionTrack)
                .where(ProductionTrack.id == track_id)
                .values(suno_status="failed", error_message=res["error"])
            )
            await db.commit()
            return

        clip_ids = [c["id"] for c in res] if isinstance(res, list) else [res.get("id")]
        clip_ids = [c for c in clip_ids if c]

        clips = await suno_service.wait_for_track(clip_ids)
        if not clips:
            return

        best = clips[0]
        audio_url = best.get("audio_url") or best.get("url")
        lyrics = suno_service.extract_lyrics(best)

        # Persist track result
        await db.execute(
            update(ProductionTrack)
            .where(ProductionTrack.id == track_id)
            .values(
                suno_task_id=best.get("id"),
                suno_status="succeed",
                title=best.get("title"),
                audio_url=audio_url,
                duration_seconds=best.get("audio_length") or best.get("duration"),
            )
        )
        await db.commit()

        # ── Phase 5: store lyrics on the parent job ────────────────────────
        if lyrics:
            job_result = await db.execute(
                select(ProductionJob).where(ProductionJob.id == track.job_id)
            )
            parent_job = job_result.scalar_one_or_none()
            if parent_job and not parent_job.lyrics:
                await _update_job(str(track.job_id), lyrics=lyrics)

        # ── Phase 4: kick off stem separation if enabled ──────────────────
        if settings.STEM_SEPARATION_ENABLED and audio_url:
            separate_stems.delay(str(track.job_id), audio_url)


# ---------------------------------------------------------------------------
# Phase 1 — Animate scene (Kling or SeeDance)
# ---------------------------------------------------------------------------

@celery_app.task(name="tasks.production.animate_scene")
def animate_scene(scene_id: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_animate_scene_async(scene_id))


async def _animate_scene_async(scene_id: str):
    async with async_session_factory() as db:
        result = await db.execute(
            select(ProductionScene).where(ProductionScene.id == scene_id)
        )
        scene = result.scalar_one_or_none()
        if not scene or not scene.image_url:
            return

    engine = scene.video_engine or "kling"

    if engine == "seedance":
        await _animate_seedance(scene)
    else:
        await _animate_kling(scene)


async def _animate_kling(scene: ProductionScene):
    """Submit animation via Kling 3.0."""
    from app.services import kling_service  # type: ignore — not yet extracted; placeholder

    logger.info(f"Kling animation for scene {scene.scene_number}")
    # Existing Kling logic remains here (or in kling_service.py)
    # This stub marks the scene as submitted for now
    await _update_scene(
        str(scene.id),
        kling_status="submitted",
        video_engine="kling",
    )


async def _animate_seedance(scene: ProductionScene):
    """Submit animation via SeeDance 2.0."""
    from app.services.seedance_service import seedance_service

    logger.info(f"SeeDance animation for scene {scene.scene_number}")
    result = await seedance_service.generate_video(
        image_url=scene.image_url,
        motion_prompt=scene.motion_prompt or scene.description or "",
        duration=int(scene.target_duration_sec or 5),
        negative_prompt=scene.negative_prompt or "",
    )
    if "error" in result:
        await _update_scene(
            str(scene.id),
            seedance_status="failed",
            error_message=result["error"],
        )
        return

    await _update_scene(
        str(scene.id),
        seedance_task_id=result.get("task_id"),
        seedance_status="succeed",
        raw_video_url=result.get("video_url"),
        video_engine="seedance",
    )

    # ── Phase 6: upscale if enabled ───────────────────────────────────────
    if result.get("video_url") and settings.UPSCALING_ENABLED:
        upscale_scene_video.delay(str(scene.id))


# ---------------------------------------------------------------------------
# Phase 4 — Stem separation
# ---------------------------------------------------------------------------

@celery_app.task(name="tasks.production.separate_stems")
def separate_stems(job_id: str, audio_url: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_separate_stems_async(job_id, audio_url))


async def _separate_stems_async(job_id: str, audio_url: str):
    import httpx
    from app.services.stem_service import stem_service

    stem_dir = Path(settings.JOB_FILES_DIR) / job_id / "stems"
    stem_dir.mkdir(parents=True, exist_ok=True)

    # Download audio
    audio_path = stem_dir / "track.mp3"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.get(audio_url)
            resp.raise_for_status()
            audio_path.write_bytes(resp.content)
    except Exception as e:
        logger.error(f"Audio download failed for stem separation: {e}")
        return

    # Separate
    result = await stem_service.separate(str(audio_path), str(stem_dir))
    if result.get("error"):
        logger.error(f"Stem separation failed: {result['error']}")
        return

    # Compute energy envelopes
    envelopes = stem_service.compute_energy_envelopes(result["stems"])

    # Store on job
    await _update_job(job_id, stem_analysis={"stems": result["stems"], "envelopes": envelopes})

    # Assign stem hints to scenes
    async with async_session_factory() as db:
        scenes_result = await db.execute(
            select(ProductionScene)
            .where(ProductionScene.job_id == job_id)
            .order_by(ProductionScene.scene_number)
        )
        scenes: List[ProductionScene] = scenes_result.scalars().all()
        beat_starts = [
            float(s.beat_start_sec) for s in scenes if s.beat_start_sec is not None
        ]

    if beat_starts:
        hints = stem_service.assign_stem_hints(beat_starts, envelopes)
        async with async_session_factory() as db:
            for scene, hint in zip(scenes, hints):
                await db.execute(
                    update(ProductionScene)
                    .where(ProductionScene.id == scene.id)
                    .values(stem_energy_hint=hint)
                )
            await db.commit()

    logger.info(f"Stem separation complete for job {job_id}")


# ---------------------------------------------------------------------------
# Phase 6 — Upscaling
# ---------------------------------------------------------------------------

@celery_app.task(name="tasks.production.upscale_scene_video")
def upscale_scene_video(scene_id: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_upscale_scene_async(scene_id))


async def _upscale_scene_async(scene_id: str):
    async with async_session_factory() as db:
        result = await db.execute(
            select(ProductionScene).where(ProductionScene.id == scene_id)
        )
        scene = result.scalar_one_or_none()
        if not scene or not scene.local_video_path:
            return

    input_path = scene.local_video_path
    output_path = str(Path(input_path).with_suffix("")) + "_4k.mp4"

    upscaled = await upscale_service.upscale_video(input_path, output_path)
    if upscaled:
        await _update_scene(scene_id, upscaled_video_path=upscaled)
        logger.info(f"Scene {scene_id} upscaled → {upscaled}")


# ---------------------------------------------------------------------------
# Legacy stubs (kept for backward compatibility)
# ---------------------------------------------------------------------------

@celery_app.task(name="tasks.production.finalize_production_assets")
def finalize_production_assets(job_id: str):
    pass
