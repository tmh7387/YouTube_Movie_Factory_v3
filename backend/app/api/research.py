from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
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
    view_count: int | None
    published_at: datetime | None

    class Config:
        from_attributes = True

class ResearchJobSchema(BaseModel):
    id: UUID
    status: str
    genre_topic: str
    research_summary: str | None
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
    job_detail = ResearchJobDetail.from_orm(job)
    job_detail.videos = [ResearchVideoSchema.from_orm(v) for v in videos]
    
    return job_detail
