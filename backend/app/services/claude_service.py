import logging
import json
from typing import Dict, Any, Optional
from anthropic import AsyncAnthropic
from app.core.config import settings
from app.services.skill_loader_service import skill_loader_service

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.client = AsyncAnthropic(api_key=self.api_key)

    async def generate_creative_brief(
        self,
        analysis: str,
        style_notes: str = "",
        animation_model: str = "",
        video_type: Optional[str] = None,
        bible: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a detailed creative brief including storyboard, narration, and technical direction.
        Uses the direct Anthropic SDK with Opus model for high quality.

        When animation_model is specified (e.g. 'doubao-seedance-2-0'), relevant production
        skills are automatically loaded and injected into the system prompt so Claude writes
        model-optimized visual_prompt and motion_prompt values.

        When bible is provided, character and environment references are injected
        so Claude maintains visual consistency across all scenes.
        """
        # Load production skills relevant to the target animation model
        skills_block = await skill_loader_service.build_prompt_block(
            animation_model=animation_model or settings.SEEDANCE_VIDEO_MODEL,
            video_type=video_type,
        )

        # Build bible injection block
        bible_block = ""
        if bible and "error" not in bible:
            chars = bible.get("characters", [])
            envs = bible.get("environments", [])
            style = bible.get("style_lock", {})

            char_lines = "\n".join(
                f"- **{c.get('name', '?')}**: {c.get('physical', '')} | Wardrobe: {c.get('wardrobe', '')}"
                for c in chars
            ) if chars else "None defined"

            env_lines = "\n".join(
                f"- **{e.get('name', '?')}**: {e.get('description', '')} | Lighting: {e.get('lighting', '')}"
                for e in envs
            ) if envs else "None defined"

            rules = style.get("visual_rules", [])
            neg = style.get("negative_prompt", "")
            palette = style.get("color_palette", [])

            bible_block = f"""
## Pre-Production Bible — FOLLOW THESE RULES

### Characters (reference by name in visual_prompt)
{char_lines}

### Environments (reference by name in visual_prompt)
{env_lines}

### Style Lock
- Color Palette: {', '.join(palette) if palette else 'Not specified'}
- Visual Rules: {'; '.join(rules) if rules else 'None'}
- Negative Prompt (add to every visual_prompt): {neg}

CRITICAL: Every scene's visual_prompt MUST reference bible characters by name and
apply the style_lock rules. Use the negative prompt to avoid unwanted artifacts.
"""

        system_prompt = f"""\
You are an expert Creative Director for a high-end YouTube production house.
Transform the research analysis into a structured Creative Brief and Storyboard.

The brief MUST be a valid JSON object with the following structure:
{{
  "title": "Compelling Video Title",
  "hook": "The first 30 seconds strategy",
  "narrative_goal": "What the viewer should learn/feel",
  "music_mood": "e.g. Cinematic, Lo-fi, Tech-focused",
  "color_palette": ["Color 1", "Color 2"],
  "storyboard": [
    {{
      "scene_index": 1,
      "narration": "Exact text to be spoken by AI voiceover",
      "visual_prompt": "Detailed prompt for AI image generation — describe the scene as a single cinematic still",
      "motion_prompt": "Detailed prompt for AI video animation — describe camera movement, speed, and pacing",
      "pacing": "Fast/Slow/Steady",
      "duration": 10
    }}
  ]
}}

IMPORTANT RULES FOR PROMPTS:
- visual_prompt: Describe a photorealistic cinematic still. Include subject, environment, lighting, color grade, and composition.
- motion_prompt: Describe camera movement and speed using precise terminology. Never write vague instructions like "zoom in" — use exact camera vocabulary.

{bible_block}

{skills_block}

Focus on creating "wow" visual prompts that are descriptive and cinematic."""

        user_prompt = f"Research Analysis:\n{analysis}\n\nUser Style Notes: {style_notes}"
        
        try:
            response = await self.client.messages.create(
                model=settings.CLAUDE_CREATIVE_MODEL,
                max_tokens=4096,
                temperature=0.8,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            content = response.content[0].text.strip()

            # Strip markdown code fences Claude sometimes wraps around JSON
            if content.startswith("```"):
                content = content.split("```", 2)[1]          # drop opening fence line
                if content.startswith("json"):
                    content = content[4:]                      # drop "json" language tag
                content = content.rsplit("```", 1)[0].strip()  # drop closing fence

            brief = json.loads(content)
            logger.info(
                f"Creative brief generated: {len(brief.get('storyboard', []))} scenes, "
                f"skills injected: {bool(skills_block)}"
            )
            return brief
                
        except Exception as e:
            logger.error(f"Creative Brief generation error: {e}")
            logger.debug(f"Raw Claude response was: {locals().get('content', '<not captured>')[:500]}")
            return {"error": str(e)}

claude_service = ClaudeService()
