"""
VideoInspirationService — Watch a video and extract bible inspiration data.

Uses yt-dlp to download, ffmpeg to extract frames, Claude vision to analyze.
Returns structured InspirationData matching the PreProductionBible schema.
"""
import asyncio
import base64
import glob
import json
import logging
import os
import subprocess
import tempfile
from typing import Optional

import yt_dlp
from anthropic import AsyncAnthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

# Maximum frames to send to Claude (cost control)
MAX_FRAMES = 80
# Extract 1 frame every N seconds
FRAME_INTERVAL_SECONDS = 3


async def extract_inspiration_from_video(video_url: str) -> dict:
    """
    Main entry point. Downloads video, extracts frames, sends to Claude,
    returns InspirationData dict.

    Returns:
        {
          "characters": [...],
          "environments": [...],
          "style_signals": {...},
          "camera_signals": {...},
          "source_video_url": str,
          "source_video_title": str,
          "error": str | None
        }
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            # Step 1: Download video
            video_path, video_title = await asyncio.to_thread(
                _download_video, video_url, tmp_dir
            )
            if not video_path:
                return {"error": "Failed to download video", "source_video_url": video_url}

            logger.info(f"Downloaded: {video_title} -> {video_path}")

            # Step 2: Extract frames
            frame_paths = await asyncio.to_thread(
                _extract_frames, video_path, tmp_dir
            )
            if not frame_paths:
                return {"error": "Failed to extract frames", "source_video_url": video_url}

            logger.info(f"Extracted {len(frame_paths)} frames")

            # Step 3: Convert frames to Claude vision content
            image_blocks = _frames_to_content_blocks(frame_paths)

            # Step 4: Send to Claude and parse response
            result = await _analyze_with_claude(image_blocks, video_title, video_url)
            return result

        except Exception as e:
            logger.error(f"Inspiration extraction failed: {e}", exc_info=True)
            return {"error": str(e), "source_video_url": video_url}


def _download_video(video_url: str, output_dir: str) -> tuple[Optional[str], str]:
    """Download video with yt-dlp. Returns (file_path, title)."""
    ydl_opts = {
        "format": "bestvideo[height<=720][ext=mp4]/best[height<=720]/best",
        "outtmpl": os.path.join(output_dir, "video.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    title = "Unknown"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            title = info.get("title", "Unknown") if info else "Unknown"
    except Exception as e:
        logger.error(f"yt-dlp download failed: {e}")
        return None, title

    files = glob.glob(os.path.join(output_dir, "video.*"))
    return (files[0] if files else None), title


def _extract_frames(video_path: str, output_dir: str) -> list[str]:
    """Extract frames with ffmpeg at FRAME_INTERVAL_SECONDS, capped at MAX_FRAMES."""
    frame_pattern = os.path.join(output_dir, "frame_%04d.jpg")
    try:
        subprocess.run(
            [
                "ffmpeg", "-i", video_path,
                "-vf", f"fps=1/{FRAME_INTERVAL_SECONDS},scale=768:-1",
                "-frames:v", str(MAX_FRAMES),
                "-q:v", "3",
                frame_pattern,
                "-y", "-loglevel", "error",
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg frame extraction failed: {e.stderr.decode()}")
        return []

    return sorted(glob.glob(os.path.join(output_dir, "frame_*.jpg")))


def _frames_to_content_blocks(frame_paths: list[str]) -> list[dict]:
    """Convert frame JPEG files to Anthropic vision content blocks."""
    blocks = []
    for path in frame_paths:
        with open(path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode("utf-8")
        blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": data,
            },
        })
    return blocks


async def _analyze_with_claude(
    image_blocks: list[dict],
    video_title: str,
    video_url: str,
) -> dict:
    """Send frames to Claude and extract structured inspiration data."""

    system_prompt = """\
You are a creative director analyzing video frames to extract character and
environment inspiration for an AI video production bible.

Your goal is creative mood/style capture — not hyper-literal frame description.
Extract the visual essence of what you see so it can inspire AI-generated
recreations of similar characters and environments.

Return ONLY a valid JSON object with this exact schema (no markdown fences):
{
  "characters": [
    {
      "name": "Descriptive creative label (e.g. 'The Ritual Dancer', 'The Elder')",
      "physical": "Physical description — build, skin tone, hair style and color, age range, distinguishing features",
      "wardrobe": "Clothing style, specific garments, colors, textures, accessories",
      "expressions": ["emotional states observed, e.g. 'contemplative', 'fierce'"],
      "role": "protagonist | supporting | background | unclear",
      "visual_keywords": ["3-6 evocative style keywords, e.g. 'avant-garde', 'sculptural', 'high-fashion'"],
      "confidence": "high | medium | low"
    }
  ],
  "environments": [
    {
      "name": "Descriptive creative label (e.g. 'The Dark Studio', 'Neon Corridor')",
      "description": "Setting description and visual character — what makes it unique",
      "lighting": "Lighting description — source, direction, quality, color temperature",
      "mood": "Atmospheric mood — 2-4 evocative words",
      "color_palette_description": "Dominant colors and overall temperature",
      "time_of_day": "dawn | day | dusk | night | timeless | unknown",
      "confidence": "high | medium | low"
    }
  ],
  "style_signals": {
    "color_grade": "Overall color treatment observed across the video",
    "visual_aesthetic": "1-3 aesthetic labels (e.g. 'dark editorial', 'cyberpunk minimalism')",
    "cinematography_notes": "Notable camera or lighting techniques that define the visual style"
  },
  "camera_signals": {
    "dominant_shot_types": ["e.g. 'medium close-up', 'extreme wide'"],
    "movement_style": "Movement description (e.g. 'slow dolly with deliberate stillness')",
    "lens_feel": "Lens character (e.g. 'slight telephoto compression, shallow DOF')"
  }
}

Rules:
- Include ALL distinct characters you observe across all frames
- Include ALL distinct environments you observe
- If you are uncertain about a detail, note it in the description rather than
  guessing — e.g. 'appears to be' or 'likely a studio setting'
- confidence: 'high' means clearly visible, 'medium' means partially visible
  or inferred, 'low' means mostly inferred from limited frames
- Do not include characters if you see only a hand or shadow with no
  usable description
"""

    # Build the user message: frames first, then text instruction
    user_content = image_blocks + [
        {
            "type": "text",
            "text": (
                f"Video title: {video_title}\n"
                f"Source: {video_url}\n\n"
                "These frames are sampled at regular intervals across the full video. "
                "Analyze them to extract character and environment inspiration. "
                "Return the JSON object as specified."
            ),
        }
    ]

    try:
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=settings.CLAUDE_CREATIVE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )

        raw = response.content[0].text.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()

        data = json.loads(raw)
        data["source_video_url"] = video_url
        data["source_video_title"] = video_title
        data["error"] = None

        logger.info(
            f"Inspiration extracted: {len(data.get('characters', []))} characters, "
            f"{len(data.get('environments', []))} environments"
        )
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Claude inspiration JSON parse error: {e}")
        return {"error": f"Failed to parse inspiration JSON: {e}", "source_video_url": video_url}
    except Exception as e:
        logger.error(f"Claude inspiration analysis error: {e}", exc_info=True)
        return {"error": str(e), "source_video_url": video_url}
