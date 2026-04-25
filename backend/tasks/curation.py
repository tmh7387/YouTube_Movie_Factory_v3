"""
Curation pipeline task — Guide §3.5
Orchestrates: yt-dlp metadata extraction → Claude Creative Brief generation → store.
Uses BackgroundTasks (Stage 2 doesn't require Celery chord).
"""
import asyncio
import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models import ResearchJob, ResearchVideo, CurationJob
from app.services import ytdlp_service, claude_service

logger = logging.getLogger(__name__)


def _extract_genre_mood(res_job: ResearchJob) -> str:
    """Build genre/mood string from ResearchBrief if available, else topic."""
    if res_job.research_brief:
        rb = res_job.research_brief
        parts = []
        if rb.get("mood"):
            parts.append(rb["mood"])
        if rb.get("visual_style"):
            parts.append(rb["visual_style"])
        if rb.get("audio_character"):
            parts.append(rb["audio_character"])
        if parts:
            return ", ".join(parts)
    return res_job.genre_topic or "cinematic"


async def run_briefing_pipeline(curation_job_id: str, research_job_id: str, selected_video_ids: list | None = None):
    """
    Full briefing pipeline per Guide §3.5:
    1. Extract metadata via yt-dlp (thumbnails + descriptions)
    2. Generate Creative Brief via Claude (with vision input)
    3. Store brief and mark status = 'ready'
    """
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"Starting briefing pipeline for curation job {curation_job_id}")

            # Update status to 'briefing'
            await db.execute(
                update(CurationJob)
                .where(CurationJob.id == curation_job_id)
                .values(status="briefing")
            )
            await db.commit()

            # Fetch research context
            res_result = await db.execute(
                select(ResearchJob).where(ResearchJob.id == research_job_id)
            )
            res_job = res_result.scalar_one_or_none()
            if not res_job:
                raise ValueError(f"Research job {research_job_id} not found")

            # Fetch curation job for num_scenes config
            cur_result = await db.execute(
                select(CurationJob).where(CurationJob.id == curation_job_id)
            )
            cur_job = cur_result.scalar_one_or_none()

            # Resolve selected video IDs
            if not selected_video_ids:
                vid_result = await db.execute(
                    select(ResearchVideo.video_id)
                    .where(
                        ResearchVideo.job_id == research_job_id,
                        ResearchVideo.selected_for_curation == True,
                    )
                )
                selected_video_ids = [row[0] for row in vid_result.all()]

            if not selected_video_ids:
                raise ValueError("No videos selected for curation")

            # --- Step 1: Extract metadata via yt-dlp ---
            logger.info(f"Extracting metadata for {len(selected_video_ids)} videos")
            video_meta = await ytdlp_service.extract_metadata(selected_video_ids)

            # --- Step 2: Generate Creative Brief via Claude ---
            genre_mood = _extract_genre_mood(res_job)
            num_scenes = cur_job.num_scenes or 20
            audio_duration_hint = 95.0  # Default hint; adjusted by beat analysis in Stage 3

            logger.info(f"Generating creative brief: {num_scenes} scenes, genre={genre_mood}")
            brief = await claude_service.generate_creative_brief(
                video_metadata=video_meta,
                genre_mood=genre_mood,
                num_scenes=num_scenes,
                audio_duration_hint=audio_duration_hint,
            )

            # --- Step 3: Store and mark ready ---
            await db.execute(
                update(CurationJob)
                .where(CurationJob.id == curation_job_id)
                .values(
                    status="ready",
                    creative_brief=brief,
                    num_scenes=len(brief.get("scenes", [])),
                )
            )
            await db.commit()
            logger.info(f"Curation job {curation_job_id} → status=ready, {len(brief.get('scenes', []))} scenes")

        except Exception as e:
            logger.error(f"Briefing pipeline failed: {e}", exc_info=True)
            await db.execute(
                update(CurationJob)
                .where(CurationJob.id == curation_job_id)
                .values(status="failed", error_message=str(e))
            )
            await db.commit()
