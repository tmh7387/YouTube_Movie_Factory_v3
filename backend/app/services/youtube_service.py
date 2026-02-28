import os
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

youtube_service = YouTubeService()
