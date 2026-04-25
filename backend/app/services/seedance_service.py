"""
SeeDance 2.0 video generation service.
Follows the same submit → poll pattern as Kling, routed through CometAPI.
"""
import httpx
import asyncio
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

POLL_INTERVAL = 8   # seconds between status checks
MAX_POLLS = 90      # 12-minute ceiling


class SeeDanceService:
    def __init__(self):
        self.base_url = settings.SEEDANCE_BASE_URL
        self.api_key = settings.SEEDANCE_API_KEY or settings.COMETAPI_API_KEY

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def submit_task(
        self,
        image_url: str,
        motion_prompt: str,
        duration: int = 5,
        negative_prompt: str = "",
    ) -> Dict[str, Any]:
        """
        Submit an image-to-video task to SeeDance 2.0.
        Returns {"task_id": str} on success or {"error": str} on failure.
        """
        payload: Dict[str, Any] = {
            "model": "seedance-v2",
            "image": image_url,
            "prompt": motion_prompt,
            "duration": duration,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.base_url}/video/generations",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                task_id = data.get("id") or data.get("task_id")
                if not task_id:
                    return {"error": f"No task_id in response: {data}"}
                return {"task_id": str(task_id)}
        except Exception as e:
            logger.error(f"SeeDance submit error: {e}")
            return {"error": str(e)}

    async def poll_task(self, task_id: str) -> Dict[str, Any]:
        """
        Poll a SeeDance task until it completes or fails.
        Returns {"status": "succeed", "video_url": str} or {"status": "failed", "error": str}.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.base_url}/video/generations/{task_id}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                status = data.get("status", "processing")

                if status in ("succeed", "completed", "done"):
                    video_url = (
                        data.get("video_url")
                        or data.get("output", {}).get("video_url")
                        or (data.get("outputs") or [{}])[0].get("url")
                    )
                    return {"status": "succeed", "video_url": video_url}
                if status in ("failed", "error"):
                    return {"status": "failed", "error": data.get("error", "unknown")}
                return {"status": "processing"}
        except Exception as e:
            logger.error(f"SeeDance poll error (task {task_id}): {e}")
            return {"status": "failed", "error": str(e)}

    async def generate_video(
        self,
        image_url: str,
        motion_prompt: str,
        duration: int = 5,
        negative_prompt: str = "",
    ) -> Dict[str, Any]:
        """
        Full blocking generate: submit + poll until done.
        Returns {"video_url": str} or {"error": str}.
        """
        submit = await self.submit_task(image_url, motion_prompt, duration, negative_prompt)
        if "error" in submit:
            return submit

        task_id = submit["task_id"]
        for attempt in range(MAX_POLLS):
            await asyncio.sleep(POLL_INTERVAL)
            result = await self.poll_task(task_id)
            if result["status"] == "succeed":
                logger.info(f"SeeDance task {task_id} completed after {attempt + 1} polls")
                return {"video_url": result["video_url"], "task_id": task_id}
            if result["status"] == "failed":
                return {"error": result.get("error", "SeeDance generation failed")}

        return {"error": f"SeeDance task {task_id} timed out after {MAX_POLLS} polls"}


seedance_service = SeeDanceService()
