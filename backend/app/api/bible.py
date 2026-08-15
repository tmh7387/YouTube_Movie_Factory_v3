"""
Bible API Router — CRUD for Pre-Production Bibles.
"""
import datetime as _dt
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


class InspirationExtractRequest(BaseModel):
    video_url: str


class ApplyCharacter(BaseModel):
    name: str
    physical: str
    wardrobe: str
    expressions: Optional[list] = []
    role: Optional[str] = "unclear"
    visual_keywords: Optional[list] = []
    confidence: Optional[str] = "medium"
    ref_sheet_url: Optional[str] = None


class ApplyEnvironment(BaseModel):
    name: str
    description: str
    lighting: str
    mood: str
    color_palette_description: Optional[str] = ""
    time_of_day: Optional[str] = "unknown"
    confidence: Optional[str] = "medium"
    ref_sheet_url: Optional[str] = None


class ApplySuggestionsRequest(BaseModel):
    characters: Optional[list[ApplyCharacter]] = []
    environments: Optional[list[ApplyEnvironment]] = []
    style_signals: Optional[dict] = None
    camera_signals: Optional[dict] = None
    apply_style: bool = False
    apply_camera: bool = False
    source_video_url: str
    source_video_title: Optional[str] = ""


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


# ── Inspiration Extraction Endpoints ───────────────────────────────

@router.post("/extract-inspiration")
async def extract_inspiration(data: InspirationExtractRequest):
    """
    Download a YouTube video, extract frames, and use Claude vision to
    identify characters and environments for bible population.

    This is a long-running operation (30-90 seconds). Returns structured
    InspirationData that the frontend presents for user review before
    applying to a specific bible.
    """
    from app.services.video_inspiration_service import extract_inspiration_from_video
    result = await extract_inspiration_from_video(data.video_url)

    if result.get("error"):
        raise HTTPException(
            status_code=500,
            detail=f"Inspiration extraction failed: {result['error']}"
        )
    return result


@router.post("/{bible_id}/apply-suggestions", response_model=BibleResponse)
async def apply_suggestions(
    bible_id: UUID,
    data: ApplySuggestionsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Merge user-selected inspiration suggestions into an existing bible.

    Characters and environments are appended to existing lists.
    style_lock is deep-merged if apply_style is True.
    camera_specs is replaced if apply_camera is True.
    """
    result = await db.execute(
        select(PreProductionBible).where(PreProductionBible.id == bible_id)
    )
    bible = result.scalar_one_or_none()
    if not bible:
        raise HTTPException(status_code=404, detail="Bible not found")
    if bible.status == "locked":
        raise HTTPException(status_code=409, detail="Bible is locked")

    # Append characters
    if data.characters:
        existing = list(bible.characters or [])
        for char in data.characters:
            existing.append({
                "name": char.name,
                "physical": char.physical,
                "wardrobe": char.wardrobe,
                "expressions": char.expressions or [],
                "role": char.role,
                "visual_keywords": char.visual_keywords or [],
                "ref_sheet_url": char.ref_sheet_url,
                "source": data.source_video_url,
            })
        bible.characters = existing

    # Append environments
    if data.environments:
        existing = list(bible.environments or [])
        for env in data.environments:
            existing.append({
                "name": env.name,
                "description": env.description,
                "lighting": env.lighting,
                "mood": env.mood,
                "color_palette_description": env.color_palette_description,
                "time_of_day": env.time_of_day,
                "ref_sheet_url": env.ref_sheet_url,
                "source": data.source_video_url,
            })
        bible.environments = existing

    # Merge style_lock if requested
    if data.apply_style and data.style_signals:
        style = dict(bible.style_lock or {})
        style.update({
            "color_grade": data.style_signals.get("color_grade", ""),
            "visual_aesthetic": data.style_signals.get("visual_aesthetic", ""),
            "cinematography_notes": data.style_signals.get("cinematography_notes", ""),
        })
        bible.style_lock = style

    # Replace camera_specs if requested
    if data.apply_camera and data.camera_signals:
        bible.camera_specs = {
            "dominant_shot_types": data.camera_signals.get("dominant_shot_types", []),
            "movement_style": data.camera_signals.get("movement_style", ""),
            "lens_feel": data.camera_signals.get("lens_feel", ""),
        }

    # Append to process log
    log = list(bible.process_log or [])
    char_count = len(data.characters or [])
    env_count = len(data.environments or [])
    log.append({
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "agent": "video_inspiration",
        "action": "Inspiration applied from video",
        "outcome": (
            f"Added {char_count} character(s), {env_count} environment(s) "
            f"from '{data.source_video_title or data.source_video_url}'"
        ),
    })
    bible.process_log = log

    await db.commit()
    await db.refresh(bible)
    logger.info(f"Applied inspiration to bible {bible_id}: {char_count} chars, {env_count} envs")
    return bible


@router.post("/aggregate-inspiration")
async def aggregate_inspiration_placeholder():
    """Phase 2 placeholder — multi-source inspiration aggregation."""
    raise HTTPException(
        status_code=501,
        detail="Multi-source aggregation is not yet implemented (Phase 2)"
    )
