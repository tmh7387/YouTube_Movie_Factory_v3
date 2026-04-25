"""
GPT-Image-2 service (OpenAI).
Supports standard generation and character-consistent generation via reference images.
"""
import base64
import logging
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"
OPENAI_EDITS_URL = "https://api.openai.com/v1/images/edits"

# GPT-Image-2 supports 1024x1024, 1536x1024 (landscape), 1024x1536 (portrait)
LANDSCAPE_SIZE = "1536x1024"


class GPTImageService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _encode_image(self, image_path: str) -> str:
        """Return base64-encoded image content for multipart upload."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def generate_image(
        self,
        prompt: str,
        size: str = LANDSCAPE_SIZE,
    ) -> Dict[str, Any]:
        """
        Standard image generation with GPT-Image-2.
        Returns {"url": str, "b64_json": str} or {"error": str}.
        """
        if not self.api_key:
            return {"error": "OPENAI_API_KEY not configured"}

        payload = {
            "model": "gpt-image-2",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json",
            "quality": "high",
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    OPENAI_IMAGES_URL,
                    headers={**self._auth_headers(), "Content-Type": "application/json"},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                item = data["data"][0]
                return {
                    "b64_json": item.get("b64_json", ""),
                    "revised_prompt": item.get("revised_prompt", prompt),
                    "model": "gpt-image-2",
                }
        except Exception as e:
            logger.error(f"GPT-Image-2 generation error: {e}")
            return {"error": str(e)}

    async def generate_with_character(
        self,
        prompt: str,
        character_description: str,
        reference_image_paths: List[str],
        size: str = LANDSCAPE_SIZE,
    ) -> Dict[str, Any]:
        """
        Generate a scene image with character consistency using GPT-Image-2's
        image edit endpoint. Reference images are passed as multipart form data.

        Falls back to standard generation if no valid reference images exist.
        """
        if not self.api_key:
            return {"error": "OPENAI_API_KEY not configured"}

        valid_refs = [p for p in reference_image_paths if Path(p).exists()]
        if not valid_refs:
            logger.warning("No valid reference images found; falling back to standard generation")
            return await self.generate_image(prompt, size)

        # Build an enriched prompt that includes character description
        enriched_prompt = (
            f"{prompt}\n\n"
            f"Character appearance (maintain exactly): {character_description}"
        )

        # Use the edits endpoint with the first reference image as the base
        # and additional references embedded in the prompt context
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                with open(valid_refs[0], "rb") as ref_file:
                    files: Dict[str, Any] = {
                        "model": (None, "gpt-image-2"),
                        "prompt": (None, enriched_prompt),
                        "n": (None, "1"),
                        "size": (None, size),
                        "response_format": (None, "b64_json"),
                        "image[]": (Path(valid_refs[0]).name, ref_file, "image/png"),
                    }
                    # Attach additional reference images if available
                    additional_files = []
                    for ref_path in valid_refs[1:3]:  # cap at 3 refs total
                        f = open(ref_path, "rb")
                        additional_files.append(f)
                        files[f"image[{len(additional_files)}]"] = (
                            Path(ref_path).name, f, "image/png"
                        )

                    resp = await client.post(
                        OPENAI_EDITS_URL,
                        headers=self._auth_headers(),
                        files=files,
                    )
                    for f in additional_files:
                        f.close()
                    resp.raise_for_status()

                data = resp.json()
                item = data["data"][0]
                return {
                    "b64_json": item.get("b64_json", ""),
                    "revised_prompt": item.get("revised_prompt", enriched_prompt),
                    "model": "gpt-image-2",
                    "character_consistent": True,
                    "ref_count": len(valid_refs),
                }
        except Exception as e:
            logger.error(f"GPT-Image-2 character generation error: {e}; falling back")
            return await self.generate_image(prompt, size)

    async def save_b64_to_file(self, b64_json: str, output_path: str) -> Optional[str]:
        """Decode base64 image and write to disk. Returns path or None on error."""
        try:
            img_bytes = base64.b64decode(b64_json)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            return output_path
        except Exception as e:
            logger.error(f"Failed to save GPT-Image-2 output: {e}")
            return None


gpt_image_service = GPTImageService()
