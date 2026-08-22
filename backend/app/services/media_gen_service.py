import httpx
import asyncio
import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.services import video_models

logger = logging.getLogger(__name__)

COMET_BASE = "https://api.cometapi.com/v1"

# Correct CometAPI endpoints (verified via live testing)
IMAGE_URL = f"{COMET_BASE}/images/generations"
VIDEO_SUBMIT_URL = f"{COMET_BASE}/videos"          # POST — submit task
VIDEO_STATUS_URL = f"{COMET_BASE}/videos"          # GET  — poll: /v1/videos/{task_id}

# CometAPI task status values
TERMINAL_SUCCESS = {"succeeded", "completed", "done"}
TERMINAL_FAILURE = {"failed", "error", "cancelled"}


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
        """Generate a cinematic still using CometAPI (SeeDream/Flux models)."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    IMAGE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "prompt": prompt,
                        "n": 1,
                        "size": size,
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
        duration: Optional[int] = None,
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
        duration: Optional[int] = None,
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
    # Video Generation — Seedance 2.5 via BytePlus ModelArk (direct)
    # -------------------------------------------------------------------------
    async def animate_image_seedance25(
        self,
        image_url: str,
        prompt: str = "",
        remote_model: str = "dreamina-seedance-2-5-260628",
        duration: Optional[int] = None,
        resolution: str = "1080p",
        ratio: str = "adaptive",
        output_format: str = "mp4",
        references: Optional[List[Dict[str, str]]] = None,
        generate_audio: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate with Seedance 2.5 through the BytePlus ModelArk task API.

        Ark takes a `content` array rather than a flat image field. `image_url`
        becomes the first frame; anything in `references` is appended as extra
        assets — each item is {"type": "image_url"|"video_url", "url": ...,
        "role": "reference_image"|"reference_video"|"last_frame"}.

        Note the locking rules: first-frame generation pins the output ratio to
        the input image, so we send ratio="adaptive" whenever a first frame is
        present regardless of what the caller asked for.
        """
        if not settings.ARK_API_KEY:
            return {"error": "ARK_API_KEY is not configured — cannot reach Seedance 2.5"}

        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url},
                "role": "first_frame",
            })
            ratio = "adaptive"
        for ref in references or []:
            item_type = ref.get("type", "image_url")
            key = "image_url" if item_type == "image_url" else "video_url"
            content.append({
                "type": item_type,
                key: {"url": ref["url"]},
                "role": ref.get("role", "reference_image"),
            })

        payload: Dict[str, Any] = {
            "model": remote_model,
            "content": content,
            "resolution": resolution,
            "ratio": ratio,
            "duration": duration,
            "output_format": output_format,
            "generate_audio": generate_audio,
        }

        base = settings.ARK_BASE_URL.rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{base}/contents/generations/tasks",
                    headers={
                        "Authorization": f"Bearer {settings.ARK_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                task_data = response.json()

            task_id = task_data.get("id") or task_data.get("task_id")
            if not task_id:
                return {"error": f"No task id in Seedance 2.5 response: {task_data}"}

            logger.info(f"Seedance 2.5 task submitted: {task_id}")
            return await self._poll_ark_task(task_id, remote_model)

        except httpx.HTTPStatusError as e:
            logger.error(f"Seedance 2.5 HTTP error: {e.response.status_code} {e.response.text[:300]}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            logger.error(f"Seedance 2.5 error: {e}")
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # Video Generation — MiniMax H3 via the MiniMax open platform
    # -------------------------------------------------------------------------
    async def animate_image_minimax_h3(
        self,
        image_url: str,
        prompt: str = "",
        remote_model: str = "MiniMax-H3",
        duration: int = 6,
        resolution: str = "768P",
        ratio: str = "adaptive",
        references: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate with MiniMax H3 (v2 video generation endpoint).

        H3 refuses requests that mix keyframe roles with reference roles, so a
        first frame and `references` are mutually exclusive here: when
        references are supplied the image is dropped from the keyframe slot and
        the caller is expected to have listed it as a reference instead.

        `prompt` should already be in H3's Context-IR grammar
        (integrated_multimodal_description / overall_soundscape /
        non_diegetic_music) — see reference_documents/minimax-h3-prompting-reference.md.
        """
        if not settings.MINIMAX_API_KEY:
            return {"error": "MINIMAX_API_KEY is not configured — cannot reach MiniMax H3"}

        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        if references:
            for ref in references:
                content.append({
                    "type": ref.get("type", "image_url"),
                    "url": ref["url"],
                    "role": ref.get("role", "reference_image"),
                })
        elif image_url:
            content.append({"type": "image_url", "url": image_url, "role": "first_frame"})
            ratio = "adaptive"

        payload = {
            "model": remote_model,
            "content": content,
            "resolution": resolution,
            "duration": duration,
            "ratio": ratio,
        }

        base = settings.MINIMAX_BASE_URL.rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{base}/v2/video_generation",
                    headers={
                        "Authorization": f"Bearer {settings.MINIMAX_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                task_data = response.json()

            task_id = task_data.get("task_id")
            if not task_id:
                return {"error": f"No task_id in MiniMax H3 response: {task_data}"}

            logger.info(f"MiniMax H3 task submitted: {task_id}")
            return await self._poll_minimax_task(task_id, remote_model)

        except httpx.HTTPStatusError as e:
            logger.error(f"MiniMax H3 HTTP error: {e.response.status_code} {e.response.text[:300]}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            logger.error(f"MiniMax H3 error: {e}")
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # Unified dispatcher
    # -------------------------------------------------------------------------
    async def animate_image(
        self,
        image_url: str,
        prompt: str = "",
        model: str = "kling_video",
        duration: Optional[int] = None,
        mode: str = "std",
        input_reference: Optional[str] = None,
        references: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Route to the correct animation backend for a registry model id.

        `model` accepts either a registry id ('dreamina-seedance-2-5') or a raw
        transport name ('doubao-seedance-2-0', 'kling_video'); resolve() maps
        legacy values onto the registry so old scene rows keep working.
        """
        spec = video_models.resolve(model)
        # No house clip length. An unset duration means the caller never decided,
        # which is a planning gap — fall back to the model's own minimum so the
        # run proceeds, but do not pretend some standard length was intended.
        if duration is None:
            logger.warning(
                "animate_image called without a duration for %s; using its "
                "minimum of %ss. Callers should pass the scene's own length.",
                spec.display_name, spec.min_duration,
            )
            duration = spec.min_duration
        duration = video_models.clamp_duration(spec, duration)

        if spec.transport == video_models.TRANSPORT_BYTEPLUS_ARK:
            return await self.animate_image_seedance25(
                image_url,
                prompt,
                remote_model=spec.remote_model,
                duration=duration,
                references=references,
            )

        if spec.transport == video_models.TRANSPORT_MINIMAX_API:
            return await self.animate_image_minimax_h3(
                image_url,
                prompt,
                remote_model=spec.remote_model,
                duration=duration,
                references=references,
            )

        if spec.transport == video_models.TRANSPORT_COMFYUI:
            return {
                "error": (
                    f"{spec.display_name} is not wired up yet — see "
                    "docs/MINIMAX_H3_INTEGRATION_PLAN.md"
                )
            }

        # CometAPI gateway
        if spec.family == "seedance":
            return await self.animate_image_seedance(
                image_url, prompt, spec.remote_model, duration, input_reference=input_reference
            )
        return await self.animate_image_kling(
            image_url, prompt, spec.remote_model, duration, mode or spec.default_mode
        )

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

    async def _poll_ark_task(
        self,
        task_id: str,
        model: str,
        max_wait: int = 1800,   # 30 min — Seedance 2.5 can render up to 30s of video
        interval: int = 15,
    ) -> Dict[str, Any]:
        """Poll BytePlus ModelArk until the generation task settles."""
        base = settings.ARK_BASE_URL.rstrip("/")
        status_url = f"{base}/contents/generations/tasks/{task_id}"
        elapsed = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            while elapsed < max_wait:
                await asyncio.sleep(interval)
                elapsed += interval
                try:
                    r = await client.get(
                        status_url,
                        headers={"Authorization": f"Bearer {settings.ARK_API_KEY}"},
                    )
                    r.raise_for_status()
                    data = r.json()
                    status = (data.get("status") or "").lower()
                    logger.info(f"Ark task {task_id}: status={status} ({elapsed}s)")

                    if status in TERMINAL_SUCCESS:
                        video_url = (data.get("content") or {}).get("video_url") \
                            or self._extract_video_url(data)
                        if video_url:
                            return {"url": video_url, "model": model, "task_id": task_id}
                        return {"error": f"Ark task succeeded but no video URL found: {data}"}

                    if status in TERMINAL_FAILURE:
                        return {"error": f"Ark task {task_id} failed: {data.get('error', data)}"}

                except Exception as e:
                    logger.warning(f"Ark poll error for {task_id}: {e}")

        return {"error": f"Ark task {task_id} timed out after {max_wait}s"}

    async def _poll_minimax_task(
        self,
        task_id: str,
        model: str,
        max_wait: int = 1800,
        interval: int = 15,
    ) -> Dict[str, Any]:
        """Poll the MiniMax query-task endpoint until the H3 task settles."""
        base = settings.MINIMAX_BASE_URL.rstrip("/")
        status_url = f"{base}/v2/video_generation/{task_id}"
        elapsed = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            while elapsed < max_wait:
                await asyncio.sleep(interval)
                elapsed += interval
                try:
                    r = await client.get(
                        status_url,
                        headers={"Authorization": f"Bearer {settings.MINIMAX_API_KEY}"},
                    )
                    r.raise_for_status()
                    task = (r.json() or {}).get("task", {})
                    status = (task.get("status") or "").lower()
                    logger.info(f"MiniMax task {task_id}: status={status} ({elapsed}s)")

                    if status in TERMINAL_SUCCESS:
                        video_url = (task.get("content") or {}).get("url")
                        if video_url:
                            return {"url": video_url, "model": model, "task_id": task_id}
                        return {"error": f"MiniMax task succeeded but no video URL: {task}"}

                    if status in TERMINAL_FAILURE:
                        return {"error": f"MiniMax task {task_id} failed: {task}"}

                except Exception as e:
                    logger.warning(f"MiniMax poll error for {task_id}: {e}")

        return {"error": f"MiniMax task {task_id} timed out after {max_wait}s"}

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
