import asyncio
import base64
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy import select, update
from app.db.session import AsyncSessionLocal as async_session_factory
from app.models import ProductionJob, CurationJob, ProductionScene, ProductionTrack
from app.services.media_gen_service import media_gen_service
from app.services.assembly_service import assembly_service
from app.services.skill_loader_service import skill_loader_service
from app.core.config import settings

logger = logging.getLogger(__name__)

# Local cache dir for scene images (prevents pre-signed URL expiry)
IMAGE_CACHE_DIR = Path("env/tmp/scene_images")
IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


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

            # Assign per-scene animation model override
            scene_anim = scene_data.get("kling_mode", animation_mode)

            new_scene = ProductionScene(
                job_id=job.id,
                scene_number=scene_num,
                description=description,
                image_prompt=scene_data.get("visual_prompt", ""),
                motion_prompt=scene_data.get("motion_prompt", ""),
                animation_model=scene_anim,
                image_model=settings.DEFAULT_IMAGE_MODEL,
                animation_status="pending",
            )
            db.add(new_scene)
            scenes.append(new_scene)

        # No music track rows needed — music comes from the user-uploaded file
        await db.commit()
        for s in scenes:
            await db.refresh(s)

        scene_ids = [str(s.id) for s in scenes]

    await _log(job_id, f"Phase 1 done — {len(scene_ids)} scenes initialized")

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

    # Phase 4: ffmpeg assembly
    await _update_status(job_id, "assembling")
    await _log(job_id, f"Phase 4: Assembling video{' + mixing audio' if music_url else ''}...")
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
            remote_url = res["url"]
            scene.image_url = remote_url

            # Download and cache locally to survive pre-signed URL expiry
            local_path = IMAGE_CACHE_DIR / f"{scene_id}.jpg"
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
        if not scene or not scene.image_url:
            logger.warning(f"Skipping animation for scene {scene_id} — no image URL")
            return

        # Skip scenes that already have a video (idempotent retry safety)
        if scene.animation_status == "completed" and scene.local_video_path:
            logger.info(f"Scene {scene_id} already completed — skipping")
            return

        scene.animation_status = "animating"
        await db.commit()

        anim_model_key = (scene.animation_model or "std").lower()
        if anim_model_key == "pro":
            video_model = settings.DEFAULT_VIDEO_MODEL   # kling_video
            mode = "pro"
        else:
            video_model = settings.SEEDANCE_VIDEO_MODEL  # doubao-seedance-2-0
            mode = "std"

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

        # Use skill-aware default motion prompt instead of generic fallback
        motion_prompt = scene.motion_prompt or scene.description or ""
        if not motion_prompt or motion_prompt.strip() == "":
            motion_prompt = skill_loader_service.build_motion_prompt_default(video_model)

        res = await media_gen_service.animate_image(
            image_url=image_source,
            prompt=motion_prompt,
            model=video_model,
            duration=5,
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


# ---------------------------------------------------------------------------
# Phase 4 — Music generation
# ---------------------------------------------------------------------------

async def _generate_music_track(track_id: str, mood: str) -> Optional[str]:
    """Returns audio URL on success, None on failure."""
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

        audio_url = res.get("audio_url")
        track.suno_task_id = res.get("id", "")
        track.audio_url = audio_url
        track.suno_status = "completed"
        await db.commit()
        logger.info(f"Music track ready: {audio_url}")
        return audio_url


# ---------------------------------------------------------------------------
# Phase 5 — ffmpeg assembly
# ---------------------------------------------------------------------------

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
        video_clips = [s.local_video_path for s in scenes if s.local_video_path]


    if not video_clips:
        await _update_status(job_id, "failed", "No video clips generated to assemble")
        await _log(job_id, "❌ Phase 5 failed — no clips available")
        return

    res = await assembly_service.assemble_video(
        job_id=job_id,
        clip_urls=video_clips,
        music_url=music_url,
    )

    if "error" in res:
        await _update_status(job_id, "assembly_failed", res["error"])
        await _log(job_id, f"❌ Phase 5 failed: {res['error']}")
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
        await _log(job_id, f"✅ Phase 5 complete — {res.get('duration', 0):.1f}s video assembled")
