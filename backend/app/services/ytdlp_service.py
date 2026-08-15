"""
yt-dlp metadata and thumbnail extraction service.
Guide §3.2 — extracts title, description, thumbnail (as base64 for Claude vision).
"""
import yt_dlp
import asyncio
import base64
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


async def extract_metadata(video_ids: list[str], job_dir: str = "") -> list[dict]:
    """
    Extract title, description, and thumbnail for each selected video.
    Returns list of dicts: {video_id, title, description, thumbnail_url, thumbnail_b64}
    
    thumbnail_b64 is raw base64 (no data URI prefix) for direct use in Claude vision input.
    """
    results = []
    async with httpx.AsyncClient(timeout=30) as client:
        for vid in video_ids:
            try:
                url = f"https://www.youtube.com/watch?v={vid}"
                ydl_opts = {"quiet": True, "skip_download": True, "no_warnings": True}
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, _ydl_extract, url, ydl_opts)

                thumb_url = info.get("thumbnail", "")
                thumb_b64 = ""
                if thumb_url:
                    try:
                        r = await client.get(thumb_url)
                        if r.status_code == 200:
                            thumb_b64 = base64.b64encode(r.content).decode()
                    except Exception as e:
                        logger.warning(f"Failed to download thumbnail for {vid}: {e}")

                results.append({
                    "video_id":      vid,
                    "title":         info.get("title", ""),
                    "description":   (info.get("description", "") or "")[:500],
                    "thumbnail_url": thumb_url,
                    "thumbnail_b64": thumb_b64,
                })
            except Exception as e:
                logger.error(f"Failed to extract metadata for video {vid}: {e}")
                results.append({
                    "video_id":      vid,
                    "title":         "",
                    "description":   "",
                    "thumbnail_url": "",
                    "thumbnail_b64": "",
                })
    return results


def _ydl_extract(url: str, opts: dict) -> dict:
    """Synchronous yt-dlp extraction (run in executor)."""
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)
