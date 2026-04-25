"""
Curation API endpoints — Guide §13
Includes: start, list, get, approve, and edit brief.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.db.session import get_db
from app.models import ResearchJob, CurationJob
from tasks.curation import run_briefing_pipeline

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CurationStartRequest(BaseModel):
    research_job_id: UUID
    selected_video_ids: Optional[List[str]] = None
    num_scenes: Optional[int] = 20


class ApproveBriefRequest(BaseModel):
    """Approve the creative brief, optionally with user edits."""
    edited_brief: Optional[dict] = None


class EditBriefRequest(BaseModel):
    """Partially or fully replace the creative brief before approval."""
    brief: dict


class CurationJobResponse(BaseModel):
    id: UUID
    research_job_id: UUID
    status: str
    creative_brief: Optional[dict] = None
    user_approved_brief: Optional[dict] = None
    num_scenes: Optional[int] = None
    error_message: Optional[str] = None
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/start", response_model=CurationJobResponse)
async def create_curation_job(
    req: CurationStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a curation job and kick off the briefing pipeline."""
    # Verify research job exists
    res_result = await db.execute(
        select(ResearchJob).where(ResearchJob.id == req.research_job_id)
    )
    res_job = res_result.scalar_one_or_none()
    if not res_job:
        raise HTTPException(status_code=404, detail="Research job not found")

    # Create CurationJob
    curation_job = CurationJob(
        research_job_id=req.research_job_id,
        status="pending",
        selected_video_ids=req.selected_video_ids,
        num_scenes=req.num_scenes,
    )
    db.add(curation_job)
    await db.commit()
    await db.refresh(curation_job)

    # Trigger background briefing pipeline
    background_tasks.add_task(
        run_briefing_pipeline,
        str(curation_job.id),
        str(req.research_job_id),
        req.selected_video_ids,
    )

    return curation_job


@router.get("/", response_model=List[CurationJobResponse])
async def list_curation_jobs(db: AsyncSession = Depends(get_db)):
    """List all curation jobs, newest first."""
    result = await db.execute(
        select(CurationJob).order_by(CurationJob.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{job_id}", response_model=CurationJobResponse)
async def get_curation_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single curation job by ID."""
    result = await db.execute(
        select(CurationJob).where(CurationJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Curation job not found")
    return job


@router.put("/{job_id}/brief", response_model=CurationJobResponse)
async def edit_brief(
    job_id: UUID,
    req: EditBriefRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Edit the creative brief before approval.
    Status must be 'ready'. The full brief JSON is replaced.
    """
    result = await db.execute(
        select(CurationJob).where(CurationJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Curation job not found")
    if job.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit brief in status '{job.status}'. Must be 'ready'.",
        )

    await db.execute(
        update(CurationJob)
        .where(CurationJob.id == job_id)
        .values(
            creative_brief=req.brief,
            num_scenes=len(req.brief.get("scenes", [])),
        )
    )
    await db.commit()

    # Refresh and return
    result = await db.execute(
        select(CurationJob).where(CurationJob.id == job_id)
    )
    return result.scalar_one()


@router.put("/{job_id}/approve", response_model=CurationJobResponse)
async def approve_brief(
    job_id: UUID,
    req: ApproveBriefRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Approve the creative brief (Stage 2 → Stage 3 gate).
    
    If edited_brief is provided, it replaces the original.
    Sets user_approved_brief, status='approved', approved_at=now.
    """
    result = await db.execute(
        select(CurationJob).where(CurationJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Curation job not found")
    if job.status not in ("ready",):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve in status '{job.status}'. Must be 'ready'.",
        )

    # Use edited brief if provided, otherwise use the existing creative_brief
    approved_brief = req.edited_brief if req.edited_brief else job.creative_brief
    if not approved_brief:
        raise HTTPException(
            status_code=400,
            detail="No creative brief available to approve.",
        )

    await db.execute(
        update(CurationJob)
        .where(CurationJob.id == job_id)
        .values(
            status="approved",
            user_approved_brief=approved_brief,
            approved_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()

    # Refresh and return
    result = await db.execute(
        select(CurationJob).where(CurationJob.id == job_id)
    )
    return result.scalar_one()
