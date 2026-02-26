import asyncio
import logging
import os
import uuid
from typing import List, Dict, Any
from sqlalchemy import select, update
from tasks.celery_app import celery_app
from app.db.session import async_session_factory
from app.models import ProductionJob, CurationJob, ProductionScene, ProductionTrack
from app.services.media_gen_service import media_gen_service
from app.services.suno_service import suno_service
from celery import group, chord

logger = logging.getLogger(__name__)

async def _update_job_status(job_id: str, status: str, error: str = None):
    async with async_session_factory() as db:
        stmt = update(ProductionJob).where(ProductionJob.id == job_id).values(
            status=status,
            error_message=error
        )
        await db.execute(stmt)
        await db.commit()

@celery_app.task(name="tasks.production.start_production_job")
def start_production_job(job_id: str):
    """
    Entry point for production job. Orchestrates parallel asset generation.
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(run_production_pipeline(job_id))

async def run_production_pipeline(job_id: str):
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
        
        # 3. Trigger Parallel Generation
        # For simplicity in this iteration, we trigger them one by one asynchronously
        # In a full production env, we'd use Celery signatures for better tracking
        
        await _update_job_status(job_id, "processing")
        
        # Trigger Image Generation tasks
        image_tasks = [generate_scene_image.s(str(scene.id)) for scene in scenes]
        
        # Trigger Music Generation task
        music_task = generate_music_track.s(str(new_track.id), brief.get('music_mood', 'Cinematic'))
        
        # We can use chord to detect when all scenes are done to proceed to Phase 5
        # pipeline = chord(image_tasks)(finalize_production_assets.s(job_id))
        
        # For now, just fire and forget them as separate tasks
        for t in image_tasks:
            t.delay()
        music_task.delay()

@celery_app.task(name="tasks.production.generate_scene_image")
def generate_scene_image(scene_id: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_generate_scene_image_async(scene_id))

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

@celery_app.task(name="tasks.production.generate_music_track")
def generate_music_track(track_id: str, mood: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_generate_music_track_async(track_id, mood))

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

@celery_app.task(name="tasks.production.finalize_production_assets")
def finalize_production_assets(job_id: str):
    # This task would check if everything is ready and mark the job as "ready_for_animation"
    pass
