import asyncio
import logging
import os
from typing import Optional
from sqlalchemy import select, update
from app.db.session import AsyncSessionLocal as async_session_factory
from app.models import ProductionJob, CurationJob, ProductionScene, ProductionTrack
from app.services.media_gen_service import media_gen_service
from app.services.suno_service import suno_service
from app.services.assembly_service import assembly_service
from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

async def _update_job_status(job_id: str, status: str, error: Optional[str] = None):
    async with async_session_factory() as db:
        vals = {"status": status}
        if error:
            vals["error_message"] = error
        await db.execute(update(ProductionJob).where(ProductionJob.id == job_id).values(**vals))
        await db.commit()


# ---------------------------------------------------------------------------
# Main pipeline entry point
# ---------------------------------------------------------------------------

async def run_production_pipeline(job_id: str):
    """
    Full production pipeline:
      Phase 1 — Initialize scenes + track rows in DB
      Phase 2 — Generate still images for each scene
      Phase 3 — Animate each still (Kling or Seedance)
      Phase 4 — Generate music track (Suno via CometAPI)
      Phase 5 — Assemble final video with ffmpeg
    """
    logger.info(f"Starting production pipeline for job {job_id}")

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

        # Defensive: support both 'storyboard' (new Claude schema) and 'scenes' (legacy)
        storyboard_data = brief.get("storyboard") or brief.get("scenes", [])
        if not storyboard_data:
            await _update_job_status(job_id, "failed", "No storyboard found in approved brief")
            return

        # --- Phase 1: Initialize DB rows ---
        scenes = []
        for scene_data in storyboard_data:
            # Handle both schema variants
            scene_num = scene_data.get("scene_index") or scene_data.get("scene_number") or 0
            description = scene_data.get("narration") or scene_data.get("description", "")
            motion = scene_data.get("motion_prompt", "")
            anim_model = scene_data.get("kling_mode", "std")

            new_scene = ProductionScene(
                job_id=job.id,
                scene_number=scene_num,
                description=description,
                image_prompt=scene_data.get("visual_prompt", ""),
                motion_prompt=motion,
                animation_model=anim_model,
                image_model=settings.DEFAULT_IMAGE_MODEL,
                animation_status="pending",
            )
            db.add(new_scene)
            scenes.append(new_scene)

        new_track = ProductionTrack(
            job_id=job.id,
            track_number=1,
            song_prompt=brief.get("music_mood", "Cinematic documentary instrumental"),
            suno_status="pending",
        )
        db.add(new_track)

        await db.commit()
        # Refresh to get DB-assigned IDs
        for s in scenes:
            await db.refresh(s)
        await db.refresh(new_track)

        scene_ids = [str(s.id) for s in scenes]
        track_id = str(new_track.id)

    # --- Phase 2: Image generation ---
    await _update_job_status(job_id, "generating_images")
    for sid in scene_ids:
        await _generate_scene_image(sid)

    # --- Phase 3: Animation ---
    await _update_job_status(job_id, "animating")
    for sid in scene_ids:
        await _animate_scene(sid)

    # --- Phase 4: Music generation (runs concurrently with animation in future) ---
    await _update_job_status(job_id, "generating_music")
    music_url = await _generate_music_track(track_id, brief.get("music_mood", "Cinematic"))

    # --- Phase 5: Assembly ---
    await _update_job_status(job_id, "assembling")
    await _assemble_video(job_id, scene_ids, music_url)


# ---------------------------------------------------------------------------
# Phase 2 — Image generation
# ---------------------------------------------------------------------------

async def _generate_scene_image(scene_id: str):
    async with async_session_factory() as db:
        result = await db.execute(select(ProductionScene).where(ProductionScene.id == scene_id))
        scene = result.scalar_one_or_none()
        if not scene:
            return

        res = await media_gen_service.generate_image(
            scene.image_prompt,
            model=scene.image_model or settings.DEFAULT_IMAGE_MODEL,
        )

        if "error" in res:
            logger.error(f"Image gen failed for scene {scene_id}: {res['error']}")
            scene.animation_status = "image_failed"
        else:
            scene.image_url = res["url"]
            logger.info(f"Scene {scene_id} image ready: {res['url']}")

        await db.commit()


# ---------------------------------------------------------------------------
# Phase 3 — Animation (Kling std/pro via CometAPI, or Seedance 2.0)
# ---------------------------------------------------------------------------

async def _animate_scene(scene_id: str):
    async with async_session_factory() as db:
        result = await db.execute(select(ProductionScene).where(ProductionScene.id == scene_id))
        scene = result.scalar_one_or_none()
        if not scene or not scene.image_url:
            logger.warning(f"Skipping animation for scene {scene_id} — no image URL")
            return

        scene.animation_status = "animating"
        await db.commit()

        # Route to Seedance for 'std' mode (cheaper), Kling pro for 'pro' mode
        anim_model_key = (scene.animation_model or "std").lower()
        if anim_model_key == "pro":
            video_model = settings.DEFAULT_VIDEO_MODEL  # kling_video
            mode = "pro"
        else:
            video_model = settings.SEEDANCE_VIDEO_MODEL  # doubao-seedance-2-0
            mode = "std"

        res = await media_gen_service.animate_image(
            image_url=scene.image_url,
            prompt=scene.motion_prompt or scene.description or "",
            model=video_model,
            duration=5,
            mode=mode,
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


# ---------------------------------------------------------------------------
# Phase 4 — Music generation
# ---------------------------------------------------------------------------

async def _generate_music_track(track_id: str, mood: str) -> Optional[str]:
    """Returns the audio URL if successful, else None."""
    async with async_session_factory() as db:
        result = await db.execute(select(ProductionTrack).where(ProductionTrack.id == track_id))
        track = result.scalar_one_or_none()
        if not track:
            return None

        track.suno_status = "generating"
        await db.commit()

        res = await suno_service.create_track(track.song_prompt, mood=mood)

        if "error" in res:
            logger.error(f"Music generation failed: {res['error']}")
            track.suno_status = "failed"
            track.error_message = res["error"]
            await db.commit()
            return None

        audio_url = res.get("audio_url") or res.get("url")
        track.suno_task_id = res.get("id", "")
        track.audio_url = audio_url
        track.suno_status = "completed"
        await db.commit()
        logger.info(f"Music track ready: {audio_url}")
        return audio_url


# ---------------------------------------------------------------------------
# Phase 5 — ffmpeg assembly
# ---------------------------------------------------------------------------

async def _assemble_video(job_id: str, scene_ids: list, music_url: Optional[str]):
    async with async_session_factory() as db:
        # Collect completed video paths
        result = await db.execute(
            select(ProductionScene)
            .where(ProductionScene.id.in_(scene_ids))
            .order_by(ProductionScene.scene_number)
        )
        scenes = result.scalars().all()
        video_clips = [s.local_video_path for s in scenes if s.local_video_path]

        if not video_clips:
            await _update_job_status(job_id, "failed", "No video clips generated to assemble")
            return

        res = await assembly_service.assemble_video(
            job_id=job_id,
            clip_urls=video_clips,
            music_url=music_url,
        )

        if "error" in res:
            await _update_job_status(job_id, "assembly_failed", res["error"])
        else:
            async with async_session_factory() as db2:
                await db2.execute(
                    update(ProductionJob)
                    .where(ProductionJob.id == job_id)
                    .values(
                        status="completed",
                        assembled_video_path=res.get("output_path"),
                        total_duration_sec=res.get("duration"),
                    )
                )
                await db2.commit()
            logger.info(f"Job {job_id} assembled: {res.get('output_path')}")
