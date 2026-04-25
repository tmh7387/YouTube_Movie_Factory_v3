import asyncio
import logging
import uuid
from datetime import datetime, timezone

from celery.utils.log import get_task_logger
from sqlalchemy import update, select

from tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models import TutorialKnowledgeEntry, VideoProductionSkill
from app.services.gemini_service import gemini_service
from app.services.comment_miner_service import comment_miner_service
from app.services.skill_synthesis_service import skill_synthesis_service
from app.core.config import settings

logger = get_task_logger(__name__)


async def _orchestrate_knowledge_ingest(
    entry_id: str,
    youtube_url: str,
    category: str,
    extra_context: str = "",
):
    async with AsyncSessionLocal() as session:
        try:
            # — Phase 1: mark as analyzing —
            await session.execute(
                update(TutorialKnowledgeEntry)
                .where(TutorialKnowledgeEntry.id == entry_id)
                .values(status="analyzing")
            )
            await session.commit()

            # — Phase 2: mine comments and description for resources —
            video_id = comment_miner_service.extract_video_id(youtube_url)
            logger.info(f"[{entry_id}] Mining resources for video_id={video_id}")

            resource_data = await comment_miner_service.mine_all_resources(video_id)
            description_resources = resource_data.get("description", {})
            comment_resources = resource_data.get("top_resource_comments", [])
            aggregated = resource_data.get("aggregated", {})

            await session.execute(
                update(TutorialKnowledgeEntry)
                .where(TutorialKnowledgeEntry.id == entry_id)
                .values(
                    video_id=video_id,
                    description_resources=description_resources,
                    comment_resources=comment_resources,
                    aggregated_resources=aggregated,
                )
            )
            await session.commit()
            logger.info(
                f"[{entry_id}] Resource mining complete — "
                f"{len(aggregated.get('all_unique_urls', []))} unique URLs found"
            )

            # — Phase 3: Gemini video analysis —
            logger.info(f"[{entry_id}] Starting Gemini analysis with model={settings.GEMINI_MODEL}")
            analysis = await gemini_service.analyze_youtube_video(
                youtube_url=youtube_url,
                category=category,
                extra_context=extra_context,
            )

            if "error" in analysis:
                raise RuntimeError(f"Gemini analysis error: {analysis['error']}")

            # — Phase 4: collect Notion links — alert user, do not attempt to fetch —
            notion_links = list({
                *aggregated.get("notion_pages", []),
                *[u for u in analysis.get("resource_mentions", []) if "notion." in u],
            })
            if notion_links:
                logger.info(f"[{entry_id}] Notion links found (user action required): {notion_links}")

            # — Phase 5: save knowledge entry as completed —
            await session.execute(
                update(TutorialKnowledgeEntry)
                .where(TutorialKnowledgeEntry.id == entry_id)
                .values(
                    status="completed",
                    gemini_analysis=analysis,
                    standout_tip=analysis.get("standout_tip"),
                    exact_prompts=analysis.get("exact_prompts_shown", []),
                    tool_names=analysis.get("tool_names", []),
                    workflow_steps=analysis.get("workflow_sequence", []),
                    key_settings=analysis.get("key_settings", {}),
                    category_specific=analysis.get("category_specific", {}),
                    full_technique_summary=analysis.get("full_technique_summary"),
                    external_resources={"notion_links": notion_links} if notion_links else None,
                    gemini_model_used=settings.GEMINI_MODEL,
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()
            logger.info(
                f"[{entry_id}] Knowledge ingest complete. "
                f"Standout tip: {analysis.get('standout_tip', '')[:80]}"
            )

            # — Phase 6: synthesize skills from the analysis —
            logger.info(f"[{entry_id}] Starting skill synthesis...")
            skills_data = await skill_synthesis_service.synthesize_skills(
                knowledge_entry_id=entry_id,
                gemini_analysis=analysis,
                source_video_url=youtube_url,
            )

            skills_created = []
            for skill_dict in skills_data:
                slug = skill_dict.get("slug", "")
                if not slug:
                    continue

                # Skip if a skill with this slug already exists
                existing = await session.execute(
                    select(VideoProductionSkill).where(VideoProductionSkill.slug == slug)
                )
                if existing.scalar_one_or_none():
                    logger.info(f"[{entry_id}] Skill '{slug}' already exists — skipping")
                    continue

                # Write SKILL.md to disk
                file_path = skill_synthesis_service.write_skill_to_disk(skill_dict)

                skill = VideoProductionSkill(
                    id=uuid.uuid4(),
                    slug=slug,
                    name=skill_dict.get("name", slug),
                    description=skill_dict.get("description"),
                    skill_body=skill_dict.get("skill_body_markdown"),
                    category=skill_dict.get("category", category),
                    applicable_video_types=skill_dict.get("applicable_video_types", [category]),
                    tags=skill_dict.get("tags", []),
                    prompt_template=skill_dict.get("prompt_template"),
                    example_prompts=skill_dict.get("example_prompts", []),
                    workflow_steps=skill_dict.get("workflow_steps", []),
                    tools_tested_with=skill_dict.get("tools_tested_with", []),
                    difficulty=skill_dict.get("difficulty", "intermediate"),
                    source_video_url=youtube_url,
                    source_knowledge_entry_id=entry_id,
                    confidence_score=skill_dict.get("confidence_score", 0.8),
                    skill_file_path=file_path,
                )
                session.add(skill)
                skills_created.append(slug)

            if skills_created:
                await session.commit()
                logger.info(
                    f"[{entry_id}] Created {len(skills_created)} skill(s): {skills_created}"
                )
            else:
                logger.info(f"[{entry_id}] No new skills synthesized.")

        except Exception as e:
            logger.error(f"[{entry_id}] Knowledge ingest failed: {e}", exc_info=True)
            await session.execute(
                update(TutorialKnowledgeEntry)
                .where(TutorialKnowledgeEntry.id == entry_id)
                .values(status="failed", error_message=str(e))
            )
            await session.commit()


@celery_app.task(name="tasks.knowledge.run_knowledge_ingest")
def run_knowledge_ingest(
    entry_id: str,
    youtube_url: str,
    category: str = "general",
    extra_context: str = "",
):
    """Celery entry point — runs the full async knowledge ingestion pipeline."""
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            _orchestrate_knowledge_ingest(
                entry_id=entry_id,
                youtube_url=youtube_url,
                category=category,
                extra_context=extra_context,
            )
        )
    except Exception as e:
        logger.error(f"Celery knowledge task failed: {e}")
        raise
