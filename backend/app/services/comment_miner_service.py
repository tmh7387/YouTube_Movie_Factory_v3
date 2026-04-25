import re
import httpx
import logging
from typing import List, Dict, Any
from googleapiclient.discovery import build
from app.core.config import settings

logger = logging.getLogger(__name__)

# Resource extraction patterns
_URL = re.compile(r"https?://[^\s\)\]\"\'<>]+")
_NOTION = re.compile(r"https?://[^\s]*notion\.(?:site|so)/[^\s\)\]\"\'<>]+")
_GDOC = re.compile(r"https?://docs\.google\.com/[^\s\)\]\"\'<>]+")
_GDRIVE = re.compile(r"https?://drive\.google\.com/[^\s\)\]\"\'<>]+")
_DISCORD = re.compile(r"https?://discord\.(?:gg|com/invite)/[^\s\)\]\"\'<>]+")
_PATREON = re.compile(r"https?://(?:www\.)?patreon\.com/[^\s\)\]\"\'<>]+")
_GUMROAD = re.compile(r"https?://[^\s]*\.gumroad\.com/[^\s\)\]\"\'<>]+")
_YOUTUBE_ID = re.compile(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})")

_RESOURCE_KEYWORDS = {
    "download", "free", "template", "prompt", "pack", "preset",
    "notion", "doc", "guide", "toolkit", "resource", "link",
    "patreon", "gumroad", "discord",
}


def _extract_resources(text: str, source: str = "unknown") -> Dict[str, Any]:
    all_urls = _URL.findall(text)
    return {
        "source": source,
        "all_urls": all_urls,
        "notion_pages": _NOTION.findall(text),
        "google_docs": _GDOC.findall(text),
        "google_drive": _GDRIVE.findall(text),
        "discord_links": _DISCORD.findall(text),
        "patreon_links": _PATREON.findall(text),
        "gumroad_links": _GUMROAD.findall(text),
        "download_adjacent": [
            u for u in all_urls
            if any(kw in u.lower() for kw in {"download", "free", "gumroad", "patreon", "notion", "docs.google", "drive.google"})
        ],
    }


class CommentMinerService:
    def __init__(self):
        try:
            self.youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
        except Exception as e:
            logger.error(f"YouTube API init failed: {e}")
            self.youtube = None

    def extract_video_id(self, url: str) -> str:
        m = _YOUTUBE_ID.search(url)
        return m.group(1) if m else ""

    def get_video_description_resources(self, video_id: str) -> Dict[str, Any]:
        """Pull description text and extract all linked resources."""
        if not self.youtube:
            return {"error": "YouTube API unavailable"}
        try:
            resp = self.youtube.videos().list(id=video_id, part="snippet").execute()
            items = resp.get("items", [])
            if not items:
                return {"error": "Video not found"}

            snippet = items[0]["snippet"]
            description = snippet.get("description", "")
            resources = _extract_resources(description, source="description")
            resources["video_title"] = snippet.get("title", "")
            resources["channel"] = snippet.get("channelTitle", "")
            resources["raw_description"] = description
            return resources
        except Exception as e:
            logger.error(f"Description mining failed for {video_id}: {e}")
            return {"error": str(e)}

    def get_comments_resources(self, video_id: str, max_comments: int = 100) -> List[Dict[str, Any]]:
        """
        Scan top comments for resource links and keyword mentions.
        Returns only comments that contain actionable resources, sorted by likes.
        """
        if not self.youtube:
            return []
        try:
            resp = self.youtube.commentThreads().list(
                videoId=video_id,
                part="snippet",
                maxResults=min(max_comments, 100),
                order="relevance",
            ).execute()
        except Exception as e:
            logger.error(f"Comment fetch failed for {video_id}: {e}")
            return []

        results = []
        for item in resp.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            text = top.get("textDisplay", "")
            likes = top.get("likeCount", 0)

            has_keyword = any(kw in text.lower() for kw in _RESOURCE_KEYWORDS)
            has_url = bool(_URL.search(text))

            if not (has_keyword or has_url):
                continue

            resources = _extract_resources(text, source="comment")
            if not resources["all_urls"] and not has_keyword:
                continue

            results.append({
                "comment_text": text[:600],
                "author": top.get("authorDisplayName", ""),
                "likes": likes,
                "resources": resources,
            })

        return sorted(results, key=lambda x: x["likes"], reverse=True)

    async def fetch_and_snapshot_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch a public URL (Notion page, Google Doc, etc.) and return
        a text snapshot for downstream Gemini processing.
        """
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; VideoFactoryBot/1.0)"},
                )
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                raw = resp.text[:50000]
                # Strip HTML tags for cleaner text
                if "html" in content_type:
                    raw = re.sub(r"<[^>]+>", " ", raw)
                    raw = re.sub(r"\s+", " ", raw).strip()
                return {"url": url, "status": resp.status_code, "content": raw, "content_type": content_type}
            return {"url": url, "status": resp.status_code, "content": "", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            logger.error(f"URL fetch failed for {url}: {e}")
            return {"url": url, "error": str(e), "content": ""}

    async def mine_all_resources(self, video_id: str) -> Dict[str, Any]:
        """
        Full resource mining pass: description + comments.
        Returns a consolidated resource map ready for the knowledge task.
        """
        description_resources = self.get_video_description_resources(video_id)
        comment_resources = self.get_comments_resources(video_id)

        # Aggregate all unique URLs across both sources
        all_urls = set(description_resources.get("all_urls", []))
        for cr in comment_resources:
            all_urls.update(cr["resources"].get("all_urls", []))

        # Classify aggregated URLs
        notion_pages = list({u for u in all_urls if _NOTION.match(u)})
        google_docs = list({u for u in all_urls if _GDOC.match(u) or _GDRIVE.match(u)})
        discord_links = list({u for u in all_urls if _DISCORD.match(u)})

        return {
            "video_id": video_id,
            "description": description_resources,
            "top_resource_comments": comment_resources[:10],
            "aggregated": {
                "all_unique_urls": list(all_urls),
                "notion_pages": notion_pages,
                "google_docs": google_docs,
                "discord_links": discord_links,
            },
        }


comment_miner_service = CommentMinerService()
