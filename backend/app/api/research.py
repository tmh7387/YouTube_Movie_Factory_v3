from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from typing import List
from app.db.session import get_db
from app.models import ResearchJob, ResearchVideo
from app.core.config import settings
from tasks.research import _orchestrate_research
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

router = APIRouter()

class ResearchCreate(BaseModel):
    topic: str
    research_depth: str = "standard"

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

@router.post("/start", response_model=ResearchJobSchema)
async def start_research(data: ResearchCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Create a new research job and trigger async background task."""
    job = ResearchJob(
        genre_topic=data.topic,
        status="pending"
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Trigger Background task
    # Note: job.id is UUID, cast to str
    background_tasks.add_task(_orchestrate_research, str(job.id), data.topic)
    
    return job

@router.get("/", response_model=List[ResearchJobSchema])
async def list_research_jobs(db: AsyncSession = Depends(get_db)):
    """List all research jobs."""
    result = await db.execute(select(ResearchJob).order_by(desc(ResearchJob.created_at)))
    return result.scalars().all()

@router.get("/{job_id}", response_model=ResearchJobDetail)
async def get_research_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get details of a specific research job including discovered videos."""
    job_result = await db.execute(select(ResearchJob).where(ResearchJob.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    video_result = await db.execute(select(ResearchVideo).where(ResearchVideo.job_id == job_id))
    videos = video_result.scalars().all()
    
    # Manually attach videos for the response model
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
            gemini_reasoning=v.gemini_reasoning
        )
        for v in videos
    ]
    
    return job_detail

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
        raise HTTPException(status_code=400, detail="Cannot delete this research project because it is being used in a curation job.")
        
    # Delete associated videos first to satisfy foreign key constraint
    await db.execute(delete(ResearchVideo).where(ResearchVideo.job_id == job_id))
    
    await db.delete(job)
    await db.commit()
    
    return {"message": "Job deleted successfully"}
