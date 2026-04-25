from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, desc, func
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
import uuid

from app.db.session import AsyncSessionLocal
from app.models import VideoProductionSkill

router = APIRouter()

VALID_CATEGORIES = {"music_video", "product_brand", "asmr", "general"}


def _skill_to_dict(s: VideoProductionSkill) -> dict:
    return {
        "id": str(s.id),
        "slug": s.slug,
        "name": s.name,
        "description": s.description,
        "category": s.category,
        "applicable_video_types": s.applicable_video_types,
        "tags": s.tags,
        "prompt_template": s.prompt_template,
        "example_prompts": s.example_prompts,
        "workflow_steps": s.workflow_steps,
        "tools_tested_with": s.tools_tested_with,
        "difficulty": s.difficulty,
        "confidence_score": float(s.confidence_score) if s.confidence_score else None,
        "usage_count": s.usage_count,
        "source_video_url": s.source_video_url,
        "skill_file_path": s.skill_file_path,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _skill_to_dict_full(s: VideoProductionSkill) -> dict:
    d = _skill_to_dict(s)
    d["skill_body"] = s.skill_body
    d["source_knowledge_entry_id"] = str(s.source_knowledge_entry_id) if s.source_knowledge_entry_id else None
    return d


@router.get("/")
async def list_skills(
    category: Optional[str] = Query(None, description="Filter by category"),
    video_type: Optional[str] = Query(None, description="Filter by applicable video type"),
    tags: Optional[str] = Query(None, description="Comma-separated tags — any match"),
    difficulty: Optional[str] = Query(None, description="beginner | intermediate | advanced"),
    limit: int = Query(50, le=200),
):
    """
    Query the global skills repository. Returns skills ordered by confidence score.
    Used by the curation pipeline to inject relevant techniques into brief generation.
    """
    async with AsyncSessionLocal() as session:
        stmt = select(VideoProductionSkill).order_by(
            desc(VideoProductionSkill.confidence_score),
            desc(VideoProductionSkill.created_at),
        )

        if category:
            stmt = stmt.where(VideoProductionSkill.category == category)
        if difficulty:
            stmt = stmt.where(VideoProductionSkill.difficulty == difficulty)
        if video_type:
            # JSONB array contains check
            stmt = stmt.where(
                VideoProductionSkill.applicable_video_types.contains([video_type])
            )
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            # Match any of the requested tags
            stmt = stmt.where(
                VideoProductionSkill.tags.contains(tag_list[:1])  # at least first tag
            )

        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        skills = result.scalars().all()

    return {
        "skills": [_skill_to_dict(s) for s in skills],
        "total": len(skills),
    }


@router.get("/for-production")
async def get_skills_for_production(
    video_type: str = Query(..., description="The video type being produced"),
    limit: int = Query(10, le=30),
):
    """
    Returns the top skills for a given video type, formatted for direct injection
    into the curation brief generation prompt. Each skill includes its full body
    so Claude can reference the technique when writing scene prompts.
    """
    if video_type not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"video_type must be one of {VALID_CATEGORIES}")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(VideoProductionSkill)
            .where(VideoProductionSkill.applicable_video_types.contains([video_type]))
            .order_by(desc(VideoProductionSkill.confidence_score))
            .limit(limit)
        )
        skills = result.scalars().all()

    formatted = []
    for s in skills:
        formatted.append({
            "slug": s.slug,
            "name": s.name,
            "description": s.description,
            "prompt_template": s.prompt_template,
            "workflow_steps": s.workflow_steps,
            "pro_tip": _extract_pro_tip(s.skill_body),
        })

    return {
        "video_type": video_type,
        "skill_count": len(formatted),
        "skills": formatted,
        # Ready-to-inject block for Claude prompts
        "prompt_injection_block": _build_prompt_injection_block(formatted),
    }


@router.get("/{skill_id_or_slug}")
async def get_skill(skill_id_or_slug: str):
    """Get full details for a single skill including the complete SKILL.md body."""
    async with AsyncSessionLocal() as session:
        # Try UUID first, fall back to slug
        try:
            uid = uuid.UUID(skill_id_or_slug)
            result = await session.execute(
                select(VideoProductionSkill).where(VideoProductionSkill.id == uid)
            )
        except ValueError:
            result = await session.execute(
                select(VideoProductionSkill).where(
                    VideoProductionSkill.slug == skill_id_or_slug
                )
            )
        skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Increment usage count
    async with AsyncSessionLocal() as session:
        await session.execute(
            VideoProductionSkill.__table__.update()
            .where(VideoProductionSkill.id == skill.id)
            .values(usage_count=skill.usage_count + 1)
        )
        await session.commit()

    return _skill_to_dict_full(skill)


def _extract_pro_tip(skill_body: Optional[str]) -> Optional[str]:
    """Pull the ## Pro tip section from a skill body."""
    if not skill_body:
        return None
    m = re.search(r"## Pro tip\s*\n+(.*?)(?=\n##|\Z)", skill_body, re.DOTALL)
    return m.group(1).strip() if m else None


def _build_prompt_injection_block(skills: list[dict]) -> str:
    """
    Formats skills into a concise block suitable for injection into
    Claude's storyboard generation system prompt.
    """
    if not skills:
        return ""
    lines = ["## Available production skills (apply where relevant)\n"]
    for s in skills:
        lines.append(f"### {s['name']}")
        lines.append(s["description"])
        if s.get("prompt_template"):
            lines.append(f"\nPrompt template:\n```\n{s['prompt_template']}\n```")
        if s.get("pro_tip"):
            lines.append(f"\nPro tip: {s['pro_tip']}")
        lines.append("")
    return "\n".join(lines)


# Import re for pro tip extraction
import re
