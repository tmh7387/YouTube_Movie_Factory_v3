import httpx
import logging
import asyncio
from typing import Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class SunoService:
    def __init__(self):
        self.api_url = "https://api.cometapi.xyz/v1/audio/suno"
        self.api_key = settings.COMETAPI_API_KEY

    async def create_track(self, prompt: str, mood: str = "", make_instrumental: bool = True) -> Dict[str, Any]:
        """
        Trigger Suno AI generation for a music track.
        """
        combined_prompt = f"{mood} {prompt}".strip()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": combined_prompt,
                        "make_instrumental": make_instrumental,
                        "wait_for_model": False # Asynchronous
                    }
                )
                response.raise_for_status()
                return response.json() # Usually returns a list of clips or a job ID
        except Exception as e:
            logger.error(f"Suno track creation error: {e}")
            return {"error": str(e)}

    async def poll_track(self, clip_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Poll for the status of generated Suno clips.
        """
        try:
            ids_str = ",".join(clip_ids)
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_url}/feed?ids={ids_str}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Suno polling error: {e}")
            return []

suno_service = SunoService()
