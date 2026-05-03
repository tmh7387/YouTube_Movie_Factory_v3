import base64
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models import ResearchJob, ResearchVideo
from app.core.config import settings
from app.schemas.research import ResearchBriefResponse
from app.services.intake_service import (
    generate_research_brief,
    _extract_audio_metadata,
)
from tasks.research import _orchestrate_research

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Request / Response schemas ──────────────────────────────────────

class ResearchCreate(BaseModel):
    topic: str
    research_depth: str = "standard"
    research_brief: Optional[dict] = None
    source_type: str = "youtube_search"
    source_data: Optional[dict] = None


class ResearchVideoSchema(BaseModel):
    video_id: str
    title: str
    channel: str | None = None
    view_count: int | None = None
    likes: int | None = None
    duration_seconds: int | None = None
    published_at: datetime | None = None
    thumbnail_url: str | None = None
    relevance_score: int | None = None
    gemini_reasoning: str | None = None

    class Config:
        from_attributes = True


class ResearchJobSchema(BaseModel):
    id: UUID
    status: str
    genre_topic: str
    research_summary: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchJobDetail(ResearchJobSchema):
    videos: List[ResearchVideoSchema] = []


# ── Validation constants ────────────────────────────────────────────

MAX_IMAGE_SIZE = 5 * 1024 * 1024       # 5 MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024      # 20 MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp3"}


# ── POST /brief — stateless intake ─────────────────────────────────

@router.post("/brief", response_model=ResearchBriefResponse)
async def create_research_brief(
    topic: str = Form(...),
    style_notes: Optional[str] = Form(None),
    previous_answer: Optional[str] = Form(None),
    reference_images: Optional[List[UploadFile]] = File(None),
    reference_audio: Optional[UploadFile] = File(None),
):
    """Stateless endpoint: collect intent, return Research Brief JSON.
    No DB writes. Claude Sonnet call only."""

    # 1. Validate & encode images
    image_b64_list: List[str] = []
    if reference_images:
        for img in reference_images[:3]:
            if img.content_type not in ALLOWED_IMAGE_TYPES:
                raise HTTPException(
                    status_code=415,
                    detail=f"Unsupported image type: {img.content_type}. Use JPEG or PNG.",
                )
            raw = await img.read()
            if len(raw) > MAX_IMAGE_SIZE:
                raise HTTPException(status_code=413, detail="Image exceeds 5 MB limit.")
            image_b64_list.append(base64.b64encode(raw).decode())

    # 2. Extract audio metadata if provided
    audio_meta = None
    if reference_audio:
        if reference_audio.content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported audio type: {reference_audio.content_type}. Use MP3 or WAV.",
            )
        raw_audio = await reference_audio.read()
        if len(raw_audio) > MAX_AUDIO_SIZE:
            raise HTTPException(status_code=413, detail="Audio exceeds 20 MB limit.")
        audio_meta = _extract_audio_metadata(raw_audio)

    # 3. Call Claude Sonnet via intake service
    try:
        result = await generate_research_brief(
            topic=topic,
            style_notes=style_notes,
            previous_answer=previous_answer,
            image_b64_list=image_b64_list,
            audio_meta=audio_meta,
        )
        return result
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=422,
            detail="Brief generation failed — please try again.",
        )
    except Exception as e:
        logger.error(f"Brief generation error: {e}", exc_info=True)
        raise HTTPException(status_code=504, detail="Brief generation timed out.")


# ── POST /start — create research job ──────────────────────────────

@router.post("/start", response_model=ResearchJobSchema)
async def start_research(
    data: ResearchCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new research job and trigger async background task."""
    job = ResearchJob(
        genre_topic=data.topic,
        status="pending",
        research_brief=data.research_brief,
        source_type=data.source_type,
        source_data=data.source_data or {},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Trigger Background task
    background_tasks.add_task(
        _orchestrate_research,
        str(job.id),
        data.topic,
        data.research_brief,
        data.source_type,
        data.source_data,
    )

    return job


# ── GET / — list jobs ──────────────────────────────────────────────

@router.get("/", response_model=List[ResearchJobSchema])
async def list_research_jobs(db: AsyncSession = Depends(get_db)):
    """List all research jobs."""
    result = await db.execute(select(ResearchJob).order_by(desc(ResearchJob.created_at)))
    return result.scalars().all()


# ── GET /{job_id} — job detail ─────────────────────────────────────

@router.get("/{job_id}", response_model=ResearchJobDetail)
async def get_research_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get details of a specific research job including discovered videos."""
    job_result = await db.execute(select(ResearchJob).where(ResearchJob.id == job_id))
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    video_result = await db.execute(select(ResearchVideo).where(ResearchVideo.job_id == job_id))
    videos = video_result.scalars().all()

    job_detail = ResearchJobDetail.model_validate(job)
    job_detail.videos = [
        ResearchVideoSchema(
            video_id=v.video_id,
            title=v.title,
            channel=v.channel,
            view_count=v.views,
            likes=v.likes,
            duration_seconds=v.duration_seconds,
            published_at=v.published_at,
            thumbnail_url=v.thumbnail_url,
            relevance_score=v.relevance_score,
            gemini_reasoning=v.gemini_reasoning,
        )
        for v in videos
    ]

    return job_detail


# ── DELETE /{job_id} ───────────────────────────────────────────────

@router.delete("/{job_id}")
async def delete_research_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a specific research job and its associated videos."""
    job_result = await db.execute(select(ResearchJob).where(ResearchJob.id == job_id))
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    from app.models import CurationJob
    curation_result = await db.execute(select(CurationJob).where(CurationJob.research_job_id == job_id))
    if curation_result.first():
        raise HTTPException(
            status_code=400,
            detail="Cannot delete this research project because it is being used in a curation job.",
        )

    await db.execute(delete(ResearchVideo).where(ResearchVideo.job_id == job_id))
    await db.delete(job)
    await db.commit()

    return {"message": "Job deleted successfully"}
