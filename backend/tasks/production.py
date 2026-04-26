import asyncio
import logging
import os
import uuid
from typing import List, Dict, Any
from sqlalchemy import select, update
from app.db.session import AsyncSessionLocal as async_session_factory
from app.models import ProductionJob, CurationJob, ProductionScene, ProductionTrack
from app.services.media_gen_service import media_gen_service
from app.services.suno_service import suno_service

logger = logging.getLogger(__name__)

async def _update_job_status(job_id: str, status: str, error: str = None):
    async with async_session_factory() as db:
        stmt = update(ProductionJob).where(ProductionJob.id == job_id).values(
            status=status,
            error_message=error
        )
        await db.execute(stmt)
        await db.commit()

async def run_production_pipeline(job_id: str):
    """Run the full production pipeline sequentially."""
    logger.info(f"Starting production pipeline for job {job_id}")
    
    async with async_session_factory() as db:
        # Load job and curation info
        result = await db.execute(
            select(ProductionJob, CurationJob)
            .join(CurationJob, ProductionJob.curation_job_id == CurationJob.id)
            .where(ProductionJob.id == job_id)
        )
        row = result.one_or_none()
        if not row:
            logger.error(f"Job {job_id} not found")
            return

        job, curation = row
        brief = curation.user_approved_brief
        
        if not brief or 'storyboard' not in brief:
            await _update_job_status(job_id, "failed", "No approved storyboard found")
            return

        # 1. Initialize Scenes
        scenes = []
        for scene_data in brief['storyboard']:
            new_scene = ProductionScene(
                job_id=job.id,
                scene_number=scene_data.get('scene_index'),
                description=scene_data.get('narration'),
                image_prompt=scene_data.get('visual_prompt'),
                image_model="SeeDream4K", # Default from plan
                status="pending"
            )
            db.add(new_scene)
            scenes.append(new_scene)
        
        # 2. Initialize Music Track
        new_track = ProductionTrack(
            job_id=job.id,
            track_number=1,
            song_prompt=brief.get('narrative_goal', 'Cinematic documentary'),
            suno_status="pending"
        )
        db.add(new_track)
        
        await db.commit()
        
        # 3. Sequential Generation
        await _update_job_status(job_id, "processing")
        
        # Generate images sequentially
        for scene in scenes:
            await _generate_scene_image_async(str(scene.id))
        
        # Generate music
        await _generate_music_track_async(str(new_track.id), brief.get('music_mood', 'Cinematic'))

async def _generate_scene_image_async(scene_id: str):
    async with async_session_factory() as db:
        result = await db.execute(select(ProductionScene).where(ProductionScene.id == scene_id))
        scene = result.scalar_one_or_none()
        if not scene: return
        
        scene.status = "generating"
        await db.commit()
        
        # Call MediaGenService
        res = await media_gen_service.generate_image(scene.image_prompt)
        
        if "error" in res:
            scene.status = "failed"
            scene.error_message = res["error"]
        else:
            scene.image_url = res["url"]
            scene.status = "completed"
            
        await db.commit()

async def _generate_music_track_async(track_id: str, mood: str):
    async with async_session_factory() as db:
        result = await db.execute(select(ProductionTrack).where(ProductionTrack.id == track_id))
        track = result.scalar_one_or_none()
        if not track: return
        
        track.suno_status = "generating"
        await db.commit()
        
        # Call SunoService
        res = await suno_service.create_track(track.song_prompt, mood=mood)
        
        if "error" in res:
            track.suno_status = "failed"
            track.error_message = res["error"]
        else:
            # Suno usually returns clip info immediately or job ID
            # Here we assume it returns something we can store
            track.suno_task_id = res.get('id', 'unknown')
            track.suno_status = "polling"
            
        await db.commit()
