import httpx
import logging
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.comet_api_url = "https://api.cometapi.xyz/v1/chat/completions" # Based on standard gateway patterns
        self.comet_api_key = settings.COMETAPI_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY

    async def analyze_transcripts(self, topic: str, transcripts: List[str]) -> Dict[str, Any]:
        """
        Analyze multiple transcripts to extract key insights and a summary.
        Uses CometAPI as the primary gateway.
        """
        combined_text = "\n\n---\n\n".join(transcripts[:3]) # Limit to first 3 to prevent context overflow
        
        system_prompt = f"""
        You are an expert researcher for a YouTube documentary production.
        Your goal is to analyze the provided transcripts on the topic: "{topic}" 
        and extract the most compelling narrative points, facts, and unique perspectives.
        
        Structure your response as follows:
        1. Executive Summary: High-level overview of the topic based on findings.
        2. Key Points: List of the most important facts/insights.
        3. Potential Narratives: 2-3 different storyboard angles for a new 10-minute video.
        """
        
        user_prompt = f"Topic: {topic}\n\nTranscripts:\n{combined_text}"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.comet_api_url,
                    headers={
                        "Authorization": f"Bearer {self.comet_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "claude-3-5-sonnet-20240620", # Using Claude via CometAPI
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.7
                    }
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "raw_analysis": data['choices'][0]['message']['content'],
                    "model": data.get('model', 'unknown')
                }
        except Exception as e:
            logger.error(f"CometAPI analysis error: {e}")
            # Fallback or error return
            return {"error": str(e)}

    async def generate_creative_brief(self, analysis: str, style_notes: str = "") -> Dict[str, Any]:
        """
        Generate a detailed creative brief including storyboard, narration, and technical direction.
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
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    self.comet_api_url,
                    headers={
                        "Authorization": f"Bearer {self.comet_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "claude-3-5-sonnet-20240620",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.8,
                        "response_format": {"type": "json_object"}
                    }
                )
                response.raise_for_status()
                content = response.json()['choices'][0]['message']['content']
                
                # Handle cases where the model might return a stringified JSON
                import json
                if isinstance(content, str):
                    return json.loads(content)
                return content
                
        except Exception as e:
            logger.error(f"Creative Brief generation error: {e}")
            return {"error": str(e)}


ai_service = AIService()
