import os
import re
from typing import Optional
from pathlib import Path
import yt_dlp
import logging
from googleapiclient.discovery import build
from app.core.config import settings

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        try:
            self.youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API: {e}")
            self.youtube = None

    def search_videos(self, query: str, max_results: int = 5):
        """Search for videos based on a query."""
        if not self.youtube:
            return []
            
        try:
            request = self.youtube.search().list(
                q=query,
                part='snippet',
                type='video',
                maxResults=max_results,
                order='relevance'
            )
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                videos.append({
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail_url': item['snippet']['thumbnails']['high']['url']
                })
            return videos
        except Exception as e:
            logger.error(f"Error searching videos: {e}")
            return []

    def get_video_metadata(self, video_id: str):
        """Get detailed metadata for a video."""
        if not self.youtube:
            return None
            
        try:
            request = self.youtube.videos().list(
                id=video_id,
                part='snippet,statistics,contentDetails'
            )
            response = request.execute()
            
            if not response.get('items'):
                return None
                
            item = response['items'][0]
            return {
                'video_id': video_id,
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'view_count': int(item['statistics']['viewCount']),
                'published_at': item['snippet']['publishedAt'],
                'duration': item['contentDetails']['duration'],
                'tags': item['snippet'].get('tags', [])
            }
        except Exception as e:
            logger.error(f"Error fetching video metadata: {e}")
            return None

    def get_transcript(self, video_id: str):
        """
        Extract transcript text using yt-dlp.
        Note: This is a simplified version that attempts to get the first available English transcript.
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        jobs_dir = Path(__file__).parent.parent.parent / "jobs"
        if not jobs_dir.exists():
            jobs_dir.mkdir(parents=True, exist_ok=True)
            
        # Temporary file for transcript
        transcript_path = os.path.join(str(jobs_dir), f"transcript_{video_id}")
        
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'outtmpl': transcript_path,
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded transcript file (it will have an extension added)
            # yt-dlp adds .en.vtt or similar
            for ext in ['.en.vtt', '.en.ttml', '.en.srv1', '.en.srv2', '.en.srv3']:
                full_path = transcript_path + ext
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Clean up
                    os.remove(full_path)
                    return self._clean_vtt(content)
            
            return None
        except Exception as e:
            logger.error(f"Error extracting transcript: {e}")
            return None

    def _clean_vtt(self, vtt_content: str):
        """Very basic VTT cleaning to extract raw text."""
        lines = vtt_content.split('\n')
        text_lines = []
        for line in lines:
            # Skip timestamps, headers, and metadata
            if '-->' in line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
                continue
            if line.strip():
                text_lines.append(line.strip())
        
        # Deduplicate consecutive identical lines (VTT often has overlap)
        deduped = []
        for line in text_lines:
            if not deduped or line != deduped[-1]:
                deduped.append(line)
                
        return " ".join(deduped)

    def resolve_channel_id(self, channel_url: str) -> Optional[str]:
        """
        Resolve a YouTube channel URL to a channel ID.

        Supports these URL formats:
          - https://youtube.com/@handle
          - https://youtube.com/channel/UCxxxxxxxxxxxxxxxx
          - https://youtube.com/c/customname
          - https://youtube.com/user/username
        """
        # Direct channel ID embedded in URL — no API call needed
        m = re.search(r'/channel/(UC[a-zA-Z0-9_-]+)', channel_url)
        if m:
            return m.group(1)

        if not self.youtube:
            return None

        # @handle format — use forHandle parameter (YouTube API v3)
        m = re.search(r'@([a-zA-Z0-9_.-]+)', channel_url)
        if m:
            handle = m.group(1)
            try:
                response = self.youtube.channels().list(
                    forHandle=handle,
                    part='id'
                ).execute()
                items = response.get('items', [])
                if items:
                    return items[0]['id']
            except Exception as e:
                logger.error(f"Channel handle lookup failed for @{handle}: {e}")

        # /c/ or /user/ format — use forUsername (deprecated but functional)
        m = re.search(r'/(?:c|user)/([a-zA-Z0-9_.-]+)', channel_url)
        if m:
            username = m.group(1)
            try:
                response = self.youtube.channels().list(
                    forUsername=username,
                    part='id'
                ).execute()
                items = response.get('items', [])
                if items:
                    return items[0]['id']
            except Exception as e:
                logger.error(f"Channel username lookup failed for {username}: {e}")

        logger.warning(f"Could not resolve channel ID from URL: {channel_url}")
        return None

    def get_channel_metadata(self, channel_id: str) -> Optional[dict]:
        """Fetch channel name and basic statistics."""
        if not self.youtube:
            return None

        try:
            response = self.youtube.channels().list(
                id=channel_id,
                part='snippet,statistics'
            ).execute()
            items = response.get('items', [])
            if not items:
                return None
            item = items[0]
            return {
                'channel_id': channel_id,
                'name': item['snippet']['title'],
                'description': item['snippet'].get('description', ''),
                'subscriber_count': int(
                    item['statistics'].get('subscriberCount', 0)
                ),
                'video_count': int(item['statistics'].get('videoCount', 0)),
            }
        except Exception as e:
            logger.error(f"Channel metadata fetch failed for {channel_id}: {e}")
            return None

    def get_channel_top_videos(
        self, channel_id: str, max_results: int = 5
    ) -> list:
        """
        Fetch top-performing videos from a channel ordered by view count.

        Makes two API calls:
          1. search().list with channelId + order=viewCount to get video IDs
          2. videos().list to fetch full metadata for all IDs in one call

        Returns list of video metadata dicts, sorted descending by view count.
        """
        if not self.youtube:
            return []

        try:
            search_response = self.youtube.search().list(
                channelId=channel_id,
                part='snippet',
                type='video',
                order='viewCount',
                maxResults=max_results,
            ).execute()

            video_ids = [
                item['id']['videoId']
                for item in search_response.get('items', [])
            ]

            if not video_ids:
                return []

            # Fetch full metadata in one batched call
            videos_response = self.youtube.videos().list(
                id=','.join(video_ids),
                part='snippet,statistics,contentDetails'
            ).execute()

            videos = []
            for item in videos_response.get('items', []):
                videos.append({
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet'].get('description', ''),
                    'view_count': int(
                        item['statistics'].get('viewCount', 0)
                    ),
                    'duration': item['contentDetails']['duration'],
                    'tags': item['snippet'].get('tags', []),
                    'url': f"https://www.youtube.com/watch?v={item['id']}",
                })

            # Sort strictly by view count (search API order is approximate)
            videos.sort(key=lambda v: v['view_count'], reverse=True)
            return videos

        except Exception as e:
            logger.error(
                f"Channel top videos fetch failed for {channel_id}: {e}"
            )
            return []


youtube_service = YouTubeService()
