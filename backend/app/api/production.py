import io
import os
import uuid
import zipfile
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import (
    CurationJob, ProductionCharacter, ProductionJob,
    ProductionScene, ProductionTrack,
)
from app.core.config import settings

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ProductionStartRequest(BaseModel):
    curation_job_id: uuid.UUID
    video_engine: str = "kling"       # kling | seedance
    image_engine: str = "nanabanana"  # nanabanana | gpt_image_2
    upscale_enabled: bool = False


class ProductionJobResponse(BaseModel):
    id: uuid.UUID
    status: str
    created_at: datetime
    num_scenes: int
    num_tracks: int

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Job lifecycle
# ---------------------------------------------------------------------------

@router.post("/start", response_model=ProductionJobResponse)
async def start_production(
    request: ProductionStartRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CurationJob).where(CurationJob.id == request.curation_job_id)
    )
    curation_job = result.scalar_one_or_none()
    if not curation_job:
        raise HTTPException(status_code=404, detail="Curation job not found")

    result = await db.execute(
        select(ProductionJob).where(
            ProductionJob.curation_job_id == request.curation_job_id
        )
    )
    existing_job = result.scalar_one_or_none()
    if existing_job:
        return existing_job

    new_job = ProductionJob(
        curation_job_id=request.curation_job_id,
        status="pending",
        num_scenes=len(
            (curation_job.user_approved_brief or {}).get("storyboard", [])
        ),
        num_tracks=1,
        upscale_enabled=request.upscale_enabled,
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    # TODO: start_production_job.delay(str(new_job.id), request.video_engine, request.image_engine)
    new_job.status = "queued"
    await db.commit()

    return new_job


@router.get("/")
async def list_production_jobs(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductionJob)
        .order_by(ProductionJob.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_production_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductionJob).where(ProductionJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Production job not found")

    result = await db.execute(
        select(ProductionTrack).where(ProductionTrack.job_id == job_id)
    )
    tracks = result.scalars().all()

    result = await db.execute(
        select(ProductionScene)
        .where(ProductionScene.job_id == job_id)
        .order_by(ProductionScene.scene_number)
    )
    scenes = result.scalars().all()

    return {"job": job, "tracks": tracks, "scenes": scenes}


@router.get("/curation/{curation_job_id}")
async def get_job_by_curation(
    curation_job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductionJob).where(
            ProductionJob.curation_job_id == curation_job_id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        return {"status": "none"}
    return job


# ---------------------------------------------------------------------------
# Phase 3 — Per-scene and full-job download
# ---------------------------------------------------------------------------

@router.get("/{job_id}/scenes/{scene_id}/download")
async def download_scene_video(
    job_id: uuid.UUID,
    scene_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download the rendered MP4 for a single scene."""
    result = await db.execute(
        select(ProductionScene).where(
            ProductionScene.id == scene_id,
            ProductionScene.job_id == job_id,
        )
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    video_path = scene.upscaled_video_path or scene.local_video_path
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Scene video file not found on disk")

    filename = f"scene_{scene.scene_number:03d}.mp4"
    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=filename,
    )


@router.get("/{job_id}/scenes/{scene_id}/download-image")
async def download_scene_image(
    job_id: uuid.UUID,
    scene_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download the still image for a single scene."""
    result = await db.execute(
        select(ProductionScene).where(
            ProductionScene.id == scene_id,
            ProductionScene.job_id == job_id,
        )
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    image_path = scene.local_image_path
    if not image_path or not Path(image_path).exists():
        raise HTTPException(status_code=404, detail="Scene image not found on disk")

    ext = Path(image_path).suffix or ".png"
    filename = f"scene_{scene.scene_number:03d}{ext}"
    return FileResponse(
        path=image_path,
        media_type="image/png",
        filename=filename,
    )


@router.get("/{job_id}/export.zip")
async def export_job_zip(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Bundle all scene MP4s + the audio track + a manifest JSON into a ZIP.
    CapCut-ready export.
    """
    result = await db.execute(
        select(ProductionJob).where(ProductionJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Production job not found")

    result = await db.execute(
        select(ProductionScene)
        .where(ProductionScene.job_id == job_id)
        .order_by(ProductionScene.scene_number)
    )
    scenes = result.scalars().all()

    result = await db.execute(
        select(ProductionTrack).where(ProductionTrack.job_id == job_id)
    )
    tracks = result.scalars().all()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Manifest
        manifest = {
            "job_id": str(job_id),
            "tempo_bpm": float(job.tempo_bpm) if job.tempo_bpm else None,
            "audio_duration_sec": float(job.audio_duration_sec) if job.audio_duration_sec else None,
            "scenes": [],
        }

        for scene in scenes:
            video_path = scene.upscaled_video_path or scene.local_video_path
            scene_entry: Dict[str, Any] = {
                "scene_number": scene.scene_number,
                "description": scene.description,
                "image_prompt": scene.image_prompt,
                "beat_start_sec": float(scene.beat_start_sec) if scene.beat_start_sec else None,
                "beat_end_sec": float(scene.beat_end_sec) if scene.beat_end_sec else None,
                "video_engine": scene.video_engine,
                "stem_energy_hint": scene.stem_energy_hint,
                "has_video": bool(video_path and Path(video_path).exists()),
            }
            manifest["scenes"].append(scene_entry)

            if video_path and Path(video_path).exists():
                zf.write(video_path, f"scenes/scene_{scene.scene_number:03d}.mp4")

        # Audio track(s)
        for track in tracks:
            if track.local_audio_path and Path(track.local_audio_path).exists():
                ext = Path(track.local_audio_path).suffix or ".mp3"
                zf.write(
                    track.local_audio_path,
                    f"audio/track_{track.track_number:02d}{ext}",
                )

        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="job_{str(job_id)[:8]}_export.zip"'
        },
    )


# ---------------------------------------------------------------------------
# Phase 2 — Character management
# ---------------------------------------------------------------------------

@router.post("/{job_id}/characters")
async def create_character(
    job_id: uuid.UUID,
    name: str = Form(...),
    description: str = Form(""),
    reference_images: List[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a named character for a production job and upload reference images.
    """
    result = await db.execute(
        select(ProductionJob).where(ProductionJob.id == job_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Production job not found")

    job_dir = Path(settings.JOB_FILES_DIR) / str(job_id) / "characters" / name
    job_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: List[str] = []
    for upload in reference_images:
        dest = job_dir / (upload.filename or f"ref_{len(saved_paths)}.png")
        content = await upload.read()
        dest.write_bytes(content)
        saved_paths.append(str(dest))

    char = ProductionCharacter(
        job_id=job_id,
        name=name,
        description=description,
        reference_image_paths=saved_paths,
    )
    db.add(char)
    await db.commit()
    await db.refresh(char)

    return {
        "id": str(char.id),
        "name": char.name,
        "description": char.description,
        "reference_count": len(saved_paths),
    }


@router.get("/{job_id}/characters")
async def list_characters(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductionCharacter).where(ProductionCharacter.job_id == job_id)
    )
    chars = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "reference_count": len(c.reference_image_paths or []),
        }
        for c in chars
    ]
