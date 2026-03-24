import asyncio
from celery.utils.log import get_task_logger
from tasks.celery_app import celery_app
from app.services.claude_service import claude_service
from app.db.session import AsyncSessionLocal
from app.models import ResearchJob, ResearchVideo, CurationJob
from sqlalchemy import select, update

logger = get_task_logger(__name__)


def _build_brief_context(res_job) -> str:
    """Build the creative context block for Claude.
    Uses Research Brief if present, falls back to topic string."""
    if not res_job.research_brief:
        return f"Topic: {res_job.genre_topic}"

    rb = res_job.research_brief
    parts = [
        f"Creative Intent: {rb['intent_summary']}",
        f"Mood: {rb['mood']}",
        f"Visual Style: {rb['visual_style']}",
        f"Audio Character: {rb['audio_character']}",
    ]
    if rb.get("negative_constraints"):
        parts.append("Avoid: " + ", ".join(rb["negative_constraints"]))
    if rb.get("reference_image_descriptions"):
        parts.append(
            "Visual References: " + "; ".join(rb["reference_image_descriptions"])
        )
    if rb.get("audio_metadata", {}).get("estimated_bpm"):
        parts.append(f"Target BPM: ~{rb['audio_metadata']['estimated_bpm']}")

    return "\n".join(parts)

async def _orchestrate_curation(curation_job_id: str, research_job_id: str, selected_video_ids: list):
    async with AsyncSessionLocal() as session:
        try:
            logger.info(f"Starting curation job {curation_job_id} for research {research_job_id}")
            
            # 1. Update status to 'generating_brief'
            await session.execute(
                update(CurationJob).where(CurationJob.id == curation_job_id).values(status="generating_brief")
            )
            await session.commit()
            
            # 2. Fetch specific research videos and their transcripts
            # If no specific video IDs are provided, we use the research summary or all transcripts
            query = select(ResearchVideo).where(ResearchVideo.job_id == research_job_id)
            if selected_video_ids:
                query = query.where(ResearchVideo.video_id.in_(selected_video_ids))
            
            result = await session.execute(query)
            videos = result.scalars().all()
            
            descriptions = [v.description for v in videos if v.description]
            
            # 3. Fetch ResearchJob summary for extra context
            res_job_result = await session.execute(select(ResearchJob).where(ResearchJob.id == research_job_id))
            res_job = res_job_result.scalar_one_or_none()
            
            topic = res_job.genre_topic if res_job else "Unknown Topic"
            research_summary = res_job.research_summary if res_job else ""
            
            # Build enhanced context from Research Brief if available
            brief_context = _build_brief_context(res_job) if res_job else f"Topic: {topic}"
            
            # Combine context
            combined_context = f"{brief_context}\n\nResearch Summary:\n{research_summary}\n\n"
            if descriptions:
                combined_context += "Selected Video Descriptions:\n" + "\n\n---\n\n".join(descriptions[:2]) # Top 2 for detail
            
            # 4. Generate Creative Brief
            logger.info(f"Generating brief for topic: {topic}")
            brief_result = await claude_service.generate_creative_brief(combined_context)
            
            # 5. Final update
            if "error" in brief_result:
                await session.execute(
                    update(CurationJob).where(CurationJob.id == curation_job_id).values(
                        status="failed",
                        creative_brief={"error": brief_result["error"]}
                    )
                )
            else:
                await session.execute(
                    update(CurationJob).where(CurationJob.id == curation_job_id).values(
                        status="completed",
                        creative_brief=brief_result,
                        num_scenes=len(brief_result.get("storyboard", []))
                    )
                )
            
            await session.commit()
            logger.info(f"Curation job {curation_job_id} completed successfully.")
            
        except Exception as e:
            logger.error(f"Curation task failed: {e}", exc_info=True)
            await session.execute(
                update(CurationJob).where(CurationJob.id == curation_job_id).values(status="failed")
            )
            await session.commit()

@celery_app.task(name="tasks.curation.start_curation_job")
def start_curation_job(curation_job_id: str, research_job_id: str, selected_video_ids: list = None):
    """Celery task to generate a creative brief from research results."""
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(_orchestrate_curation(curation_job_id, research_job_id, selected_video_ids))
    except Exception as e:
        logger.error(f"Failed to run curation task: {e}")
        raise
