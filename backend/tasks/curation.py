import asyncio
from celery.utils.log import get_task_logger
from tasks.celery_app import celery_app
from app.services.ai_service import ai_service
from app.db.session import AsyncSessionLocal
from app.models import ResearchJob, ResearchVideo, CurationJob
from sqlalchemy import select, update

logger = get_task_logger(__name__)

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
            
            transcripts = [v.transcript for v in videos if v.transcript]
            
            # 3. Fetch ResearchJob summary for extra context
            res_job_result = await session.execute(select(ResearchJob).where(ResearchJob.id == research_job_id))
            res_job = res_job_result.scalar_one_or_none()
            
            topic = res_job.genre_topic if res_job else "Unknown Topic"
            research_summary = res_job.research_summary if res_job else ""
            
            # Combine context
            combined_context = f"Topic: {topic}\n\nResearch Summary:\n{research_summary}\n\n"
            if transcripts:
                combined_context += "Selected Transcripts:\n" + "\n\n---\n\n".join(transcripts[:2]) # Top 2 for detail
            
            # 4. Generate Creative Brief
            logger.info(f"Generating brief for topic: {topic}")
            brief_result = await ai_service.generate_creative_brief(combined_context)
            
            # 5. Final update
            if "error" in brief_result:
                await session.execute(
                    update(CurationJob).where(CurationJob.id == curation_job_id).values(
                        status="error",
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
                update(CurationJob).where(CurationJob.id == curation_job_id).values(status="error")
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
