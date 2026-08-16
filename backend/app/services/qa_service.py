"""
QAService — look at what was actually generated and say whether it is usable.

Until this existed the only success criterion in the pipeline was that an HTTP call
returned and a URL could be extracted from the response. A garbled clip and a perfect
one were indistinguishable, and qa_status / qa_notes were columns with zero writers.

The vision call follows the pattern already proven in video_inspiration_service:
extract frames with ffmpeg, base64 them into Anthropic image blocks, post through
AsyncAnthropic with settings.CLAUDE_CREATIVE_MODEL.

Detect, record, stop. This service never regenerates anything — automatic remediation
is a separate decision.
"""
import base64
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from anthropic import AsyncAnthropic

from app.core.config import settings
from app.services.anthropic_response import response_text

logger = logging.getLogger(__name__)

PASS = "pass"
FAIL = "fail"
SKIPPED = "skipped"

# Scores the verdict must carry for the threshold check to mean anything.
GATED_SCORES = ("character_match", "style_match")

QA_SYSTEM_PROMPT = """\
You are a shot supervisor reviewing a single frame pulled from an AI-generated video
clip. Judge only what you can see. You are looking for clips that are unusable —
warped faces, melted hands, garbled text, wrong character, wrong environment, a shot
that ignores what was asked for — not for clips that are merely imperfect.

Return ONLY a valid JSON object, no markdown fences, with exactly this schema:
{
  "pass": true or false,
  "character_match": 0.0 to 1.0,
  "style_match": 0.0 to 1.0,
  "prompt_adherence": 0.0 to 1.0,
  "artifacts": ["short phrases naming visible defects"],
  "notes": "one or two sentences explaining the verdict"
}

Scoring:
- character_match: how well the person in frame matches the described character. Score
  1.0 when no character was specified — there is nothing to contradict.
- style_match: adherence to the colour palette and visual rules given.
- prompt_adherence: whether the frame depicts what the scene prompt asked for.
- artifacts: [] when the frame is clean. Name defects plainly, e.g. "six fingers",
  "text is illegible gibberish", "face melts at the jaw".
- pass: false if any artifact would stop a viewer, or if the frame plainly shows the
  wrong character, environment, or subject.
"""


class QAService:
    def __init__(self):
        self._client: Optional[AsyncAnthropic] = None

    # -- ffmpeg ------------------------------------------------------------

    @staticmethod
    def probe_duration(video_source: str) -> Optional[float]:
        """Clip length in seconds via ffprobe. Accepts a local path or a URL."""
        try:
            proc = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video_source,
                ],
                capture_output=True, text=True, timeout=60,
            )
            value = float(proc.stdout.strip())
            return value if value > 0 else None
        except Exception as e:
            logger.warning(f"QA: ffprobe failed for {video_source[:80]}: {e}")
            return None

    @staticmethod
    def extract_frame(video_source: str, dest: Path, at_seconds: float) -> bool:
        """Pull a single JPEG at `at_seconds`. Same invocation style as assembly_service."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            proc = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", f"{max(at_seconds, 0):.3f}",
                    "-i", video_source,
                    "-frames:v", "1",
                    "-vf", "scale=768:-1",
                    "-q:v", "3",
                    str(dest),
                    "-loglevel", "error",
                ],
                capture_output=True, text=True, timeout=180,
            )
            if proc.returncode != 0:
                logger.warning(f"QA: frame extraction failed: {proc.stderr[-300:]}")
                return False
            return dest.exists() and dest.stat().st_size > 0
        except Exception as e:
            logger.warning(f"QA: frame extraction error: {e}")
            return False

    def capture_midpoint_frame(self, video_source: str, dest: Path) -> bool:
        """Extract a frame at the clip midpoint, falling back to 1s in if unprobeable."""
        duration = self.probe_duration(video_source)
        at = (duration / 2.0) if duration else 1.0
        return self.extract_frame(video_source, dest, at)

    # -- verdict -----------------------------------------------------------

    @staticmethod
    def build_review_prompt(
        image_prompt: str,
        style_lock: Optional[dict],
        character: Optional[dict],
    ) -> str:
        style = style_lock or {}
        palette = style.get("color_palette") or []
        rules = style.get("visual_rules") or []
        negative = style.get("negative_prompt") or ""

        lines = [f"Scene prompt: {image_prompt or '(none recorded)'}", ""]

        if character:
            physical = str(character.get("physical", "")).strip()
            wardrobe = str(character.get("wardrobe", "")).strip()
            lines.append(f"Expected character: {character.get('name', 'unnamed')}")
            if physical:
                lines.append(f"  Physical: {physical}")
            if wardrobe:
                lines.append(f"  Wardrobe: {wardrobe}")
        else:
            lines.append("Expected character: none specified — score character_match 1.0.")

        lines.append("")
        lines.append(f"Colour palette: {', '.join(map(str, palette)) if palette else 'not specified'}")
        lines.append(f"Visual rules: {'; '.join(map(str, rules)) if rules else 'none'}")
        lines.append(f"Must avoid: {negative or 'nothing specified'}")
        lines.append("")
        lines.append("Return the JSON verdict now.")
        return "\n".join(lines)

    def classify(self, verdict: Dict[str, Any]) -> str:
        """Turn a verdict into pass/fail against QA_FAIL_THRESHOLD."""
        threshold = float(settings.QA_FAIL_THRESHOLD)
        for key in GATED_SCORES:
            raw = verdict.get(key)
            if raw is None:
                continue
            try:
                score = float(raw)
            except (TypeError, ValueError):
                continue
            if score < threshold:
                return FAIL
        return PASS if verdict.get("pass", False) else FAIL

    async def _ask_claude(self, frame_path: Path, review_prompt: str) -> Dict[str, Any]:
        data = base64.standard_b64encode(frame_path.read_bytes()).decode("utf-8")
        content: List[dict] = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": data},
            },
            {"type": "text", "text": review_prompt},
        ]

        if self._client is None:
            self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        response = await self._client.messages.create(
            model=settings.CLAUDE_CREATIVE_MODEL,
            max_tokens=1024,
            system=QA_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )

        raw = response_text(response).strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()
        return json.loads(raw)

    async def review_scene(
        self,
        video_source: Optional[str],
        image_prompt: str = "",
        style_lock: Optional[dict] = None,
        character: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """
        Review one generated clip.

        Returns {"status": pass|fail|skipped, "verdict": {...}}. `skipped` covers every
        case where no judgement could be formed — QA disabled, no clip, ffmpeg or the
        vision call failing. A skip is never a failure: it must not stop assembly, and
        it must not be mistaken for a pass either.
        """
        if not settings.QA_ENABLED:
            return {"status": SKIPPED, "verdict": {"reason": "QA_ENABLED is false"}}

        if not video_source:
            return {"status": SKIPPED, "verdict": {"reason": "no clip to review"}}

        with tempfile.TemporaryDirectory() as tmp_dir:
            frame = Path(tmp_dir) / "midpoint.jpg"
            if not self.capture_midpoint_frame(video_source, frame):
                return {"status": SKIPPED, "verdict": {"reason": "frame extraction failed"}}

            try:
                verdict = await self._ask_claude(
                    frame, self.build_review_prompt(image_prompt, style_lock, character)
                )
            except json.JSONDecodeError as e:
                logger.warning(f"QA: verdict was not valid JSON: {e}")
                return {"status": SKIPPED, "verdict": {"reason": f"unparseable verdict: {e}"}}
            except Exception as e:
                logger.warning(f"QA: review call failed: {e}")
                return {"status": SKIPPED, "verdict": {"reason": f"review call failed: {e}"}}

        return {"status": self.classify(verdict), "verdict": verdict}


qa_service = QAService()
