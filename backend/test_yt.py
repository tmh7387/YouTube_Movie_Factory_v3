from app.services.youtube_service import youtube_service
import logging

logging.basicConfig(level=logging.INFO)

print("Starting YouTube Service test...")
videos = youtube_service.search_videos("AI Agents")
print(f"Found {len(videos)} videos")
print(videos)
