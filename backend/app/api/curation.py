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
from app.models import ResearchJob, CurationJob, ResearchVideo
from tasks.curation import _orchestrate_curation

logger = logging.getLogger(__name__)
router = APIRouter()


class CurationStartRequest(BaseModel):
    research_job_id: UUID
    selected_video_ids: Optional[List[str]] = None
    bible_id: Optional[UUID] = None


class CurationJobResponse(BaseModel):
    id: UUID
    research_job_id: UUID
    bible_id: Optional[UUID] = None
    status: str
    creative_brief: Optional[dict] = None
    num_scenes: Optional[int] = None
    selected_video_ids: Optional[List[str]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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

    curation_job = CurationJob(
        research_job_id=req.research_job_id,
        bible_id=req.bible_id,
        status="pending",
        selected_video_ids=req.selected_video_ids,
    )
    db.add(curation_job)
    await db.commit()
    await db.refresh(curation_job)

    background_tasks.add_task(_orchestrate_curation, str(curation_job.id), str(req.research_job_id), req.selected_video_ids)

    return curation_job


@router.get("/", response_model=List[CurationJobResponse])
async def list_curation_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CurationJob).order_by(CurationJob.created_at.desc()))
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
    result = await db.execute(select(CurationJob).where(CurationJob.id == job_id))
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
