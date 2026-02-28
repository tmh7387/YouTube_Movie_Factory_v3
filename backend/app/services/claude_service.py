import logging
import json
from typing import Dict, Any
from anthropic import AsyncAnthropic
from app.core.config import settings

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.client = AsyncAnthropic(api_key=self.api_key)

    async def generate_creative_brief(self, analysis: str, style_notes: str = "") -> Dict[str, Any]:
        """
        Generate a detailed creative brief including storyboard, narration, and technical direction.
        Uses the direct Anthropic SDK with Opus model for high quality.
        """
        system_prompt = """
        You are an expert Creative Director for a high-end YouTube production house.
        Transform the research analysis into a structured Creative Brief and Storyboard.
        
        The brief MUST be a valid JSON object with the following structure:
        {
          "title": "Compelling Video Title",
          "hook": "The first 30 seconds strategy",
          "narrative_goal": "What the viewer should learn/feel",
          "music_mood": "e.g. Cinematic, Lo-fi, Tech-focused",
          "color_palette": ["Color 1", "Color 2"],
          "storyboard": [
            {
              "scene_index": 1,
              "narration": "Exact text to be spoken by AI voiceover",
              "visual_prompt": "Detailed prompt for AI video generation (Midjourney/Kling style)",
              "pacing": "Fast/Slow/Steady",
              "duration": 10
            }
          ]
        }
        
        Focus on creating "wow" visual prompts that are descriptive and cinematic.
        """
        
        user_prompt = f"Research Analysis:\n{analysis}\n\nUser Style Notes: {style_notes}"
        
        try:
            response = await self.client.messages.create(
                model=settings.CLAUDE_CREATIVE_MODEL,
                max_tokens=2500,
                temperature=0.8,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            content = response.content[0].text
            # Parse the JSON response
            return json.loads(content)
                
        except Exception as e:
            logger.error(f"Creative Brief generation error via Anthropic SDK: {e}")
            return {"error": str(e)}

claude_service = ClaudeService()
