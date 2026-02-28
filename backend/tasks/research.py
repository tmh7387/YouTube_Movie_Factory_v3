import asyncio
from typing import List
from celery.utils.log import get_task_logger
from tasks.celery_app import celery_app
from app.services.youtube_service import youtube_service
from app.services.ai_service import ai_service
from app.db.session import AsyncSessionLocal
from app.models import ResearchJob, ResearchVideo
from sqlalchemy import select, update

logger = get_task_logger(__name__)

async def _orchestrate_research(job_id: str, topic: str):
    async with AsyncSessionLocal() as session:
        try:
            logger.info(f"Starting research job {job_id} for topic: {topic}")
            
            # 1. Update job status to 'searching'
            await session.execute(
                update(ResearchJob).where(ResearchJob.id == job_id).values(status="searching")
            )
            await session.commit()
            
            # 2. Search videos
            # Note: search_videos is sync, so we call it normally
            videos = youtube_service.search_videos(topic)
            if not videos:
                logger.warning(f"No videos found for topic: {topic}")
                await session.execute(
                    update(ResearchJob).where(ResearchJob.id == job_id).values(status="failed", research_summary="No videos found")
                )
                await session.commit()
                return

            logger.info(f"Found {len(videos)} videos. Extracting transcripts...")
            
            # 3. Process each video
            transcripts = []
            for video_data in videos:
                # get_transcript is sync
                transcript = youtube_service.get_transcript(video_data['video_id'])
                
                # Create ResearchVideo record (UUID job_id)
                rv = ResearchVideo(
                    job_id=job_id,
                    video_id=video_data['video_id'],
                    title=video_data['title'],
                    description=video_data.get('description', ''),
                    thumbnail_url=video_data.get('thumbnail_url', ''),
                    url=f"https://www.youtube.com/watch?v={video_data['video_id']}"
                )
                session.add(rv)
                if transcript:
                    transcripts.append(transcript)
            
            await session.commit()
            
            # 4. AI Analysis
            if transcripts:
                logger.info(f"Extracted {len(transcripts)} transcripts. Running AI analysis...")
                await session.execute(
                    update(ResearchJob).where(ResearchJob.id == job_id).values(status="analyzing")
                )
                await session.commit()
                
                analysis_result = await ai_service.analyze_transcripts(topic, transcripts)
                
                # 5. Final update
                if "error" in analysis_result:
                     await session.execute(
                        update(ResearchJob).where(ResearchJob.id == job_id).values(
                            status="failed",
                            research_summary=f"AI Analysis error: {analysis_result['error']}"
                        )
                    )
                else:
                    await session.execute(
                        update(ResearchJob).where(ResearchJob.id == job_id).values(
                            status="completed",
                            research_summary=analysis_result.get('raw_analysis', 'Analysis failed')
                        )
                    )
                await session.commit()
                logger.info(f"Research job {job_id} completed successfully.")
            else:
                logger.warning(f"No transcripts extracted for job {job_id}")
                await session.execute(
                    update(ResearchJob).where(ResearchJob.id == job_id).values(status="failed", research_summary="No transcripts extracted")
                )
                await session.commit()
                
        except Exception as e:
            logger.error(f"Research task failed: {e}", exc_info=True)
            await session.execute(
                update(ResearchJob).where(ResearchJob.id == job_id).values(status="failed", research_summary=str(e))
            )
            await session.commit()

@celery_app.task(name="tasks.research.start_research_job")
def start_research_job(job_id: str, topic: str):
    """Entry point for Celery to start the async orchestration."""
    try:
        # Create a new event loop for the thread if one doesn't exist
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(_orchestrate_research(job_id, topic))
    except Exception as e:
        logger.error(f"Failed to run async task: {e}")
        raise
