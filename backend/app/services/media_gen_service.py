import httpx
import asyncio
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

COMET_BASE = "https://api.cometapi.com/v1"

# Correct CometAPI endpoints (verified via live testing)
IMAGE_URL = f"{COMET_BASE}/images/generations"
VIDEO_SUBMIT_URL = f"{COMET_BASE}/videos"          # POST — submit task
VIDEO_STATUS_URL = f"{COMET_BASE}/videos"          # GET  — poll: /v1/videos/{task_id}

# CometAPI task status values
TERMINAL_SUCCESS = {"succeeded", "completed", "done"}
TERMINAL_FAILURE = {"failed", "error", "cancelled"}

# gpt-image models accept only these three sizes. Routing one through CometAPI with the
# usual 1280x720 gets the request refused.
GPT_IMAGE_LANDSCAPE = "1536x1024"


class MediaGenService:
    def __init__(self):
        self.api_key = settings.COMETAPI_API_KEY

    # -------------------------------------------------------------------------
    # Image Generation
    # -------------------------------------------------------------------------
    async def generate_image(
        self,
        prompt: str,
        model: str = "doubao-seedream-4-0-250828",
        size: str = "1280x720",
    ) -> Dict[str, Any]:
        """
        Generate a cinematic still through CometAPI.

        CometAPI is a gateway in front of several vendors, so the request that suits
        SeeDream is not the request that suits an OpenAI gpt-image model. Two things
        differ and both fail hard:

          - gpt-image rejects `response_format` outright, and returns base64 whatever
            you ask for. SeeDream returns a URL only when asked.
          - gpt-image accepts only 1024x1024, 1536x1024 and 1024x1536. A 1280x720
            request is refused.

        Returns {"url": ...} or {"b64_json": ...}; callers handle both.
        """
        is_gpt_image = "gpt-image" in model.lower() or "gpt_image" in model.lower()

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": GPT_IMAGE_LANDSCAPE if is_gpt_image else size,
        }
        if not is_gpt_image:
            payload["response_format"] = "url"

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    IMAGE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                # Do not index blindly. A shape change here used to raise KeyError out
                # of a function whose whole contract is "return {'error': ...}", which
                # crashed the caller instead of failing the scene.
                items = data.get("data")
                item = items[0] if isinstance(items, list) and items else None
                if not isinstance(item, dict):
                    logger.error(f"Unexpected image response shape ({model}): {str(data)[:300]}")
                    return {"error": f"No image in response: {str(data)[:200]}"}

                result = {
                    "model": model,
                    "revised_prompt": item.get("revised_prompt", prompt),
                }
                if item.get("url"):
                    return {**result, "url": item["url"]}
                if item.get("b64_json"):
                    return {**result, "b64_json": item["b64_json"]}

                logger.error(f"Image response carried neither url nor b64_json ({model}): {str(item)[:300]}")
                return {"error": f"No image data in response: {str(item)[:200]}"}
        except httpx.HTTPStatusError as e:
            logger.error(f"Image generation HTTP error ({model}): {e.response.status_code} {e.response.text[:300]}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            logger.error(f"Image generation error ({model}): {e}")
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # Video Generation — Seedance 2.0 via CometAPI
    # -------------------------------------------------------------------------
    async def animate_image_seedance(
        self,
        image_url: str,
        prompt: str = "",
        model: str = "doubao-seedance-2-0",
        duration: int = 5,
        input_reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Animate a still image using Seedance 2.0 via CometAPI.
        - input_reference: optional .mp4 URL for beat-sync / audio reference.
        Returns the video URL when complete (polls until done).
        """
        try:
            payload: Dict[str, Any] = {
                "model": model,
                "image": image_url,
                "prompt": prompt or "slow dolly in, cinematic lighting, subtle depth of field shift, smooth motion",
                "duration": duration,
                "n": 1,
            }
            if input_reference:
                payload["input_reference"] = input_reference
                logger.info(f"Seedance: using audio reference for beat-sync")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    VIDEO_SUBMIT_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                task_data = response.json()

            task_id = task_data.get("id") or task_data.get("task_id")
            if not task_id:
                video_url = self._extract_video_url(task_data)
                if video_url:
                    return {"url": video_url, "model": model}
                return {"error": f"No task_id in Seedance response: {task_data}"}

            logger.info(f"Seedance task submitted: {task_id}")
            return await self._poll_video_task(task_id, model)

        except httpx.HTTPStatusError as e:
            logger.error(f"Seedance HTTP error: {e.response.status_code} {e.response.text[:300]}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            logger.error(f"Seedance animation error: {e}")
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # Video Generation — Kling via CometAPI gateway
    # -------------------------------------------------------------------------
    async def animate_image_kling(
        self,
        image_url: str,
        prompt: str = "",
        model: str = "kling_video",
        duration: int = 5,
        mode: str = "std",
    ) -> Dict[str, Any]:
        """
        Animate a still using Kling video model via CometAPI gateway.
        mode: 'std' | 'pro'
        """
        try:
            payload: Dict[str, Any] = {
                "model": model,
                "image": image_url,
                "prompt": prompt or "cinematic camera movement, smooth dolly, natural motion",
                "duration": duration,
                "mode": mode,
                "n": 1,
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    VIDEO_SUBMIT_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                task_data = response.json()

            task_id = task_data.get("id") or task_data.get("task_id")
            if not task_id:
                video_url = self._extract_video_url(task_data)
                if video_url:
                    return {"url": video_url, "model": model}
                return {"error": f"No task_id in Kling response: {task_data}"}

            logger.info(f"Kling task submitted: {task_id}")
            return await self._poll_video_task(task_id, model)

        except httpx.HTTPStatusError as e:
            logger.error(f"Kling HTTP error: {e.response.status_code} {e.response.text[:300]}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            logger.error(f"Kling animation error: {e}")
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # Unified dispatcher
    # -------------------------------------------------------------------------
    async def animate_image(
        self,
        image_url: str,
        prompt: str = "",
        model: str = "kling_video",
        duration: int = 5,
        mode: str = "std",
        input_reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Route to the correct animation backend based on model name.
        - 'doubao-seedance-*'  → Seedance via CometAPI  (supports input_reference)
        - 'kling_*' or default → Kling via CometAPI
        """
        if "seedance" in model.lower():
            return await self.animate_image_seedance(
                image_url, prompt, model, duration, input_reference=input_reference
            )
        return await self.animate_image_kling(image_url, prompt, model, duration, mode)

    # -------------------------------------------------------------------------
    # Shared polling helper
    # -------------------------------------------------------------------------
    async def _poll_video_task(
        self,
        task_id: str,
        model: str,
        max_wait: int = 600,   # 10 minutes — Seedance can be slow
        interval: int = 15,
    ) -> Dict[str, Any]:
        """Poll CometAPI /v1/videos/{task_id} until the video task completes or times out."""
        elapsed = 0
        status_url = f"{VIDEO_STATUS_URL}/{task_id}"
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
                    status = (data.get("status") or "").lower()
                    progress = data.get("progress", 0)
                    logger.info(f"Video task {task_id}: status={status} progress={progress}% ({elapsed}s)")

                    if status in TERMINAL_SUCCESS:
                        video_url = self._extract_video_url(data)
                        if video_url:
                            return {"url": video_url, "model": model, "task_id": task_id}
                        return {"error": f"Task succeeded but no video URL found: {data}"}

                    if status in TERMINAL_FAILURE:
                        return {"error": f"Video task {task_id} failed: {data.get('error', data)}"}

                except Exception as e:
                    logger.warning(f"Poll error for {task_id}: {e}")

        return {"error": f"Video task {task_id} timed out after {max_wait}s"}

    @staticmethod
    def _extract_video_url(data: dict) -> Optional[str]:
        """Try various response shapes to find the video URL."""
        # Shape 1: data.data[0].url
        if "data" in data and isinstance(data["data"], list) and data["data"]:
            item = data["data"][0]
            return item.get("url") or item.get("video_url")
        # Shape 2: data.url or data.video_url
        return data.get("url") or data.get("video_url")


media_gen_service = MediaGenService()
