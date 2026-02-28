from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import uuid
from app.db.session import get_db
from app.models import ProductionJob, CurationJob, ProductionTrack, ProductionScene
from pydantic import BaseModel
from datetime import datetime
from tasks.production import start_production_job # I'll implement this next

router = APIRouter()

class ProductionStartRequest(BaseModel):
    curation_job_id: uuid.UUID

class ProductionJobResponse(BaseModel):
    id: uuid.UUID
    status: str
    created_at: datetime
    num_scenes: int
    num_tracks: int

    class Config:
        from_attributes = True

@router.post("/start", response_model=ProductionJobResponse)
async def start_production(request: ProductionStartRequest, db: AsyncSession = Depends(get_db)):
    """
    Start a production job from an approved curation job.
    """
    # Check if curation job exists and is approved
    result = await db.execute(select(CurationJob).where(CurationJob.id == request.curation_job_id))
    curation_job = result.scalar_one_or_none()
    
    if not curation_job:
        raise HTTPException(status_code=404, detail="Curation job not found")
    
    # Check if production job already exists
    result = await db.execute(select(ProductionJob).where(ProductionJob.curation_job_id == request.curation_job_id))
    existing_job = result.scalar_one_or_none()
    if existing_job:
        return existing_job

    # Create new production job
    new_job = ProductionJob(
        curation_job_id=request.curation_job_id,
        status="pending",
        num_scenes=len(curation_job.user_approved_brief.get('storyboard', [])),
        num_tracks=1 # Default 1 track for now
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    # Trigger Celery task
    task = start_production_job.delay(str(new_job.id))
    new_job.celery_task_id = task.id
    new_job.status = "queued"
    await db.commit()

    return new_job

@router.get("/")
async def list_production_jobs(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """
    List all production jobs, ordered by creation date descending.
    """
    result = await db.execute(
        select(ProductionJob)
        .order_by(ProductionJob.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    jobs = result.scalars().all()
    return jobs

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_production_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Get detailed status of a production job, including tracks and scenes.
    """
    result = await db.execute(select(ProductionJob).where(ProductionJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Production job not found")

    # Get tracks
    result = await db.execute(select(ProductionTrack).where(ProductionTrack.job_id == job_id))
    tracks = result.scalars().all()

    # Get scenes
    result = await db.execute(select(ProductionScene).where(ProductionScene.job_id == job_id).order_by(ProductionScene.scene_number))
    scenes = result.scalars().all()

    return {
        "job": job,
        "tracks": tracks,
        "scenes": scenes
    }

@router.get("/curation/{curation_job_id}")
async def get_job_by_curation(curation_job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductionJob).where(ProductionJob.curation_job_id == curation_job_id))
    job = result.scalar_one_or_none()
    if not job:
        return {"status": "none"}
    return job
