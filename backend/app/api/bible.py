"""
Bible API Router — CRUD for Pre-Production Bibles.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import PreProductionBible
from app.services.supabase_storage_service import supabase_storage

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ─────────────────────────────────────────────────────────

class BibleCreate(BaseModel):
    name: str
    curation_job_id: Optional[UUID] = None
    characters: Optional[list] = None
    environments: Optional[list] = None
    style_lock: Optional[dict] = None
    surreal_motifs: Optional[list] = None
    camera_specs: Optional[dict] = None


class BibleUpdate(BaseModel):
    name: Optional[str] = None
    characters: Optional[list] = None
    environments: Optional[list] = None
    style_lock: Optional[dict] = None
    surreal_motifs: Optional[list] = None
    camera_specs: Optional[dict] = None
    character_sheet_urls: Optional[list] = None
    environment_sheet_urls: Optional[list] = None


class LogEntry(BaseModel):
    agent: str = "user"
    action: str
    outcome: str = ""


class BibleResponse(BaseModel):
    id: UUID
    curation_job_id: Optional[UUID] = None
    name: str
    status: str
    characters: Optional[list] = None
    environments: Optional[list] = None
    style_lock: Optional[dict] = None
    surreal_motifs: Optional[list] = None
    camera_specs: Optional[dict] = None
    character_sheet_urls: Optional[list] = None
    environment_sheet_urls: Optional[list] = None
    process_log: Optional[list] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Endpoints ───────────────────────────────────────────────────────

@router.post("/", response_model=BibleResponse)
async def create_bible(data: BibleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new Pre-Production Bible."""
    bible = PreProductionBible(
        name=data.name,
        curation_job_id=data.curation_job_id,
        characters=data.characters or [],
        environments=data.environments or [],
        style_lock=data.style_lock or {},
        surreal_motifs=data.surreal_motifs or [],
        camera_specs=data.camera_specs or {},
        process_log=[{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": "system",
            "action": "Bible created",
            "outcome": f"Name: {data.name}",
        }],
    )
    db.add(bible)
    await db.commit()
    await db.refresh(bible)
    logger.info(f"Created bible {bible.id}: {bible.name}")
    return bible


@router.get("/", response_model=List[BibleResponse])
async def list_bibles(db: AsyncSession = Depends(get_db)):
    """List all bibles, newest first."""
    result = await db.execute(
        select(PreProductionBible).order_by(PreProductionBible.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{bible_id}", response_model=BibleResponse)
async def get_bible(bible_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get full bible with all sections."""
    result = await db.execute(
        select(PreProductionBible).where(PreProductionBible.id == bible_id)
    )
    bible = result.scalar_one_or_none()
    if not bible:
        raise HTTPException(status_code=404, detail="Bible not found")
    return bible


@router.put("/{bible_id}", response_model=BibleResponse)
async def update_bible(bible_id: UUID, data: BibleUpdate, db: AsyncSession = Depends(get_db)):
    """Partial update of bible sections (JSONB merge)."""
    result = await db.execute(
        select(PreProductionBible).where(PreProductionBible.id == bible_id)
    )
    bible = result.scalar_one_or_none()
    if not bible:
        raise HTTPException(status_code=404, detail="Bible not found")
    if bible.status == "locked":
        raise HTTPException(status_code=409, detail="Bible is locked — unlock or create a new one")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "style_lock" and isinstance(value, dict) and isinstance(bible.style_lock, dict):
            # Merge style_lock instead of replacing
            merged = {**bible.style_lock, **value}
            setattr(bible, field, merged)
        else:
            setattr(bible, field, value)

    await db.commit()
    await db.refresh(bible)
    logger.info(f"Updated bible {bible_id}")
    return bible


@router.put("/{bible_id}/lock", response_model=BibleResponse)
async def lock_bible(bible_id: UUID, db: AsyncSession = Depends(get_db)):
    """Lock the bible to prevent further edits."""
    result = await db.execute(
        select(PreProductionBible).where(PreProductionBible.id == bible_id)
    )
    bible = result.scalar_one_or_none()
    if not bible:
        raise HTTPException(status_code=404, detail="Bible not found")

    bible.status = "locked"
    # Append lock event to process log
    log = list(bible.process_log or [])
    log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "system",
        "action": "Bible locked",
        "outcome": "No further edits allowed",
    })
    bible.process_log = log

    await db.commit()
    await db.refresh(bible)
    logger.info(f"Bible {bible_id} locked")
    return bible


@router.post("/{bible_id}/log", response_model=BibleResponse)
async def append_log(bible_id: UUID, entry: LogEntry, db: AsyncSession = Depends(get_db)):
    """Append an entry to the bible's process log."""
    result = await db.execute(
        select(PreProductionBible).where(PreProductionBible.id == bible_id)
    )
    bible = result.scalar_one_or_none()
    if not bible:
        raise HTTPException(status_code=404, detail="Bible not found")

    log = list(bible.process_log or [])
    log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": entry.agent,
        "action": entry.action,
        "outcome": entry.outcome,
    })
    bible.process_log = log
    await db.commit()
    await db.refresh(bible)
    return bible


@router.delete("/{bible_id}")
async def delete_bible(bible_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a bible (only if status is 'draft')."""
    result = await db.execute(
        select(PreProductionBible).where(PreProductionBible.id == bible_id)
    )
    bible = result.scalar_one_or_none()
    if not bible:
        raise HTTPException(status_code=404, detail="Bible not found")
    if bible.status != "draft":
        raise HTTPException(status_code=409, detail="Only draft bibles can be deleted")

    await db.delete(bible)
    await db.commit()
    return {"message": "Bible deleted"}


@router.post("/{bible_id}/upload")
async def upload_reference_sheet(
    bible_id: UUID,
    sheet_type: str = "character",
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a reference sheet image to Supabase Storage and append URL to bible.
    sheet_type: 'character' or 'environment'
    """
    result = await db.execute(
        select(PreProductionBible).where(PreProductionBible.id == bible_id)
    )
    bible = result.scalar_one_or_none()
    if not bible:
        raise HTTPException(status_code=404, detail="Bible not found")

    file_bytes = await file.read()
    upload_result = await supabase_storage.upload_file(
        file_bytes=file_bytes,
        filename=file.filename or "ref_sheet.png",
        folder=f"bibles/{bible_id}",
    )

    if "error" in upload_result:
        raise HTTPException(status_code=500, detail=upload_result["error"])

    url = upload_result["public_url"]

    if sheet_type == "character":
        urls = list(bible.character_sheet_urls or [])
        urls.append(url)
        bible.character_sheet_urls = urls
    else:
        urls = list(bible.environment_sheet_urls or [])
        urls.append(url)
        bible.environment_sheet_urls = urls

    await db.commit()
    await db.refresh(bible)
    logger.info(f"Uploaded {sheet_type} ref sheet to bible {bible_id}: {url}")
    return {"public_url": url, "sheet_type": sheet_type}
