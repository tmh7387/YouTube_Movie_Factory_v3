"""
Phase 6 — 4K video upscaling via Real-ESRGAN.
Requires the realesrgan-ncnn-vulkan binary in PATH or REALESRGAN_BIN env var.
Gate: settings.UPSCALING_ENABLED must be True.

Install: https://github.com/xinntao/Real-ESRGAN/releases
"""
import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class UpscaleService:
    BINARY_ENV = "REALESRGAN_BIN"
    DEFAULT_BINARY = "realesrgan-ncnn-vulkan"
    MODEL = "realesr-animevideov3"  # best for animated/AI-generated content
    SCALE = 4  # 4× → reaches 4K from 1080p input

    def _find_binary(self) -> Optional[str]:
        binary = os.environ.get(self.BINARY_ENV) or shutil.which(self.DEFAULT_BINARY)
        return binary

    async def upscale_video(self, input_path: str, output_path: str) -> Optional[str]:
        """
        Upscale a video file to 4K using Real-ESRGAN frame-by-frame.
        Returns the output path on success, None on failure.

        Real-ESRGAN works on image sequences; this function:
          1. Extracts frames via ffmpeg
          2. Upscales each frame
          3. Re-encodes to video at original fps
        """
        if not settings.UPSCALING_ENABLED:
            logger.info("Upscaling disabled — returning input path as-is")
            return input_path

        binary = self._find_binary()
        if not binary:
            logger.error(
                "realesrgan-ncnn-vulkan not found in PATH. "
                "Set REALESRGAN_BIN or install from https://github.com/xinntao/Real-ESRGAN/releases"
            )
            return None

        input_p = Path(input_path)
        frames_dir = input_p.parent / f"{input_p.stem}_frames"
        upscaled_frames_dir = input_p.parent / f"{input_p.stem}_upscaled_frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        upscaled_frames_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Extract fps
            fps = await self._get_fps(input_path)

            # 2. Extract frames
            extract_cmd = [
                "ffmpeg", "-y", "-i", input_path,
                str(frames_dir / "frame%08d.png"),
            ]
            await self._run(extract_cmd, "Frame extraction")

            # 3. Upscale frames
            upscale_cmd = [
                binary,
                "-i", str(frames_dir),
                "-o", str(upscaled_frames_dir),
                "-n", self.MODEL,
                "-s", str(self.SCALE),
                "-f", "png",
            ]
            await self._run(upscale_cmd, "Real-ESRGAN upscale")

            # 4. Re-encode to video
            encode_cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", str(upscaled_frames_dir / "frame%08d.png"),
                "-c:v", "libx264",
                "-crf", "18",
                "-preset", "slow",
                "-pix_fmt", "yuv420p",
                output_path,
            ]
            await self._run(encode_cmd, "Video re-encode")

            logger.info(f"Upscaling complete: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Upscaling failed for {input_path}: {e}")
            return None
        finally:
            # Clean up frame directories
            shutil.rmtree(frames_dir, ignore_errors=True)
            shutil.rmtree(upscaled_frames_dir, ignore_errors=True)

    async def _get_fps(self, video_path: str) -> float:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "0",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "csv=p=0",
            video_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        raw = stdout.decode().strip()
        if "/" in raw:
            num, den = raw.split("/")
            return float(num) / float(den)
        return 24.0

    async def _run(self, cmd: list, label: str):
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=1800)
        if proc.returncode != 0:
            raise RuntimeError(f"{label} failed: {stderr.decode()[:500]}")
        logger.debug(f"{label} OK")


upscale_service = UpscaleService()
