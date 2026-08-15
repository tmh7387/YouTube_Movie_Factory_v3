import httpx
import logging
import asyncio
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

COMET_BASE = "https://api.cometapi.com/v1"


class SunoService:
    def __init__(self):
        self.api_key = settings.COMETAPI_API_KEY
        self.audio_url = f"{COMET_BASE}/audio/generations"

    async def create_track(
        self,
        prompt: str,
        mood: str = "",
        make_instrumental: bool = True,
    ) -> Dict[str, Any]:
        """
        Submit a Suno music generation task, then poll until the audio URL is ready.
        Returns {"audio_url": str} or {"error": str}.
        """
        combined_prompt = f"{mood} {prompt}".strip()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.audio_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "suno_music",
                        "prompt": combined_prompt,
                        "make_instrumental": make_instrumental,
                    },
                )
                response.raise_for_status()
                data = response.json()

            logger.info(f"Suno task submitted: {data}")

            # If the response already contains an audio URL, return it immediately
            audio_url = self._extract_audio_url(data)
            if audio_url:
                logger.info(f"Suno returned audio immediately: {audio_url}")
                return {"audio_url": audio_url, "id": data.get("id", "")}

            # Otherwise poll for completion
            task_id = data.get("id") or data.get("task_id")
            if not task_id:
                return {"error": f"Suno: no task_id in response: {data}"}

            return await self._poll_audio_task(task_id)

        except httpx.HTTPStatusError as e:
            logger.error(f"Suno HTTP error: {e.response.status_code} {e.response.text[:300]}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            logger.error(f"Suno track creation error: {e}")
            return {"error": str(e)}

    async def _poll_audio_task(
        self,
        task_id: str,
        max_wait: int = 300,
        interval: int = 10,
    ) -> Dict[str, Any]:
        """Poll CometAPI until the audio generation task completes."""
        elapsed = 0
        status_url = f"{self.audio_url}/{task_id}"
        logger.info(f"Polling Suno task {task_id}...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            while elapsed < max_wait:
                await asyncio.sleep(interval)
                elapsed += interval
                try:
                    r = await client.get(
                        status_url,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                    )
                    r.raise_for_status()
                    data = r.json()
                    status = data.get("status", "")
                    logger.info(f"Suno task {task_id} status: {status} ({elapsed}s)")

                    if status in ("succeeded", "completed", "done"):
                        audio_url = self._extract_audio_url(data)
                        if audio_url:
                            return {"audio_url": audio_url, "id": task_id}
                        return {"error": f"Suno task succeeded but no audio URL found: {data}"}

                    if status in ("failed", "error", "cancelled"):
                        return {"error": f"Suno task {task_id} failed: {data.get('error', data)}"}

                except Exception as e:
                    logger.warning(f"Suno poll error for {task_id}: {e}")

        return {"error": f"Suno task {task_id} timed out after {max_wait}s"}

    @staticmethod
    def _extract_audio_url(data: dict) -> Optional[str]:
        """Try common response shapes to find the audio URL."""
        # Shape 1: data.data[0].audio_url or .url
        if "data" in data and isinstance(data["data"], list) and data["data"]:
            item = data["data"][0]
            return item.get("audio_url") or item.get("url")
        # Shape 2: top-level audio_url or url
        return data.get("audio_url") or data.get("url")

    async def poll_track(self, clip_ids: List[str]) -> List[Dict[str, Any]]:
        """Poll for the status of generated Suno clips (legacy method)."""
        try:
            ids_str = ",".join(clip_ids)
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{COMET_BASE}/audio/feed?ids={ids_str}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Suno polling error: {e}")
            return []


suno_service = SunoService()
