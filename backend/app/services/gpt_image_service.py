"""
OpenAI images service.
Supports standard generation and character-consistent generation via reference images.

Two things about the gpt-image family that this module has to get right, because both
fail as an HTTP 400 that only shows up against the real API:

  1. `response_format` is rejected. The gpt-image models always return base64 and the
     parameter is not in their schema — sending it returns
     {"error": {"message": "Unknown parameter: 'response_format'.", ...}}.
  2. Multiple reference images are passed by REPEATING the `image[]` multipart field.
     A dict cannot hold a repeated key, so `files` must be a list of tuples. Building
     `image[]`, `image[1]`, `image[2]` sends three differently-named fields, of which
     the API reads one.
"""
import base64
import contextlib
import logging
import httpx
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"
OPENAI_EDITS_URL = "https://api.openai.com/v1/images/edits"

# gpt-image supports 1024x1024, 1536x1024 (landscape), 1024x1536 (portrait)
LANDSCAPE_SIZE = "1536x1024"

# The edits endpoint accepts many reference images; keep the request small and cheap.
MAX_REFERENCES = 3

MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


class GPTImageService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY

    @property
    def model(self) -> str:
        return settings.OPENAI_IMAGE_MODEL

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {settings.OPENAI_API_KEY or self.api_key}"}

    @staticmethod
    def _mime_for(path: Path) -> str:
        return MIME_BY_SUFFIX.get(path.suffix.lower(), "image/png")

    @staticmethod
    def _first_image(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Pull data[0] out of an images response without assuming it is there."""
        items = data.get("data")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            return items[0]
        return None

    async def generate_image(
        self,
        prompt: str,
        size: str = LANDSCAPE_SIZE,
    ) -> Dict[str, Any]:
        """
        Standard image generation.
        Returns {"b64_json": str, ...} or {"error": str}.
        """
        if not (settings.OPENAI_API_KEY or self.api_key):
            return {"error": "OPENAI_API_KEY not configured"}

        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": "high",
            # No response_format: gpt-image models reject it and return base64 anyway.
        }

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(
                    OPENAI_IMAGES_URL,
                    headers={**self._auth_headers(), "Content-Type": "application/json"},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"OpenAI image generation HTTP {e.response.status_code}: {e.response.text[:400]}"
            )
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:300]}"}
        except Exception as e:
            logger.error(f"OpenAI image generation error: {e}")
            return {"error": str(e)}

        item = self._first_image(data)
        if item is None:
            return {"error": f"No image in OpenAI response: {str(data)[:300]}"}
        if not item.get("b64_json"):
            return {"error": f"OpenAI returned an image with no b64_json: {str(item)[:300]}"}

        return {
            "b64_json": item["b64_json"],
            "revised_prompt": item.get("revised_prompt", prompt),
            "model": self.model,
        }

    async def generate_with_character(
        self,
        prompt: str,
        character_description: str,
        reference_image_paths: List[str],
        size: str = LANDSCAPE_SIZE,
    ) -> Dict[str, Any]:
        """
        Generate a scene image anchored to reference images via the edits endpoint.

        Every reference is sent as its own `image[]` part — the API reads them as an
        array. Falls back to standard generation if no reference file exists.
        """
        if not (settings.OPENAI_API_KEY or self.api_key):
            return {"error": "OPENAI_API_KEY not configured"}

        valid_refs = [Path(p) for p in reference_image_paths if Path(p).is_file()]
        if not valid_refs:
            logger.warning("No valid reference images found; falling back to standard generation")
            return await self.generate_image(prompt, size)
        valid_refs = valid_refs[:MAX_REFERENCES]

        enriched_prompt = prompt
        if character_description.strip():
            enriched_prompt = (
                f"{prompt}\n\n"
                f"Character appearance (maintain exactly): {character_description}"
            )

        try:
            with contextlib.ExitStack() as stack:
                # A list of tuples, not a dict: `image[]` has to repeat once per file.
                files: List[tuple] = [
                    ("model", (None, self.model)),
                    ("prompt", (None, enriched_prompt)),
                    ("n", (None, "1")),
                    ("size", (None, size)),
                ]
                for ref in valid_refs:
                    handle = stack.enter_context(open(ref, "rb"))
                    files.append(("image[]", (ref.name, handle, self._mime_for(ref))))

                async with httpx.AsyncClient(timeout=300.0) as client:
                    resp = await client.post(
                        OPENAI_EDITS_URL,
                        headers=self._auth_headers(),
                        files=files,
                    )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"OpenAI edits HTTP {e.response.status_code}: {e.response.text[:400]}; falling back"
            )
            return await self.generate_image(prompt, size)
        except Exception as e:
            logger.error(f"OpenAI character generation error: {e}; falling back")
            return await self.generate_image(prompt, size)

        item = self._first_image(data)
        if item is None or not item.get("b64_json"):
            logger.warning(
                f"OpenAI edits returned no usable image ({str(data)[:200]}); falling back"
            )
            return await self.generate_image(prompt, size)

        return {
            "b64_json": item["b64_json"],
            "revised_prompt": item.get("revised_prompt", enriched_prompt),
            "model": self.model,
            "character_consistent": True,
            "ref_count": len(valid_refs),
        }

    async def save_b64_to_file(self, b64_json: str, output_path: str) -> Optional[str]:
        """Decode base64 image and write to disk. Returns path or None on error."""
        try:
            img_bytes = base64.b64decode(b64_json)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            return output_path
        except Exception as e:
            logger.error(f"Failed to save OpenAI image output: {e}")
            return None


gpt_image_service = GPTImageService()
