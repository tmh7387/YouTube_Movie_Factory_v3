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
from datetime import datetime
import copy
import logging

from app.db.session import get_db
from app.models import ResearchJob, CurationJob
from tasks.curation import _orchestrate_curation

from app.services import video_models

logger = logging.getLogger(__name__)
router = APIRouter()


class CurationStartRequest(BaseModel):
    research_job_id: UUID
    selected_video_ids: Optional[List[str]] = None
    bible_id: Optional[UUID] = None
    # Registry id from app/services/video_models.py. Steers the brief's prompt
    # dialect and becomes the default for the production run.
    video_model: Optional[str] = None


class CurationJobResponse(BaseModel):
    id: UUID
    research_job_id: UUID
    bible_id: Optional[UUID] = None
    status: str
    creative_brief: Optional[dict] = None
    user_approved_brief: Optional[dict] = None
    num_scenes: Optional[int] = None
    selected_video_ids: Optional[List[str]] = None
    video_model: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApproveBriefRequest(BaseModel):
    """Approve the creative brief, optionally with user edits."""
    edited_brief: Optional[dict] = None


class EditBriefRequest(BaseModel):
    """Partially or fully replace the creative brief before approval."""
    brief: dict


class RippleEditRequest(BaseModel):
    """Describe what to change across all scenes."""
    directive: str  # e.g. "Change the protagonist's hair from black to silver"
    target_field: str = "visual_prompt"  # which scene field to modify
    preview_only: bool = True


class RippleEditResponse(BaseModel):
    original_scenes: list
    modified_scenes: list
    changes_summary: str


@router.post("/start", response_model=CurationJobResponse)
async def create_curation_job(req: CurationStartRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    res_job_result = await db.execute(select(ResearchJob).where(ResearchJob.id == req.research_job_id))
    res_job = res_job_result.scalar_one_or_none()

    if not res_job:
        raise HTTPException(status_code=404, detail="Research job not found")

    if req.video_model and not video_models.is_known(req.video_model):
        raise HTTPException(status_code=400, detail=f"Unknown video model: {req.video_model}")

    curation_job = CurationJob(
        research_job_id=req.research_job_id,
        bible_id=req.bible_id,
        status="pending",
        selected_video_ids=req.selected_video_ids,
        video_model=video_models.resolve(req.video_model).id if req.video_model else None,
    )
    db.add(curation_job)
    await db.commit()
    await db.refresh(curation_job)

    background_tasks.add_task(_orchestrate_curation, str(curation_job.id), str(req.research_job_id), req.selected_video_ids)

    return curation_job


@router.get("/", response_model=List[CurationJobResponse])
async def list_curation_jobs(db: AsyncSession = Depends(get_db)):
    """List all curation jobs, newest first."""
    result = await db.execute(
        select(CurationJob).order_by(CurationJob.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{job_id}", status_code=204)
async def delete_curation_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CurationJob).where(CurationJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Curation job not found")
    await db.delete(job)
    await db.commit()


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


# ── Ripple Edit Endpoints ─────────────────────────────────────────

@router.post("/{job_id}/ripple-edit", response_model=RippleEditResponse)
async def ripple_edit_preview(
    job_id: UUID,
    req: RippleEditRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Preview a ripple edit across all storyboard scenes without saving.
    Returns original and modified scenes side-by-side.
    """
    result = await db.execute(select(CurationJob).where(CurationJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Curation job not found")
    if not job.creative_brief or "storyboard" not in job.creative_brief:
        raise HTTPException(status_code=400, detail="No storyboard to edit")

    storyboard = job.creative_brief["storyboard"]
    original = copy.deepcopy(storyboard)

    # Apply directive to each scene's target field
    modified = _apply_ripple(storyboard, req.directive, req.target_field)

    return RippleEditResponse(
        original_scenes=original,
        modified_scenes=modified,
        changes_summary=f"Applied '{req.directive}' to '{req.target_field}' across {len(modified)} scenes",
    )


@router.post("/{job_id}/ripple-apply")
async def ripple_apply(
    job_id: UUID,
    req: RippleEditRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Apply a ripple edit and persist the modified storyboard.
    """
    result = await db.execute(select(CurationJob).where(CurationJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Curation job not found")
    if not job.creative_brief or "storyboard" not in job.creative_brief:
        raise HTTPException(status_code=400, detail="No storyboard to edit")

    storyboard = job.creative_brief["storyboard"]
    modified = _apply_ripple(storyboard, req.directive, req.target_field)

    # Persist
    updated_brief = {**job.creative_brief, "storyboard": modified}
    await db.execute(
        update(CurationJob)
        .where(CurationJob.id == job_id)
        .values(creative_brief=updated_brief)
    )
    await db.commit()

    logger.info(f"Ripple edit applied to curation {job_id}: {req.directive}")
    return {
        "message": f"Ripple edit applied across {len(modified)} scenes",
        "directive": req.directive,
        "scenes_affected": len(modified),
    }


def _apply_ripple(scenes: list, directive: str, target_field: str) -> list:
    """
    Simple string-based ripple edit.
    For now uses find-and-replace heuristics. In Phase 6+ this could
    call Claude for intelligent rewriting.
    """
    modified = copy.deepcopy(scenes)

    # Parse directive: "Change X to Y" or "Replace X with Y"
    directive_lower = directive.lower()
    old_val, new_val = None, None

    for pattern in ["change ", "replace "]:
        if directive_lower.startswith(pattern):
            rest = directive[len(pattern):]
            for sep in [" to ", " with ", " → "]:
                if sep in rest.lower():
                    idx = rest.lower().index(sep)
                    old_val = rest[:idx].strip()
                    new_val = rest[idx + len(sep):].strip()
                    break

    if old_val and new_val:
        for scene in modified:
            if target_field in scene and isinstance(scene[target_field], str):
                # Case-insensitive replacement
                import re
                scene[target_field] = re.sub(
                    re.escape(old_val), new_val, scene[target_field], flags=re.IGNORECASE
                )
    else:
        # Fallback: append directive as instruction suffix
        for scene in modified:
            if target_field in scene and isinstance(scene[target_field], str):
                scene[target_field] += f" [{directive}]"

    return modified

# ---------------------------------------------------------------------------
# Stage 2 -> Stage 3 approval gate (from Stage-2 schema alignment)
# ---------------------------------------------------------------------------

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
    if job.status not in ("ready", "completed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit brief in status '{job.status}'. Must be 'ready' or 'completed'.",
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
    if job.status not in ("ready", "completed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve in status '{job.status}'. Must be 'ready' or 'completed'.",
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
