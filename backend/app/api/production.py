from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Dict, Any, Optional
import uuid
import os
from app.db.session import get_db
from app.models import ProductionJob, CurationJob, ProductionTrack, ProductionScene
from app.services.supabase_storage_service import supabase_storage
from app.services import video_models
from pydantic import BaseModel
from datetime import datetime
from tasks.production import run_production_pipeline, _animate_scene, _assemble_video

router = APIRouter()

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ProductionStartRequest(BaseModel):
    curation_job_id: uuid.UUID
    animation_mode: str = "std"       # Kling quality knob: 'std' | 'pro'
    beat_sync_enabled: bool = False   # Pass music as input_reference to Seedance
    # Registry id from app/services/video_models.py. None = auto-route per scene.
    video_model: Optional[str] = None
    # music_url is set separately via POST /upload-audio before calling /start

class ShotSpec(BaseModel):
    """One cut inside a clip. Timestamps are whole seconds, relative to the clip."""
    index: int
    start: int
    end: int
    beat: Optional[str] = None


class SceneTimingRequest(BaseModel):
    """Dictate how long a scene runs and how it is cut.

    There is no house clip length. `duration_sec` is whatever the scene needs.
    `shots` is optional — omit it for a single continuous take.
    """
    duration_sec: Optional[int] = None
    shots: Optional[List[ShotSpec]] = None


class ProductionJobResponse(BaseModel):
    id: uuid.UUID
    status: str
    created_at: datetime
    num_scenes: int
    num_tracks: int
    video_model: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Audio upload
# ---------------------------------------------------------------------------

@router.post("/upload/audio")
async def upload_audio(
    job_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an audio or video reference file to Supabase Storage.
    Returns the public URL to be stored on the ProductionJob.

    Accepted formats:
      - .mp3 / .wav  → ffmpeg audio mix only
      - .mp4         → can also be passed to Seedance as beat-sync reference

    Call this BEFORE POST /start.  Pass the returned music_url when calling /start
    (or update the existing job via PATCH if already started).
    """
    allowed = {".mp3", ".wav", ".mp4", ".m4a", ".aac"}
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{ext}'. Accepted: {', '.join(sorted(allowed))}",
        )

    max_size = 50 * 1024 * 1024  # 50 MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    # Use a temporary job_id prefix if no job_id provided yet
    prefix = job_id or f"tmp-{uuid.uuid4()}"
    result = await supabase_storage.upload_audio(content, file.filename, prefix)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # If a production job already exists, update it immediately
    if job_id:
        try:
            job_uuid = uuid.UUID(job_id)
            await db.execute(
                update(ProductionJob)
                .where(ProductionJob.id == job_uuid)
                .values(
                    music_url=result["public_url"],
                    music_filename=file.filename,
                )
            )
            await db.commit()
        except Exception:
            pass  # Job may not exist yet; caller will pass music_url to /start

    return {
        "public_url": result["public_url"],
        "filename": file.filename,
        "size_bytes": len(content),
        "is_video_reference": ext == ".mp4",
    }


# ---------------------------------------------------------------------------
# Start production job
# ---------------------------------------------------------------------------

@router.post("/start", response_model=ProductionJobResponse)
async def start_production(
    request: ProductionStartRequest,
    background_tasks: BackgroundTasks,
    music_url: Optional[str] = None,
    music_filename: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a production job from a completed curation job.
    Optionally pass music_url (Supabase public URL from /upload-audio).
    """
    result = await db.execute(select(CurationJob).where(CurationJob.id == request.curation_job_id))
    curation_job = result.scalar_one_or_none()
    if not curation_job:
        raise HTTPException(status_code=404, detail="Curation job not found")

    # Return existing job if one already exists for this curation
    result = await db.execute(
        select(ProductionJob).where(ProductionJob.curation_job_id == request.curation_job_id)
    )
    existing_job = result.scalar_one_or_none()
    if existing_job:
        return existing_job

    # Validate the model choice up front so a typo fails the request rather
    # than silently falling back mid-render. None means "auto-route".
    resolved_video_model = request.video_model or curation_job.video_model
    if resolved_video_model:
        if not video_models.is_known(resolved_video_model):
            raise HTTPException(
                status_code=400, detail=f"Unknown video model: {resolved_video_model}"
            )
        spec = video_models.resolve(resolved_video_model)
        if not spec.is_selectable:
            raise HTTPException(
                status_code=400,
                detail=f"{spec.display_name} is not available yet (status={spec.status})",
            )
        if not video_models.is_configured(spec):
            raise HTTPException(
                status_code=400,
                detail=f"{spec.display_name} is missing credentials for its {spec.transport} transport",
            )
        resolved_video_model = spec.id

    brief = curation_job.user_approved_brief or curation_job.creative_brief or {}
    storyboard = brief.get("storyboard") or brief.get("scenes", [])

    new_job = ProductionJob(
        curation_job_id=request.curation_job_id,
        status="pending",
        num_scenes=len(storyboard),
        num_tracks=0,
        music_url=music_url,
        music_filename=music_filename,
        beat_sync_enabled=request.beat_sync_enabled and bool(music_url),
        video_model=resolved_video_model,
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    background_tasks.add_task(
        run_production_pipeline,
        str(new_job.id),
        animation_mode=request.animation_mode,
        video_model=resolved_video_model,
    )
    new_job.status = "queued"
    await db.commit()
    return new_job


# ---------------------------------------------------------------------------
# List jobs
# ---------------------------------------------------------------------------

@router.get("/")
async def list_production_jobs(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductionJob)
        .order_by(ProductionJob.created_at.desc())
        .offset(skip).limit(limit)
    )
    jobs = result.scalars().all()
    return [_job_to_dict(j) for j in jobs]


# ---------------------------------------------------------------------------
# Job detail
# ---------------------------------------------------------------------------

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_production_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductionJob).where(ProductionJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Production job not found")

    tracks_res = await db.execute(select(ProductionTrack).where(ProductionTrack.job_id == job_id))
    tracks = tracks_res.scalars().all()

    scenes_res = await db.execute(
        select(ProductionScene)
        .where(ProductionScene.job_id == job_id)
        .order_by(ProductionScene.scene_number)
    )
    scenes = scenes_res.scalars().all()

    return {
        "job": _job_to_dict(job),
        "tracks": [_track_to_dict(t) for t in tracks],
        "scenes": [_scene_to_dict(s) for s in scenes],
    }


@router.patch("/{job_id}/scenes/{scene_id}/timing")
async def set_scene_timing(
    job_id: uuid.UUID,
    scene_id: uuid.UUID,
    body: SceneTimingRequest,
    db: AsyncSession = Depends(get_db),
):
    """Set a scene's clip length and cut structure.

    Overrides whatever the creative brief proposed. Takes effect on the next
    animation of that scene, so it can be set before the run or before a retry.
    """
    result = await db.execute(
        select(ProductionScene).where(
            ProductionScene.id == scene_id,
            ProductionScene.job_id == job_id,
        )
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found on this job")

    spec = video_models.resolve(scene.animation_model)

    if body.duration_sec is not None:
        if body.duration_sec < spec.min_duration or body.duration_sec > spec.max_duration:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"{spec.display_name} accepts {spec.min_duration}-{spec.max_duration}s. "
                    f"Got {body.duration_sec}s. Pick a model with more headroom, or "
                    f"split the scene."
                ),
            )
        scene.target_duration_sec = body.duration_sec

    if body.shots is not None:
        shots = sorted(body.shots, key=lambda s: s.index)
        total = scene.target_duration_sec
        if total is None:
            raise HTTPException(
                status_code=422,
                detail="Set duration_sec before defining shots, or send both together.",
            )
        if shots and shots[0].start != 0:
            raise HTTPException(status_code=422, detail="Shot 1 must start at 0.")
        for prev, nxt in zip(shots, shots[1:]):
            if prev.end != nxt.start:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Gap or overlap: shot {prev.index} ends at {prev.end}s but "
                        f"shot {nxt.index} starts at {nxt.start}s."
                    ),
                )
        if shots and shots[-1].end != int(total):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Last shot ends at {shots[-1].end}s but the clip runs {int(total)}s."
                ),
            )
        if shots and not spec.supports_timestamps:
            # Not an error — 2.0 honours shot order, just not clock times.
            pass
        scene.shot_plan = {
            "shots": [s.model_dump() for s in shots],
            "source": "user",
        } if shots else None

    await db.commit()
    await db.refresh(scene)
    return {
        "scene_id": str(scene.id),
        "target_duration_sec": (
            int(scene.target_duration_sec) if scene.target_duration_sec else None
        ),
        "shot_plan": scene.shot_plan,
        "model": spec.display_name,
        "timestamps_honoured": spec.supports_timestamps,
    }


@router.get("/curation/{curation_job_id}")
async def get_job_by_curation(curation_job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductionJob).where(ProductionJob.curation_job_id == curation_job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        return {"status": "none"}
    return _job_to_dict(job)


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

@router.get("/download/{job_id}")
async def download_assembled_video(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductionJob).where(ProductionJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Production job not found")
    if not job.assembled_video_path or not os.path.exists(job.assembled_video_path):
        raise HTTPException(status_code=404, detail="Assembled video not available yet")
    return FileResponse(
        path=job.assembled_video_path,
        media_type="video/mp4",
        filename=f"ymf_production_{job_id}.mp4",
    )


# ---------------------------------------------------------------------------
# Retry failed scenes
# ---------------------------------------------------------------------------

@router.post("/{job_id}/retry-failed")
async def retry_failed_scenes(
    job_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Re-submit animation for all scenes with status 'failed' or stale 'animating'.
    Skips scenes that are already 'completed'. Safe to call multiple times.
    """
    result = await db.execute(select(ProductionJob).where(ProductionJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Production job not found")

    scenes_res = await db.execute(
        select(ProductionScene)
        .where(ProductionScene.job_id == job_id)
        .order_by(ProductionScene.scene_number)
    )
    scenes = scenes_res.scalars().all()

    retry_ids = []
    for s in scenes:
        if s.animation_status in ("failed", "animating") or (
            s.animation_status == "pending" and not s.local_video_path
        ):
            # Reset stale animating to failed so skip guard doesn't block it
            if s.animation_status == "animating":
                s.animation_status = "failed"
            retry_ids.append(str(s.id))

    if not retry_ids:
        return {"message": "No scenes need retrying", "retried": 0}

    await db.commit()

    audio_url = job.music_url

    async def _retry_all():
        for scene_id in retry_ids:
            try:
                await _animate_scene(scene_id, audio_reference_url=audio_url)
            except Exception as exc:
                import logging
                logging.getLogger(__name__).error(f"Retry scene {scene_id} failed: {exc}")

    background_tasks.add_task(_retry_all)
    return {"message": f"Retrying {len(retry_ids)} scenes in background", "retried": len(retry_ids), "scene_ids": retry_ids}


# ---------------------------------------------------------------------------
# Trigger assembly
# ---------------------------------------------------------------------------

@router.post("/{job_id}/assemble")
async def trigger_assembly(
    job_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the ffmpeg assembly phase for a job. All scenes should be 'completed'
    before calling this, but it will proceed with whatever videos are available.
    """
    result = await db.execute(select(ProductionJob).where(ProductionJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Production job not found")

    job.status = "assembling"
    await db.commit()

    background_tasks.add_task(_assemble_video, str(job_id))
    return {"message": "Assembly started in background", "job_id": str(job_id)}


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _job_to_dict(j) -> dict:
    return {
        "id": str(j.id),
        "curation_job_id": str(j.curation_job_id),
        "status": j.status,
        "num_scenes": j.num_scenes,
        "num_tracks": j.num_tracks,
        "assembled_video_path": j.assembled_video_path,
        "total_duration_sec": float(j.total_duration_sec) if j.total_duration_sec else None,
        "file_size_bytes": j.file_size_bytes,
        "error_message": j.error_message,
        "progress_log": j.progress_log or [],
        "music_url": j.music_url,
        "music_filename": j.music_filename,
        "beat_sync_enabled": j.beat_sync_enabled or False,
        "created_at": j.created_at.isoformat() if j.created_at else None,
    }


def _scene_to_dict(s) -> dict:
    return {
        "id": str(s.id), "scene_number": s.scene_number,
        "description": s.description, "image_prompt": s.image_prompt,
        "image_url": s.image_url, "motion_prompt": s.motion_prompt,
        "animation_model": s.animation_model, "animation_status": s.animation_status,
        "local_video_path": s.local_video_path, "cometapi_task_id": s.cometapi_task_id,
        "target_duration_sec": int(s.target_duration_sec) if s.target_duration_sec else None,
        "shot_plan": s.shot_plan,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _track_to_dict(t) -> dict:
    return {
        "id": str(t.id), "track_number": t.track_number, "song_prompt": t.song_prompt,
        "suno_status": t.suno_status, "audio_url": t.audio_url,
        "error_message": t.error_message,
    }
