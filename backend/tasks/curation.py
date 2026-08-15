import asyncio
import json
import logging
from app.services.claude_service import claude_service
from app.services.bible_service import generate_bible_from_context
from app.db.session import AsyncSessionLocal
from app.models import ResearchJob, ResearchVideo, CurationJob, PreProductionBible
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
                combined_context += "Selected Video Descriptions:\n" + "\n\n---\n\n".join(descriptions[:2])
            
            # 4. Resolve animation model
            from app.core.config import settings
            animation_model = ""
            curation_result = await session.execute(
                select(CurationJob).where(CurationJob.id == curation_job_id)
            )
            curation_row = curation_result.scalar_one_or_none()
            if curation_row and curation_row.video_model:
                animation_model = curation_row.video_model
            else:
                animation_model = settings.SEEDANCE_VIDEO_MODEL

            # 5. Bible — load existing or auto-generate
            bible_dict = None
            if curation_row and curation_row.bible_id:
                # Load existing bible
                bible_result = await session.execute(
                    select(PreProductionBible).where(PreProductionBible.id == curation_row.bible_id)
                )
                existing_bible = bible_result.scalar_one_or_none()
                if existing_bible:
                    bible_dict = {
                        "characters": existing_bible.characters or [],
                        "environments": existing_bible.environments or [],
                        "style_lock": existing_bible.style_lock or {},
                        "surreal_motifs": existing_bible.surreal_motifs or [],
                        "camera_specs": existing_bible.camera_specs or {},
                    }
                    logger.info(f"Using existing bible {curation_row.bible_id}")
            
            if bible_dict is None:
                # Auto-generate bible from research context
                logger.info("No bible linked — auto-generating from research context")
                research_ctx = {
                    "topic": topic,
                    "source_type": res_job.source_type if res_job else "youtube_search",
                    "text_content": combined_context[:4000],
                }
                bible_dict = await generate_bible_from_context(
                    research_context=research_ctx,
                    animation_model=animation_model,
                )
                
                if "error" not in bible_dict:
                    # Save the generated bible
                    new_bible = PreProductionBible(
                        name=f"Auto: {topic[:80]}",
                        curation_job_id=curation_job_id,
                        characters=bible_dict.get("characters", []),
                        environments=bible_dict.get("environments", []),
                        style_lock=bible_dict.get("style_lock", {}),
                        surreal_motifs=bible_dict.get("surreal_motifs", []),
                        camera_specs=bible_dict.get("camera_specs", {}),
                        process_log=[{
                            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                            "agent": "bible_service",
                            "action": "Auto-generated during curation",
                            "outcome": f"{len(bible_dict.get('characters', []))} characters, "
                                       f"{len(bible_dict.get('environments', []))} environments",
                        }],
                    )
                    session.add(new_bible)
                    await session.commit()
                    await session.refresh(new_bible)
                    
                    # Link bible to curation job
                    await session.execute(
                        update(CurationJob)
                        .where(CurationJob.id == curation_job_id)
                        .values(bible_id=new_bible.id)
                    )
                    await session.commit()
                    logger.info(f"Auto-generated bible {new_bible.id} linked to curation {curation_job_id}")
                else:
                    logger.warning(f"Bible generation failed: {bible_dict.get('error')} — proceeding without bible")
                    bible_dict = None

            # 6. Generate Creative Brief (with bible + production skill injection)
            logger.info(f"Generating brief for topic: {topic} (animation_model={animation_model})")
            brief_result = await claude_service.generate_creative_brief(
                combined_context,
                animation_model=animation_model,
                bible=bible_dict,
            )
            
            # 7. Final update
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

