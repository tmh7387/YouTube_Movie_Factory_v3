"""
Claude AI service — Creative Brief generation with vision input.
Guide §3.4 — Generates structured Creative Brief JSON from inspiration video metadata.
Also contains music prompt and image prompt generators for Stage 3.
"""
import json
import logging
from typing import Any

from anthropic import AsyncAnthropic
from app.core.config import settings

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

# ---------------------------------------------------------------------------
# §3.4 — Creative Brief System Prompt
# ---------------------------------------------------------------------------

BRIEF_SYSTEM = """
You are an AI creative director for short-form music video production.
Return ONLY valid JSON matching the CreativeBrief schema. No markdown fences,
no prose, no explanation — just the raw JSON object.

STRICT RULES for the scenes array:
1. scene_number starts at 1 and increments by 1 with no gaps.
2. Sum of all target_duration_sec values MUST be ≤ (audio_duration_hint_sec - 2.0).
   Distribute time to serve the narrative. Most scenes: 4.0–5.5s.
   Hero shots or key moments: up to 8.0s. Transitions: 3.5–4.5s.
3. When image_tail_scene is set (integer), ALWAYS set kling_mode = "pro".
   When image_tail_scene is null, set kling_mode = "std".
4. image_tail_scene should be used when:
   - A scene transitions INTO the next with visual continuity
     (e.g., a character appearing to enter the next scene's location)
   - The narrative has a dissolve/morph moment
   - A repeated location/character reappears and a visual bridge adds impact
5. motion_prompt must be a specific cinematic instruction:
   camera movement (push-in, pull-out, orbit, pan, dolly, crane),
   speed (slow, ultra-slow, normal),
   and what should be happening visually.
6. negative_prompt must list specific artefacts to avoid
   (e.g., "bright flash, lens flare, face morphing, distortion, watermark").
7. suno_music_direction should reflect the mood and energy of the inspiration videos.
""".strip()

# ---------------------------------------------------------------------------
# §5.2 — Music Prompt System
# ---------------------------------------------------------------------------

MUSIC_PROMPT_SYSTEM = """
You are a music director. Generate Suno V5 prompts for instrumental background music.
Return ONLY a JSON array of prompt strings. No prose.
Each prompt must include: genre, mood, BPM hint, key instruments, energy level.
Example: "lo-fi hip hop, 90 BPM, chill and nostalgic, vinyl crackle, mellow piano,
warm bass, soft brushed drums, study session energy"
""".strip()

# ---------------------------------------------------------------------------
# §6.1 — Image Prompt System
# ---------------------------------------------------------------------------

IMAGE_PROMPT_SYSTEM = """
You are a visual art director. Given a scene description and overall theme,
generate a detailed image generation prompt optimised for a 16:9 cinematic still.
Return ONLY the prompt string — no JSON, no labels, no explanation.
The prompt must specify: art style, subject, setting, lighting, camera angle,
colour palette, mood. Under 120 words. No negative prompts here.
""".strip()

# ---------------------------------------------------------------------------
# §7.1 — Creative Direction System
# ---------------------------------------------------------------------------

DIRECTION_SYSTEM = """
You are a film director reviewing storyboard frames.
Given a scene image, its description, the overall video theme, and
the beat timestamp window, decide the optimal animation approach.
Return ONLY valid JSON with this exact schema:
{
  "scene_number": int,
  "kling_mode": "std" | "pro",
  "motion_prompt": "string — specific camera + motion direction",
  "negative_prompt": "string — artefacts to avoid",
  "image_tail_confirmed": true | false,
  "reasoning": "string — brief explanation (for logging only)"
}

RULES:
- kling_mode must be "pro" if image_tail_confirmed is true
- motion_prompt should be precise: camera type + direction + speed + subject action
- Always include in negative_prompt: distortion, watermark, face morphing
""".strip()


# ---------------------------------------------------------------------------
# Main Creative Brief Generation (Stage 2)
# ---------------------------------------------------------------------------

async def generate_creative_brief(
    video_metadata: list[dict],
    genre_mood: str,
    num_scenes: int,
    audio_duration_hint: float,
) -> dict:
    """
    Generate a structured Creative Brief from inspiration video metadata.
    Uses Claude Opus with vision input (thumbnails).
    Guide §3.4
    """
    # Build content blocks: text description + thumbnail images
    content: list[dict[str, Any]] = []

    intro = (
        f"Genre/mood: {genre_mood}\n"
        f"Number of scenes to plan: {num_scenes}\n"
        f"Audio duration: {audio_duration_hint:.1f}s\n\n"
        f"Inspiration videos:\n"
    )
    for v in video_metadata:
        intro += f"\n- Title: {v['title']}\n  Description: {v['description'][:200]}\n"
    content.append({"type": "text", "text": intro})

    # Include thumbnails as vision input
    for v in video_metadata:
        if v.get("thumbnail_b64"):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": v["thumbnail_b64"],
                },
            })

    content.append({
        "type": "text",
        "text": (
            f"Generate a Creative Brief for a {num_scenes}-scene music video. "
            f"Return ONLY the JSON object matching the CreativeBrief schema."
        ),
    })

    response = await client.messages.create(
        model=settings.CLAUDE_CREATIVE_MODEL,
        max_tokens=6000,
        system=BRIEF_SYSTEM,
        messages=[{"role": "user", "content": content}],
    )

    raw = response.content[0].text.strip()
    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Music Prompt Generation (Stage 3 — Phase A)
# ---------------------------------------------------------------------------

async def generate_music_prompts(brief: dict, num_tracks: int) -> list[str]:
    """Generate Suno V5 music prompts from Creative Brief. Guide §5.2"""
    md = brief.get("suno_music_direction", {})
    prompt = (
        f"Genre: {md.get('genre', brief.get('genre', 'hip hop'))}\n"
        f"Mood: {md.get('mood', brief.get('mood', 'energetic'))}\n"
        f"BPM hint: {md.get('bpm_hint', 90)}\n"
        f"Style tags: {', '.join(md.get('style_tags', []))}\n"
        f"Generate {num_tracks} distinct Suno V5 instrumental prompts."
    )
    response = await client.messages.create(
        model=settings.CLAUDE_CREATIVE_MODEL,
        max_tokens=800,
        system=MUSIC_PROMPT_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Image Prompt Generation (Stage 3 — Phase B)
# ---------------------------------------------------------------------------

async def generate_image_prompts(brief: dict) -> list[str]:
    """Generate one image prompt per scene. Guide §6.1"""
    theme = brief["theme"]
    palette = ", ".join(brief.get("palette", []))
    prompts = []

    for scene in brief["scenes"]:
        user_msg = (
            f"Theme: {theme}\n"
            f"Palette: {palette}\n"
            f"Scene: {scene['description']}\n"
            f"Mood: {brief.get('mood', '')}\n"
            "Generate a 16:9 cinematic image generation prompt for this scene."
        )
        r = await client.messages.create(
            model=settings.CLAUDE_CREATIVE_MODEL,
            max_tokens=200,
            system=IMAGE_PROMPT_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        prompts.append(r.content[0].text.strip())

    return prompts


# ---------------------------------------------------------------------------
# Per-Scene Creative Direction (Stage 3 — Phase C)
# ---------------------------------------------------------------------------

async def direct_scene(
    scene_image_b64: str,
    scene_desc: str,
    theme: str,
    beat_start: float,
    beat_end: float,
    has_image_tail: bool,
) -> dict:
    """AI creative direction for a single scene. Guide §7.1"""
    response = await client.messages.create(
        model=settings.CLAUDE_CREATIVE_MODEL,
        max_tokens=400,
        system=DIRECTION_SYSTEM,
        messages=[{"role": "user", "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": scene_image_b64,
                },
            },
            {
                "type": "text",
                "text": (
                    f"Scene: {scene_desc}\n"
                    f"Theme: {theme}\n"
                    f"Beat window: {beat_start:.2f}s → {beat_end:.2f}s "
                    f"({beat_end - beat_start:.2f}s)\n"
                    f"image_tail planned: {has_image_tail}\n"
                    "Confirm or adjust the animation direction."
                ),
            },
        ]}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    return json.loads(raw)
