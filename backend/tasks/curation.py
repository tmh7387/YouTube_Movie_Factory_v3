import asyncio
import logging
from app.services.claude_service import claude_service
from app.db.session import AsyncSessionLocal
from app.models import ResearchJob, ResearchVideo, CurationJob
from sqlalchemy import select, update

logger = logging.getLogger(__name__)


def _build_brief_context(res_job) -> str:
    """Build the creative context block for Claude.
    Uses Research Brief if present, falls back to topic string."""
    rb = res_job.research_brief if res_job else None
    if not rb or not isinstance(rb, dict):
        return f"Topic: {res_job.genre_topic if res_job else 'Unknown'}"

    parts = [
        f"Creative Intent: {rb.get('intent_summary', '')}",
        f"Mood: {rb.get('mood', '')}",
        f"Visual Style: {rb.get('visual_style', '')}",
        f"Audio Character: {rb.get('audio_character', '')}",
    ]
    neg = rb.get("negative_constraints")
    if neg:
        parts.append("Avoid: " + ", ".join(neg))

    ref_imgs = rb.get("reference_image_descriptions")
    if ref_imgs:
        parts.append("Visual References: " + "; ".join(ref_imgs))

    # Safely handle audio_metadata — may be None, not just missing
    audio_meta = rb.get("audio_metadata") or {}
    bpm = audio_meta.get("estimated_bpm")
    if bpm:
        parts.append(f"Target BPM: ~{bpm}")

    return "\n".join(p for p in parts if p.split(": ", 1)[-1])  # strip empty values

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
