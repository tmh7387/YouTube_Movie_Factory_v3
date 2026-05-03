"""
BibleService — Generate Pre-Production Bibles using Claude + loaded production skills.
"""
import json
import logging
from typing import Optional

from anthropic import AsyncAnthropic

from app.core.config import settings
from app.services.skill_loader_service import skill_loader_service

logger = logging.getLogger(__name__)


async def generate_bible_from_context(
    research_context: dict,
    style_notes: str = "",
    animation_model: str = "doubao-seedance-2-0",
) -> dict:
    """
    Generate a structured Pre-Production Bible from research context.

    Loads relevant skills (project_bible, character_consistency) and asks
    Claude Sonnet to produce a structured JSON bible matching the
    PreProductionBible schema.
    """
    # Load production skills for bible context
    skills_block = await skill_loader_service.build_prompt_block(
        animation_model=animation_model,
        contexts=["project_bible", "character_consistency"],
    )

    system_prompt = f"""\
You are an expert Pre-Production Director for a high-end AI video production house.
Given the research context below, create a detailed Pre-Production Bible that will
guide all visual consistency across the entire video.

Return ONLY a valid JSON object with this exact structure:
{{
  "characters": [
    {{
      "name": "Character Name",
      "physical": "Detailed physical description — age, build, skin tone, hair, distinguishing features",
      "wardrobe": "Clothing style and specific outfit details",
      "expressions": ["neutral", "determined", "joyful"],
      "role": "protagonist | supporting | background",
      "ref_sheet_url": null
    }}
  ],
  "environments": [
    {{
      "name": "Environment Name",
      "description": "Detailed environment description",
      "lighting": "Lighting setup — golden hour, neon, overcast, etc.",
      "mood": "Atmospheric mood — serene, tense, ethereal",
      "time_of_day": "dawn | day | dusk | night",
      "ref_sheet_url": null
    }}
  ],
  "style_lock": {{
    "color_palette": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"],
    "visual_rules": [
      "Rule 1 — e.g. All shots use shallow depth of field",
      "Rule 2 — e.g. Warm 3200K color temperature throughout"
    ],
    "negative_prompt": "Things to avoid in every prompt — e.g. text, watermark, blurry, deformed",
    "looks": "Overall visual aesthetic — e.g. cinematic film grain, dreamy soft focus",
    "angles": "Preferred camera angles — e.g. low angle hero shots, eye-level dialogue"
  }},
  "surreal_motifs": [
    {{
      "symbol": "Motif name — e.g. floating petals",
      "meaning": "What it represents narratively",
      "visual_fragment": "How it appears visually in prompts"
    }}
  ],
  "camera_specs": {{
    "default_lens": "e.g. 35mm anamorphic",
    "default_movement": "e.g. slow dolly, tracking",
    "lighting_setup": "e.g. natural + fill, three-point studio"
  }}
}}

IMPORTANT RULES:
- Be specific and cinematic in all descriptions
- Color palette should be 5 hex colors that work harmoniously
- Visual rules should be actionable directives for AI image/video generation
- Negative prompt should list common AI generation artifacts to avoid
- Every character and environment name should be unique and memorable

{skills_block}
"""

    topic = research_context.get("topic", "Unknown")
    text_content = research_context.get("text_content", "")
    source_type = research_context.get("source_type", "")

    user_prompt = f"""Research Context:
Topic: {topic}
Source Type: {source_type}

Content:
{text_content[:4000]}

Style Notes: {style_notes}

Generate the Pre-Production Bible now."""

    try:
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=settings.CLAUDE_FAST_MODEL,
            max_tokens=4096,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = response.content[0].text.strip()

        # Strip markdown code fences
        if content.startswith("```"):
            content = content.split("```", 2)[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.rsplit("```", 1)[0].strip()

        bible = json.loads(content)
        logger.info(
            f"Bible generated: {len(bible.get('characters', []))} characters, "
            f"{len(bible.get('environments', []))} environments"
        )
        return bible

    except json.JSONDecodeError as e:
        logger.error(f"Bible JSON parse error: {e}")
        return {"error": f"Failed to parse bible JSON: {e}"}
    except Exception as e:
        logger.error(f"Bible generation error: {e}", exc_info=True)
        return {"error": str(e)}
