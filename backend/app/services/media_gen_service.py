"""
Unified image generation facade.
Routes to NanaBanana Pro (CometAPI) or GPT-Image-2 based on engine setting.
"""
import httpx
import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class MediaGenService:
    def __init__(self):
        self.comet_url = "https://api.cometapi.xyz/v1/images/generations"
        self.api_key = settings.COMETAPI_API_KEY

    # ------------------------------------------------------------------
    # NanaBanana Pro (CometAPI)
    # ------------------------------------------------------------------

    async def _nanabanana_generate(self, prompt: str, model: str = "nanabananapro") -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.comet_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "prompt": prompt,
                        "n": 1,
                        "size": "1024x1024",
                        "response_format": "url",
                    },
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "url": data["data"][0]["url"],
                    "model": model,
                    "revised_prompt": data["data"][0].get("revised_prompt", prompt),
                }
        except Exception as e:
            logger.error(f"NanaBanana generation error ({model}): {e}")
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_image(
        self,
        prompt: str,
        engine: Optional[str] = None,
        model: Optional[str] = None,
        character_description: Optional[str] = None,
        reference_image_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an image. Engine selection:
          - "nanabanana"  → NanaBanana Pro via CometAPI
          - "gpt_image_2" → GPT-Image-2 via OpenAI (with optional character references)
        Falls back to NanaBanana if engine is unrecognised or key is missing.
        """
        resolved_engine = engine or settings.DEFAULT_IMAGE_ENGINE

        if resolved_engine == "gpt_image_2" and settings.OPENAI_API_KEY:
            from app.services.gpt_image_service import gpt_image_service
            if character_description and reference_image_paths:
                return await gpt_image_service.generate_with_character(
                    prompt=prompt,
                    character_description=character_description,
                    reference_image_paths=reference_image_paths,
                )
            return await gpt_image_service.generate_image(prompt)

        resolved_model = model or settings.DEFAULT_IMAGE_MODEL or "nanabananapro"
        return await self._nanabanana_generate(prompt, resolved_model)

    async def animate_image(self, image_url: str, prompt: str = "", model: str = "Wan2.6") -> Dict[str, Any]:
        """Placeholder — actual animation goes through Kling/SeeDance services."""
        logger.info(f"animate_image called for {image_url} with {model} (stub)")
        return {"id": "job_placeholder", "status": "pending"}


media_gen_service = MediaGenService()
