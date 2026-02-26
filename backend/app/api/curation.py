from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.db.session import get_db
from app.models import ResearchJob, CurationJob, ResearchVideo
from tasks.curation import start_curation_job

router = APIRouter()

class CurationStartRequest(BaseModel):
    research_job_id: UUID
    selected_video_ids: Optional[List[str]] = None

class CurationJobResponse(BaseModel):
    id: UUID
    research_job_id: UUID
    status: str
    creative_brief: Optional[dict] = None
    num_scenes: Optional[int] = None

    class Config:
        from_attributes = True

@router.post("/start", response_model=CurationJobResponse)
async def create_curation_job(req: CurationStartRequest, db: AsyncSession = Depends(get_db)):
    # 1. Verify research job exists and is completed
    res_job_result = await db.execute(select(ResearchJob).where(ResearchJob.id == req.research_job_id))
    res_job = res_job_result.scalar_one_or_none()
    
    if not res_job:
        raise HTTPException(status_code=404, detail="Research job not found")
    
    # 2. Create CurationJob
    curation_job = CurationJob(
        research_job_id=req.research_job_id,
        status="pending",
        selected_video_ids=req.selected_video_ids
    )
    db.add(curation_job)
    await db.commit()
    await db.refresh(curation_job)
    
    # 3. Trigger Celery Task
    start_curation_job.delay(str(curation_job.id), str(req.research_job_id), req.selected_video_ids)
    
    return curation_job

@router.get("/", response_model=List[CurationJobResponse])
async def list_curation_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CurationJob).order_by(CurationJob.created_at.desc()))
    return result.scalars().all()

@router.get("/{job_id}", response_model=CurationJobResponse)
async def get_curation_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CurationJob).where(CurationJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Curation job not found")
    return job
