"""
IntakeNormalizer — Normalize any source type into a unified research context.

Routes by source_type to extract text, images, audio metadata, or bible snapshots
into a common dict structure for downstream AI analysis.
"""
import logging
from typing import Optional

import httpx
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import PreProductionBible

logger = logging.getLogger(__name__)


async def normalize_to_research_context(
    source_type: str,
    source_data: dict,
    topic: str,
) -> dict:
    """
    Normalize any source type into a unified research_context dict.

    Returns:
        {
            "topic": str,
            "source_type": str,
            "text_content": str,
            "image_urls": list[str],
            "audio_meta": dict | None,
            "bible_snapshot": dict | None,
            "video_analysis": dict | None,
        }
    """
    context = {
        "topic": topic,
        "source_type": source_type,
        "text_content": "",
        "image_urls": [],
        "audio_meta": None,
        "bible_snapshot": None,
        "video_analysis": None,
    }

    if source_type == "text_brief":
        context["text_content"] = source_data.get("text", "")

    elif source_type == "single_video":
        context = await _normalize_single_video(context, source_data)

    elif source_type == "image_board":
        context["image_urls"] = source_data.get("image_urls", [])
        context["text_content"] = source_data.get("notes", "")

    elif source_type == "audio_track":
        context["audio_meta"] = {
            "bpm": source_data.get("bpm"),
            "duration_sec": source_data.get("duration_sec"),
            "mood": source_data.get("mood", ""),
            "file_url": source_data.get("file_url", ""),
        }
        context["text_content"] = source_data.get("notes", "")

    elif source_type == "existing_bible":
        context = await _normalize_existing_bible(context, source_data)

    elif source_type == "web_article":
        context = await _normalize_web_article(context, source_data)

    elif source_type == "youtube_search":
        # Passthrough — handled by existing pipeline in research.py
        context["text_content"] = topic

    else:
        logger.warning(f"Unknown source_type: {source_type}, treating as text_brief")
        context["text_content"] = source_data.get("text", topic)

    return context


async def _normalize_single_video(context: dict, source_data: dict) -> dict:
    """Extract video details, metadata, and transcript for a single YouTube video."""
    video_url = source_data.get("video_url") or source_data.get("url", "")
    if not video_url:
        context["text_content"] = "No video URL provided"
        return context

    try:
        from app.services.youtube_service import youtube_service

        # Extract video ID from URL
        video_id = _extract_video_id(video_url)
        if not video_id:
            context["text_content"] = f"Could not parse video ID from: {video_url}"
            return context

        # Fetch full metadata (title, description, tags, duration, view count)
        metadata = youtube_service.get_video_metadata(video_id)

        # Get transcript
        transcript = youtube_service.get_transcript(video_id)

        # Build rich video_analysis dict
        context["video_analysis"] = {
            "video_id": video_id,
            "url": video_url,
            "title": metadata.get("title", "") if metadata else "",
            "description": metadata.get("description", "") if metadata else "",
            "tags": metadata.get("tags", []) if metadata else [],
            "duration": metadata.get("duration", "") if metadata else "",
            "view_count": metadata.get("view_count", 0) if metadata else 0,
            "published_at": metadata.get("published_at", "") if metadata else "",
            "transcript_available": bool(transcript),
        }

        # Build combined text content for AI consumption
        parts = []
        if metadata:
            parts.append(f"Title: {metadata.get('title', 'Unknown')}")
            parts.append(f"Description: {metadata.get('description', '')}")
            if metadata.get("tags"):
                parts.append(f"Tags: {', '.join(metadata['tags'][:20])}")
            parts.append(f"Duration: {metadata.get('duration', 'Unknown')}")
            parts.append(f"Views: {metadata.get('view_count', 'Unknown')}")
            parts.append("")

        if transcript:
            parts.append("--- TRANSCRIPT ---")
            parts.append(transcript)
        else:
            parts.append(f"No transcript available for {video_url}")

        context["text_content"] = "\n".join(parts)
        logger.info(
            f"Single video normalized: {video_id} | "
            f"metadata={'yes' if metadata else 'no'} | "
            f"transcript={'yes' if transcript else 'no'} | "
            f"text_len={len(context['text_content'])}"
        )
    except Exception as e:
        logger.error(f"Single video normalization failed: {e}", exc_info=True)
        context["text_content"] = f"Failed to analyze video: {e}"

    return context


async def _normalize_existing_bible(context: dict, source_data: dict) -> dict:
    """Load an existing PreProductionBible as context."""
    bible_id = source_data.get("bible_id")
    if not bible_id:
        context["text_content"] = "No bible_id provided"
        return context

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PreProductionBible).where(PreProductionBible.id == bible_id)
            )
            bible = result.scalar_one_or_none()

        if bible:
            context["bible_snapshot"] = {
                "name": bible.name,
                "characters": bible.characters or [],
                "environments": bible.environments or [],
                "style_lock": bible.style_lock or {},
                "surreal_motifs": bible.surreal_motifs or [],
                "camera_specs": bible.camera_specs or {},
            }
            # Build text summary for AI analysis
            char_names = [c.get("name", "?") for c in (bible.characters or [])]
            env_names = [e.get("name", "?") for e in (bible.environments or [])]
            context["text_content"] = (
                f"Existing Bible: {bible.name}\n"
                f"Characters: {', '.join(char_names)}\n"
                f"Environments: {', '.join(env_names)}\n"
                f"Style: {bible.style_lock}"
            )
        else:
            context["text_content"] = f"Bible {bible_id} not found"
    except Exception as e:
        logger.error(f"Bible snapshot failed: {e}")
        context["text_content"] = f"Failed to load bible: {e}"

    return context


async def _normalize_web_article(context: dict, source_data: dict) -> dict:
    """Fetch and extract text from a web article URL."""
    article_url = source_data.get("article_url") or source_data.get("url", "")
    if not article_url:
        context["text_content"] = "No article URL provided"
        return context

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(article_url, follow_redirects=True)
            response.raise_for_status()

        html = response.text
        # Basic HTML text extraction — strip tags
        import re
        # Remove script and style blocks
        clean = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', ' ', clean)
        # Collapse whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()

        context["text_content"] = clean[:8000]  # Cap at 8K chars
        logger.info(f"Extracted {len(clean)} chars from {article_url}")
    except Exception as e:
        logger.error(f"Web article fetch failed: {e}")
        context["text_content"] = f"Failed to fetch article: {e}"

    return context


def _extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    import re
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None
