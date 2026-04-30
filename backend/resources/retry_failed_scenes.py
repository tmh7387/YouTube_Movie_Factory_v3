"""
retry_failed_scenes.py
Retries animation for scenes in 'failed' or 'animating' (stale) status.
Uses the updated production pipeline which handles expired image URLs via re-generation.

Usage: python resources/retry_failed_scenes.py <job_id>
"""
import asyncio
import sys
import logging
import os
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../env/.env'))

from sqlalchemy import select, text
from app.db.session import AsyncSessionLocal
from app.models import ProductionScene, ProductionJob
from app.services.media_gen_service import media_gen_service
from app.core.config import settings
from tasks.production import _animate_scene

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('../env/logs/retry_animations.log'),
    ]
)
logger = logging.getLogger(__name__)


COMET_BASE = "https://api.cometapi.com/v1"


async def check_comet_task(task_id: str) -> dict:
    """Poll CometAPI for a task's current state and return video URL if done."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{COMET_BASE}/videos/{task_id}",
            headers={"Authorization": f"Bearer {media_gen_service.api_key}"},
        )
        return r.json()


async def recover_animating_scene(scene: ProductionScene) -> str | None:
    """
    If a scene is stuck in 'animating' with a known task_id, poll CometAPI.
    Returns video URL if task completed, else None.
    """
    if not scene.cometapi_task_id:
        return None

    logger.info(f"Scene {scene.scene_number}: checking in-flight task {scene.cometapi_task_id}")
    data = await check_comet_task(scene.cometapi_task_id)
    status = data.get("status", "")
    logger.info(f"Scene {scene.scene_number}: CometAPI status={status} progress={data.get('progress')}%")

    if status in ("succeeded", "completed", "done"):
        url = None
        if isinstance(data.get("data"), list) and data["data"]:
            url = data["data"][0].get("url") or data["data"][0].get("video_url")
        url = url or data.get("url") or data.get("video_url")
        return url

    return None


async def run_retry(job_id: str):
    logger.info(f"=== Retry script starting for job {job_id} ===")

    async with AsyncSessionLocal() as db:
        job = await db.get(ProductionJob, job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        audio_url = getattr(job, 'music_url', None)
        logger.info(f"Audio reference URL: {audio_url or 'none'}")

        result = await db.execute(
            select(ProductionScene)
            .where(ProductionScene.job_id == job_id)
            .order_by(ProductionScene.scene_number)
        )
        scenes = result.scalars().all()

    # Classify scenes
    to_retry = []
    for s in scenes:
        if s.animation_status == "completed" and s.local_video_path:
            logger.info(f"Scene {s.scene_number}: already completed — skip")
        elif s.animation_status == "animating" and s.cometapi_task_id:
            # Try to recover the in-flight task
            video_url = await recover_animating_scene(s)
            if video_url:
                logger.info(f"Scene {s.scene_number}: recovered video from in-flight task!")
                async with AsyncSessionLocal() as db2:
                    s2 = await db2.get(ProductionScene, str(s.id))
                    s2.local_video_path = video_url
                    s2.animation_status = "completed"
                    await db2.commit()
            else:
                logger.info(f"Scene {s.scene_number}: in-flight task still running, adding to retry queue")
                to_retry.append(s)
        elif s.animation_status in ("failed", "animating", "pending", None):
            to_retry.append(s)
        else:
            logger.info(f"Scene {s.scene_number}: status={s.animation_status} — skip")

    if not to_retry:
        logger.info("No scenes to retry — all done!")
        return

    logger.info(f"Retrying {len(to_retry)} scenes: {[s.scene_number for s in to_retry]}")

    # Reset stale animating scenes before retrying
    async with AsyncSessionLocal() as db:
        for s in to_retry:
            if s.animation_status == "animating":
                scene_obj = await db.get(ProductionScene, str(s.id))
                if scene_obj:
                    scene_obj.animation_status = "failed"
                    logger.info(f"Scene {s.scene_number}: reset stale 'animating' to 'failed'")
        await db.commit()

    for scene in to_retry:
        logger.info(f"--- Retrying scene {scene.scene_number} ---")
        try:
            await _animate_scene(str(scene.id), audio_reference_url=audio_url)
        except Exception as e:
            logger.error(f"Scene {scene.scene_number} retry exception: {e}")

    # Final summary
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ProductionScene)
            .where(ProductionScene.job_id == job_id)
            .order_by(ProductionScene.scene_number)
        )
        scenes_final = result.scalars().all()

    counts = {}
    for s in scenes_final:
        status = s.animation_status or "none"
        counts[status] = counts.get(status, 0) + 1

    logger.info(f"=== Retry complete. Summary: {counts} ===")

    completed = [s for s in scenes_final if s.animation_status == "completed"]
    total = len(scenes_final)
    if len(completed) == total:
        logger.info("ALL SCENES COMPLETED — ready for assembly phase!")
    else:
        remaining = [s.scene_number for s in scenes_final if s.animation_status != "completed"]
        logger.warning(f"Still has non-completed scenes: {remaining}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <job_id>")
        sys.exit(1)
    asyncio.run(run_retry(sys.argv[1]))
