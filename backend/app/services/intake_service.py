"""Research Brief Intake Service — Claude Sonnet integration + audio metadata extraction."""

import base64
import json
import logging
from typing import List, Optional

from anthropic import AsyncAnthropic

from app.core.config import settings
from app.schemas.research import ResearchBriefResponse

logger = logging.getLogger(__name__)

INTAKE_SYSTEM_PROMPT = """\
You are a creative research director for a video production AI pipeline.
Your job is to transform a user's creative intent into a structured
Research Brief that will drive YouTube content discovery.

You will receive:
  - A topic, genre, or mood (required)
  - Optional style notes, reference image descriptions, and audio metadata
  - Optionally, the user's answer to a clarifying question you asked previously

You MUST always return a valid JSON object matching this exact schema:
{
  "research_brief": {
    "intent_summary": "...",
    "mood": "...",
    "visual_style": "...",
    "audio_character": "...",
    "youtube_search_queries": ["...", "..."],
    "filter_overrides": {
      "min_duration_sec": null,
      "max_duration_sec": null,
      "date_after": null,
      "min_views": null
    },
    "negative_constraints": [],
    "reference_image_descriptions": [],
    "audio_metadata": null
  },
  "clarifying_question": null,
  "is_complete": true
}

RULES FOR clarifying_question:
  - Ask at most ONE question per response.
  - Ask ONLY if the answer would meaningfully change the search queries
    or creative direction. For example:
      GOOD: "Is this intended to feel more introspective and quiet,
             or energetic and forward-moving?"
      BAD:  "What is the target audience?" (infer from topic)
      BAD:  "What platform will this be published on?" (irrelevant to search)
  - If you have enough context to generate confident search queries,
    set clarifying_question to null and is_complete to true.
  - A bare mood/genre topic (e.g. "lofi chill", "ambient forest") SHOULD
    trigger one question about visual direction or emotional tone.
  - A topic with style notes and/or reference images should NOT trigger
    a question unless something critical is missing.

RULES FOR youtube_search_queries:
  - Generate 4-6 distinct query strings, not variations of the same phrase.
  - Think like a video director looking for inspiration, not a viewer.
  - Include at least one query focused on visual/cinematography style.
  - Include at least one query focused on mood or emotional tone.
  - Avoid generic queries. "ambient music" is bad. "ambient drone
    nature cinematography 4K slow motion" is good.
  - Respect negative_constraints — if the user said "avoid talking heads",
    do not generate queries likely to return talking head videos.

RULES FOR filter_overrides:
  - Only set non-null values when the user's intent clearly implies them.
  - Example: "short clips" -> max_duration_sec: 120
  - Example: "recent trends" -> date_after: "2024-01-01"
  - Never invent filter values not supported by context.

Return ONLY the JSON object. No preamble, no explanation, no markdown fences."""


def _extract_audio_metadata(raw_bytes: bytes) -> dict:
    """Extract BPM and duration from uploaded audio bytes.
    Uses librosa in-memory — does not write to disk."""
    try:
        import io
        import librosa

        buffer = io.BytesIO(raw_bytes)
        y, sr = librosa.load(buffer, sr=None, mono=True)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        duration = librosa.get_duration(y=y, sr=sr)
        return {
            "estimated_bpm": round(float(tempo), 1),
            "duration_sec": round(duration, 1),
        }
    except Exception as e:
        logger.warning(f"Audio metadata extraction failed: {e}")
        return {"estimated_bpm": None, "duration_sec": None}


def _build_user_message(
    topic: str,
    style_notes: Optional[str],
    previous_answer: Optional[str],
    image_b64_list: List[str],
    audio_meta: Optional[dict],
) -> list:
    """Build the Claude message content blocks."""
    content = []

    # Text block — always present
    text_parts = [f"Topic / genre / mood: {topic}"]
    if style_notes:
        text_parts.append(f"Style notes: {style_notes}")
    if audio_meta:
        text_parts.append(
            f"Reference audio metadata: {audio_meta['duration_sec']}s, "
            f"estimated {audio_meta['estimated_bpm']} BPM"
        )
    if previous_answer:
        text_parts.append(
            f"My answer to your clarifying question: {previous_answer}"
        )

    content.append({"type": "text", "text": "\n".join(text_parts)})

    # Image blocks — add after text block
    for b64_data in image_b64_list:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": b64_data,
                },
            }
        )

    return content


async def generate_research_brief(
    topic: str,
    style_notes: Optional[str] = None,
    previous_answer: Optional[str] = None,
    image_b64_list: Optional[List[str]] = None,
    audio_meta: Optional[dict] = None,
) -> ResearchBriefResponse:
    """Call Claude Sonnet to generate a Research Brief from user intent."""
    content = _build_user_message(
        topic, style_notes, previous_answer, image_b64_list or [], audio_meta
    )

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = await client.messages.create(
        model=settings.CLAUDE_FAST_MODEL,
        max_tokens=1200,
        system=INTAKE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    raw_json = response.content[0].text
    brief_data = json.loads(raw_json)
    return ResearchBriefResponse(**brief_data)
