import logging
from typing import List, Dict, Any
from anthropic import AsyncAnthropic
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY

    async def analyze_transcripts(self, topic: str, transcripts: List[str]) -> Dict[str, Any]:
        """
        Analyze multiple transcripts to extract key insights and a summary.
        Uses Anthropic SDK directly for reliability.
        """
        combined_text = "\n\n---\n\n".join(transcripts[:3])

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
            client = AsyncAnthropic(api_key=self.anthropic_api_key)
            response = await client.messages.create(
                model=settings.CLAUDE_FAST_MODEL,
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return {
                "raw_analysis": response.content[0].text,
                "model": response.model,
            }
        except Exception as e:
            logger.error(f"Anthropic analysis error: {type(e).__name__}: {e}", exc_info=True)
            return {"error": f"{type(e).__name__}: {e}"}


ai_service = AIService()
