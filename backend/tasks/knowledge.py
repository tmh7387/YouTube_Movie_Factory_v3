import asyncio
import logging
from typing import Optional
from datetime import datetime, timezone

from celery.utils.log import get_task_logger
from sqlalchemy import update

from tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models import TutorialKnowledgeEntry
from app.services.gemini_service import gemini_service
from app.services.comment_miner_service import comment_miner_service
from app.core.config import settings

logger = get_task_logger(__name__)


async def _orchestrate_knowledge_ingest(
    entry_id: str,
    youtube_url: str,
    category: str,
    extra_context: str = "",
    external_resource_url: Optional[str] = None,
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

            # — Phase 2: extract video_id and mine comments/description —
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
            logger.info(f"[{entry_id}] Resource mining complete — {len(aggregated.get('all_unique_urls', []))} unique URLs found")

            # — Phase 3: Gemini video analysis —
            logger.info(f"[{entry_id}] Starting Gemini analysis with model={settings.GEMINI_MODEL}")
            analysis = await gemini_service.analyze_youtube_video(
                youtube_url=youtube_url,
                category=category,
                extra_context=extra_context,
            )

            if "error" in analysis:
                raise RuntimeError(f"Gemini analysis error: {analysis['error']}")

            # — Phase 4: fetch and parse external Notion/resource URLs —
            external_resources = {}

            # Gather Notion pages from both: the explicit external_resource_url param
            # and any discovered in comments/description
            notion_urls_to_fetch = list(aggregated.get("notion_pages", []))
            if external_resource_url:
                notion_urls_to_fetch.insert(0, external_resource_url)

            for notion_url in notion_urls_to_fetch[:3]:  # cap at 3 to stay reasonable
                logger.info(f"[{entry_id}] Extracting Notion page: {notion_url}")
                extracted = await gemini_service.extract_notion_page_content(notion_url)
                external_resources[notion_url] = extracted

            # — Phase 5: save everything —
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
                    external_resources=external_resources if external_resources else None,
                    gemini_model_used=settings.GEMINI_MODEL,
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()
            logger.info(f"[{entry_id}] Knowledge ingest complete. Standout tip: {analysis.get('standout_tip', '')[:80]}")

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
    external_resource_url: Optional[str] = None,
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
                external_resource_url=external_resource_url,
            )
        )
    except Exception as e:
        logger.error(f"Celery knowledge task failed: {e}")
        raise
