from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, field_validator
from typing import Optional, List
from sqlalchemy import select, desc
import uuid

from app.db.session import AsyncSessionLocal
from app.models import TutorialKnowledgeEntry

router = APIRouter()

VALID_CATEGORIES = {"music_video", "product_brand", "asmr", "general"}


class IngestRequest(BaseModel):
    youtube_url: str
    category: str = "general"
    extra_context: str = ""

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {VALID_CATEGORIES}")
        return v

    @field_validator("youtube_url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        if "youtube.com" not in v and "youtu.be" not in v:
            raise ValueError("youtube_url must be a YouTube URL")
        # Strip playlist params — Gemini rejects them
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(v)
        if "youtu.be" in parsed.netloc:
            return f"https://youtu.be{parsed.path}"
        qs = parse_qs(parsed.query)
        video_id = qs.get("v", [None])[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
        return v


class IngestResponse(BaseModel):
    entry_id: str
    status: str
    message: str


def _entry_to_dict(e: TutorialKnowledgeEntry) -> dict:
    notion_links = (e.external_resources or {}).get("notion_links", [])
    return {
        "id": str(e.id),
        "youtube_url": e.youtube_url,
        "video_id": e.video_id,
        "category": e.category,
        "status": e.status,
        "standout_tip": e.standout_tip,
        "exact_prompts": e.exact_prompts,
        "tool_names": e.tool_names,
        "workflow_steps": e.workflow_steps,
        "key_settings": e.key_settings,
        "category_specific": e.category_specific,
        "full_technique_summary": e.full_technique_summary,
        "aggregated_resources": e.aggregated_resources,
        # Notion links found in the video — visit these manually
        "notion_links_found": notion_links,
        "notion_links_alert": (
            f"⚠ {len(notion_links)} Notion resource(s) found — visit manually: {', '.join(notion_links)}"
            if notion_links else None
        ),
        "gemini_model_used": e.gemini_model_used,
        "error_message": e.error_message,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "completed_at": e.completed_at.isoformat() if e.completed_at else None,
    }


@router.post("/ingest", response_model=IngestResponse)
async def ingest_tutorial(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Submit a YouTube tutorial URL for full analysis:
    - Gemini 3.1 video understanding (techniques, prompts, tools, workflow)
    - Comment and description resource mining
    - Any Notion links found are surfaced in the response as alerts for manual review.
    Processing runs as a FastAPI background task.
    """
    from tasks.knowledge import _orchestrate_knowledge_ingest

    async with AsyncSessionLocal() as session:
        entry = TutorialKnowledgeEntry(
            youtube_url=request.youtube_url,
            category=request.category,
            status="pending",
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        entry_id = str(entry.id)

    background_tasks.add_task(
        _orchestrate_knowledge_ingest,
        entry_id=entry_id,
        youtube_url=request.youtube_url,
        category=request.category,
        extra_context=request.extra_context,
    )

    return IngestResponse(
        entry_id=entry_id,
        status="pending",
        message=f"Analysis queued for {request.youtube_url}. Category: {request.category}.",
    )


@router.get("/")
async def list_entries(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=200),
):
    """List all knowledge entries, newest first. Optionally filter by category or status."""
    async with AsyncSessionLocal() as session:
        stmt = select(TutorialKnowledgeEntry).order_by(desc(TutorialKnowledgeEntry.created_at))
        if category:
            stmt = stmt.where(TutorialKnowledgeEntry.category == category)
        if status:
            stmt = stmt.where(TutorialKnowledgeEntry.status == status)
        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        entries = result.scalars().all()

    return {"entries": [_entry_to_dict(e) for e in entries], "total": len(entries)}


@router.get("/{entry_id}")
async def get_entry(entry_id: str):
    """Get full details for a single knowledge entry including all Gemini analysis."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TutorialKnowledgeEntry).where(
                TutorialKnowledgeEntry.id == uuid.UUID(entry_id)
            )
        )
        entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    return _entry_to_dict(entry)


@router.get("/prompts/by-category")
async def get_prompts_by_category(
    category: str = Query(..., description="Category to pull prompts for"),
    tools_filter: Optional[str] = Query(None, description="Comma-separated tool names to filter by"),
):
    """
    Return all extracted prompts for a given category, aggregated across
    all completed knowledge entries. Useful for feeding into curation.
    """
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"category must be one of {VALID_CATEGORIES}")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TutorialKnowledgeEntry).where(
                TutorialKnowledgeEntry.category == category,
                TutorialKnowledgeEntry.status == "completed",
            )
        )
        entries = result.scalars().all()

    tool_filter_list = [t.strip().lower() for t in tools_filter.split(",")] if tools_filter else []

    all_prompts = []
    for entry in entries:
        if not entry.exact_prompts:
            continue
        # If tool filter is active, only include entries mentioning those tools
        if tool_filter_list and entry.tool_names:
            entry_tools = [t.lower() for t in entry.tool_names]
            if not any(f in t for f in tool_filter_list for t in entry_tools):
                continue
        for p in entry.exact_prompts:
            all_prompts.append({
                "prompt": p,
                "source_url": entry.youtube_url,
                "tools": entry.tool_names,
                "standout_tip": entry.standout_tip,
            })

    return {
        "category": category,
        "prompt_count": len(all_prompts),
        "prompts": all_prompts,
    }
