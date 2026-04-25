"""
Suno V5 music generation via CometAPI.
Phase 5 extension: parses lyrics from the Suno response when available.
"""
import httpx
import logging
import asyncio
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

POLL_INTERVAL = 5    # seconds
MAX_POLLS = 120      # 10-minute ceiling


class SunoService:
    def __init__(self):
        self.api_url = "https://api.cometapi.xyz/v1/audio/suno"
        self.api_key = settings.COMETAPI_API_KEY

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_track(
        self,
        prompt: str,
        mood: str = "",
        make_instrumental: bool = True,
    ) -> Dict[str, Any]:
        """
        Submit a Suno V5 generation. Returns API response (clip list or job ID).
        """
        combined_prompt = f"{mood} {prompt}".strip()
        payload: Dict[str, Any] = {
            "prompt": combined_prompt,
            "make_instrumental": make_instrumental,
            "wait_for_model": False,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    self.api_url,
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"Suno create_track error: {e}")
            return {"error": str(e)}

    async def poll_track(self, clip_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Poll clip status by IDs.
        """
        try:
            ids_str = ",".join(clip_ids)
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.api_url}/feed?ids={ids_str}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"Suno poll error: {e}")
            return []

    async def wait_for_track(self, clip_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Block until all clips in clip_ids reach a terminal state.
        Returns the final clip objects.
        """
        for _ in range(MAX_POLLS):
            await asyncio.sleep(POLL_INTERVAL)
            clips = await self.poll_track(clip_ids)
            if not clips:
                continue
            statuses = {c.get("status", "processing") for c in clips}
            if statuses.issubset({"complete", "succeeded", "error", "failed"}):
                return clips
        logger.error(f"Suno wait_for_track timed out for {clip_ids}")
        return []

    def extract_lyrics(self, clip: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Parse lyrics from a completed Suno clip response.

        Suno V5 may return lyrics in several shapes:
          clip["lyrics"] — plain string (newline-separated lines)
          clip["metadata"]["lyrics"] — same but nested
          clip["segments"] — [{text, start, end}, ...] timestamped

        Returns a list of {"text": str, "start": float, "end": float} dicts,
        or None if no lyric data is present.
        """
        # Prefer pre-timestamped segments
        if clip.get("segments"):
            return [
                {
                    "text": seg.get("text", ""),
                    "start": float(seg.get("start", 0)),
                    "end": float(seg.get("end", 0)),
                }
                for seg in clip["segments"]
            ]

        # Fall back to plain-text lyrics — assign equal duration windows
        raw: Optional[str] = (
            clip.get("lyrics")
            or (clip.get("metadata") or {}).get("lyrics")
        )
        if not raw:
            return None

        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        duration = float(clip.get("audio_length") or clip.get("duration") or 0)
        if duration and lines:
            step = duration / len(lines)
            return [
                {
                    "text": line,
                    "start": round(i * step, 2),
                    "end": round((i + 1) * step, 2),
                }
                for i, line in enumerate(lines)
            ]

        # Return text only with zero timestamps as last resort
        return [{"text": line, "start": 0.0, "end": 0.0} for line in lines]


suno_service = SunoService()
