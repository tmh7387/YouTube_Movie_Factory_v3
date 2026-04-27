"""
assembly_service.py — ffmpeg video assembly pipeline

Phases:
  1. Download all scene video clips to jobs/{job_id}/clips/
  2. Download music track (if available) to jobs/{job_id}/audio/
  3. Build ffmpeg concat filter list
  4. Run ffmpeg to assemble final video with music overlay
  5. Return output path + duration
"""
import asyncio
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AssemblyService:
    def __init__(self):
        self.jobs_dir = Path(settings.JOB_FILES_DIR)

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------

    async def assemble_video(
        self,
        job_id: str,
        clip_urls: List[str],
        music_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Download clips + music, then assemble with ffmpeg.
        Returns {"output_path": str, "duration": float} or {"error": str}.
        """
        job_dir = self.jobs_dir / job_id
        clips_dir = job_dir / "clips"
        audio_dir = job_dir / "audio"
        clips_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Check ffmpeg is available
        if not self._ffmpeg_available():
            return {"error": "ffmpeg not found. Install ffmpeg and ensure it is on PATH."}

        # --- Step 1: Download clips ---
        local_clips: List[Path] = []
        for i, url in enumerate(clip_urls):
            dest = clips_dir / f"scene_{i:03d}.mp4"
            err = await self._download_file(url, dest)
            if err:
                logger.warning(f"Failed to download clip {i}: {err}")
                continue
            local_clips.append(dest)

        if not local_clips:
            return {"error": "All clip downloads failed — nothing to assemble"}

        # --- Step 2: Download music ---
        music_path: Optional[Path] = None
        if music_url:
            music_dest = audio_dir / "music.mp3"
            err = await self._download_file(music_url, music_dest)
            if err:
                logger.warning(f"Music download failed: {err} — assembling without music")
            else:
                music_path = music_dest

        # --- Step 3: Write concat list ---
        concat_list = job_dir / "concat.txt"
        with open(concat_list, "w") as f:
            for clip in local_clips:
                f.write(f"file '{clip.as_posix()}'\n")

        # --- Step 4: Run ffmpeg ---
        output_path = job_dir / "assembled.mp4"
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._run_ffmpeg(concat_list, music_path, output_path),
        )
        return result

    # -------------------------------------------------------------------------
    # ffmpeg execution
    # -------------------------------------------------------------------------

    def _run_ffmpeg(
        self,
        concat_list: Path,
        music_path: Optional[Path],
        output_path: Path,
    ) -> Dict[str, Any]:
        """Build and execute the ffmpeg command. Runs synchronously (call via executor)."""
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
        ]

        if music_path and music_path.exists():
            cmd += [
                "-i", str(music_path),
                # Mix music under clips audio (or just use music if clips have no audio)
                "-filter_complex",
                "[0:a]volume=1.0[ca];[1:a]volume=0.85[ma];[ca][ma]amix=inputs=2:duration=first[aout]",
                "-map", "0:v",
                "-map", "[aout]",
            ]
        else:
            cmd += ["-map", "0:v", "-map", "0:a?"]

        cmd += [
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path),
        ]

        logger.info(f"Running ffmpeg: {' '.join(cmd)}")
        t0 = time.time()

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 min max
            )
            elapsed = time.time() - t0

            if proc.returncode != 0:
                logger.error(f"ffmpeg failed:\n{proc.stderr[-2000:]}")
                return {"error": f"ffmpeg exited {proc.returncode}: {proc.stderr[-500:]}"}

            # Get duration via ffprobe
            duration = self._probe_duration(output_path)
            size = output_path.stat().st_size if output_path.exists() else 0
            logger.info(f"Assembly complete in {elapsed:.1f}s — {duration:.1f}s video, {size / 1e6:.1f} MB")
            return {
                "output_path": str(output_path),
                "duration": duration,
                "file_size_bytes": size,
            }

        except subprocess.TimeoutExpired:
            return {"error": "ffmpeg timed out after 10 minutes"}
        except FileNotFoundError:
            return {"error": "ffmpeg binary not found on PATH"}
        except Exception as e:
            return {"error": f"ffmpeg error: {e}"}

    def _probe_duration(self, video_path: Path) -> float:
        """Use ffprobe to get video duration in seconds."""
        try:
            proc = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(video_path),
                ],
                capture_output=True, text=True, timeout=30,
            )
            return float(proc.stdout.strip())
        except Exception:
            return 0.0

    def _ffmpeg_available(self) -> bool:
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    # -------------------------------------------------------------------------
    # File download helper
    # -------------------------------------------------------------------------

    async def _download_file(self, url: str, dest: Path) -> Optional[str]:
        """Download a URL to dest. Returns error string on failure, None on success."""
        try:
            async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                async with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    with open(dest, "wb") as f:
                        async for chunk in resp.aiter_bytes(chunk_size=65536):
                            f.write(chunk)
            logger.info(f"Downloaded {url} → {dest}")
            return None
        except Exception as e:
            return str(e)


assembly_service = AssemblyService()
