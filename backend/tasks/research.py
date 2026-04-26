import asyncio
from typing import List, Optional
import logging
from app.services.youtube_service import youtube_service
from app.services.ai_service import ai_service
from app.db.session import AsyncSessionLocal
from app.models import ResearchJob, ResearchVideo
from sqlalchemy import select, update

logger = logging.getLogger(__name__)


async def _orchestrate_research(
    job_id: str, topic: str, research_brief: Optional[dict] = None
):
    async with AsyncSessionLocal() as session:
        try:
            logger.info(f"Starting research job {job_id} for topic: {topic}")

            # 1. Update job status to 'searching'
            await session.execute(
                update(ResearchJob)
                .where(ResearchJob.id == job_id)
                .values(status="searching")
            )
            await session.commit()

            # 2. Determine search queries
            # If research_brief provides youtube_search_queries, use them
            # Otherwise fall back to the raw topic string
            search_queries: List[str] = []
            if (
                research_brief
                and research_brief.get("youtube_search_queries")
            ):
                search_queries = research_brief["youtube_search_queries"]
                logger.info(
                    f"Using {len(search_queries)} queries from research brief"
                )
            else:
                search_queries = [topic]
                logger.info("No research brief — using raw topic as query")

            # 3. Search videos using all queries
            all_videos = []
            seen_ids = set()
            for query in search_queries:
                videos = youtube_service.search_videos(query)
                for v in videos:
                    if v["video_id"] not in seen_ids:
                        seen_ids.add(v["video_id"])
                        all_videos.append(v)

            if not all_videos:
                logger.warning(f"No videos found for topic: {topic}")
                await session.execute(
                    update(ResearchJob)
                    .where(ResearchJob.id == job_id)
                    .values(
                        status="failed",
                        research_summary="No videos found",
                    )
                )
                await session.commit()
                return

            logger.info(
                f"Found {len(all_videos)} unique videos. Extracting transcripts..."
            )

            # 4. Process each video
            transcripts = []
            for video_data in all_videos:
                transcript = youtube_service.get_transcript(
                    video_data["video_id"]
                )

                rv = ResearchVideo(
                    job_id=job_id,
                    video_id=video_data["video_id"],
                    title=video_data["title"],
                    description=video_data.get("description", ""),
                    thumbnail_url=video_data.get("thumbnail_url", ""),
                    url=f"https://www.youtube.com/watch?v={video_data['video_id']}",
                )
                session.add(rv)
                if transcript:
                    transcripts.append(transcript)

            await session.commit()

            # 5. AI Analysis
            if transcripts:
                logger.info(
                    f"Extracted {len(transcripts)} transcripts. Running AI analysis..."
                )
                await session.execute(
                    update(ResearchJob)
                    .where(ResearchJob.id == job_id)
                    .values(status="analyzing")
                )
                await session.commit()

                analysis_result = await ai_service.analyze_transcripts(
                    topic, transcripts
                )

                # 6. Final update
                if "error" in analysis_result:
                    await session.execute(
                        update(ResearchJob)
                        .where(ResearchJob.id == job_id)
                        .values(
                            status="failed",
                            research_summary=f"AI Analysis error: {analysis_result['error']}",
                        )
                    )
                else:
                    await session.execute(
                        update(ResearchJob)
                        .where(ResearchJob.id == job_id)
                        .values(
                            status="completed",
                            research_summary=analysis_result.get(
                                "raw_analysis", "Analysis failed"
                            ),
                        )
                    )
                await session.commit()
                logger.info(f"Research job {job_id} completed successfully.")
            else:
                logger.warning(f"No transcripts extracted for job {job_id}")
                await session.execute(
                    update(ResearchJob)
                    .where(ResearchJob.id == job_id)
                    .values(
                        status="failed",
                        research_summary="No transcripts extracted",
                    )
                )
                await session.commit()

        except Exception as e:
            logger.error(f"Research task failed: {e}", exc_info=True)
            await session.execute(
                update(ResearchJob)
                .where(ResearchJob.id == job_id)
                .values(status="failed", research_summary=str(e))
            )
            await session.commit()


