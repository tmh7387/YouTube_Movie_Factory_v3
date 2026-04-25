import httpx
import json
import logging
import re
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Category-specific extraction schemas define what Gemini looks for in each video type
CATEGORY_SCHEMAS = {
    "music_video": {
        "label": "AI-generated music video",
        "focus_areas": [
            "beat_sync_and_timing: How visuals are synchronized to music beats",
            "visual_style_prompts: Specific prompt structures that produce the visual aesthetic",
            "color_grading_and_mood: Color palette choices, LUT mentions, mood-to-color mappings",
            "transition_techniques: Cut types, morph transitions, beat-aligned cuts",
            "lyric_treatment: How lyrics or text are integrated visually",
            "energy_pacing: How energy levels map to visual intensity across the video",
        ],
    },
    "product_brand": {
        "label": "product or brand video",
        "focus_areas": [
            "product_prompt_structure: How prompts describe the product itself cleanly",
            "lighting_and_background: Studio lighting setups, background style for brand consistency",
            "brand_color_adherence: Techniques for keeping brand colors accurate across frames",
            "lifestyle_context: How product is placed in lifestyle/environment shots",
            "consistency_across_shots: Methods for maintaining visual consistency between scenes",
            "text_and_logo_treatment: Overlay styles, font choices, CTA placement",
        ],
    },
    "asmr": {
        "label": "ASMR video",
        "focus_areas": [
            "texture_prompts: Specific language describing surfaces, materials, tactile qualities",
            "macro_and_detail_framing: How extreme close-ups and detail shots are prompted",
            "motion_and_speed: Slow-motion settings, smooth motion parameters",
            "sound_visual_sync: How audio triggers map to visual actions",
            "satisfying_loop_structure: How seamless loops and satisfying repetition are achieved",
            "sensory_language: Descriptive sensory vocabulary that generates ASMR-quality imagery",
        ],
    },
    "general": {
        "label": "AI video generation",
        "focus_areas": [
            "core_techniques: Primary methods or approaches demonstrated",
            "prompt_architecture: How prompts are structured and layered",
            "tool_chain: Sequence of tools used in the workflow",
            "model_specific_tips: Settings or tricks specific to the AI models used",
            "quality_improvement: Tips that specifically improve output quality",
        ],
    },
}


class GeminiVideoAnalyzerService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL

    def _build_analysis_prompt(self, youtube_url: str, category: str, extra_context: str = "") -> str:
        schema = CATEGORY_SCHEMAS.get(category, CATEGORY_SCHEMAS["general"])
        focus_lines = "\n".join(f"  - {f}" for f in schema["focus_areas"])

        return f"""You are an expert analyst of AI video production tutorials, specializing in {schema['label']}s.

Watch this tutorial carefully and extract structured, actionable knowledge for an automated AI video production system.

VIDEO URL: {youtube_url}
CATEGORY: {category}
{f'ADDITIONAL CONTEXT: {extra_context}' if extra_context else ''}

Extract the following. Be specific and verbatim where possible:

CATEGORY-SPECIFIC FOCUS AREAS:
{focus_lines}

UNIVERSAL EXTRACTIONS:
  - exact_prompts_shown: Copy any text prompts shown on screen VERBATIM, word for word
  - tool_names: Every AI tool, model, platform, or service mentioned (e.g., Kling 2.1, Runway Gen-4, Suno v4, MidJourney)
  - workflow_sequence: The step-by-step order of operations actually demonstrated
  - key_settings: Specific model parameters, CFG scale, motion intensity, seed values, or config options shown
  - resource_mentions: Any URLs, Notion pages, Discord links, download links, Patreon, Google Docs mentioned verbally or on screen
  - standout_tip: The single most valuable, non-obvious insight in this video (1-2 sentences)
  - difficulty_level: beginner / intermediate / advanced
  - estimated_workflow_time: Rough time to replicate this workflow

Respond ONLY with valid JSON — no markdown fences, no commentary outside the JSON:
{{
  "video_url": "{youtube_url}",
  "category": "{category}",
  "title_detected": "video title as shown or spoken",
  "creator_name": "channel or creator name",
  "difficulty_level": "beginner|intermediate|advanced",
  "estimated_workflow_time": "e.g. 30 minutes",
  "standout_tip": "the single most valuable insight",
  "exact_prompts_shown": ["verbatim prompt 1", "verbatim prompt 2"],
  "tool_names": ["Tool A v2.1", "Tool B"],
  "workflow_sequence": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
  "key_settings": {{"setting_name": "value", "another_setting": "value"}},
  "resource_mentions": ["https://...", "discord.gg/..."],
  "category_specific": {{
    "field_name": "extracted value or array"
  }},
  "full_technique_summary": "2-3 paragraph narrative summarising all techniques, suitable for training a production system"
}}"""

    async def analyze_youtube_video(
        self,
        youtube_url: str,
        category: str = "general",
        extra_context: str = "",
    ) -> dict:
        """
        Submit a YouTube URL directly to Gemini for native video understanding.
        Returns structured extraction of techniques, prompts, and workflow tips.
        """
        prompt = self._build_analysis_prompt(youtube_url, category, extra_context)

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "fileData": {
                                "fileUri": youtube_url,
                                "mimeType": "video/mp4",
                            }
                        },
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 8192,
                "temperature": 0.2,
            },
        }

        endpoint = f"{GEMINI_API_BASE}/{self.model}:generateContent"
        params = {"key": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(endpoint, params=params, json=payload)

            if resp.status_code != 200:
                error_body = resp.json() if resp.content else {}
                logger.error(f"Gemini API error {resp.status_code}: {error_body}")
                return {
                    "video_url": youtube_url,
                    "category": category,
                    "error": f"HTTP {resp.status_code}: {error_body.get('error', {}).get('message', 'Unknown error')}",
                }

            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

            # Strip markdown fences if Gemini wraps output
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_text)
            if json_match:
                raw_text = json_match.group(1).strip()

            result = json.loads(raw_text)
            logger.info(f"Gemini analysis complete for {youtube_url} — standout tip: {result.get('standout_tip', '')[:80]}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned non-JSON response: {e}")
            return {
                "video_url": youtube_url,
                "category": category,
                "error": "json_parse_error",
                "raw_response": raw_text[:3000] if "raw_text" in dir() else "no response",
            }
        except Exception as e:
            logger.error(f"Gemini video analysis failed: {e}", exc_info=True)
            return {"video_url": youtube_url, "category": category, "error": str(e)}

    async def extract_notion_page_content(self, notion_url: str) -> dict:
        """
        Fetch a public Notion page and use Gemini to extract structured prompt
        libraries and techniques from it (e.g. the Higgs AI brand prompts page).
        """
        # Fetch the raw page HTML
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                page_resp = await client.get(
                    notion_url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; VideoFactoryBot/1.0)"},
                    follow_redirects=True,
                )
            if page_resp.status_code != 200:
                return {"url": notion_url, "error": f"Fetch failed: HTTP {page_resp.status_code}"}

            # Strip HTML tags for a cleaner text feed to Gemini
            raw_html = page_resp.text
            clean_text = re.sub(r"<[^>]+>", " ", raw_html)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()[:40000]

        except Exception as e:
            return {"url": notion_url, "error": f"Fetch error: {e}"}

        prompt = f"""You are analysing a Notion page that contains AI video generation resources and prompts.

Extract ALL of the following from the page content below:
1. prompt_library: Every AI prompt listed, exactly as written (verbatim)
2. tool_references: Any AI tools, models, or platforms mentioned
3. workflow_guides: Any step-by-step workflows or instructions
4. tips_and_tricks: Standalone tips, best practices, or notes
5. page_title: The main title or heading of the page
6. page_summary: 1-2 sentence description of what this resource is

Respond ONLY with valid JSON:
{{
  "url": "{notion_url}",
  "page_title": "...",
  "page_summary": "...",
  "prompt_library": ["verbatim prompt 1", "verbatim prompt 2"],
  "tool_references": ["tool name", "model name"],
  "workflow_guides": ["step-by-step guide as found"],
  "tips_and_tricks": ["tip 1", "tip 2"]
}}

PAGE CONTENT:
{clean_text}"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.1},
        }

        endpoint = f"{GEMINI_API_BASE}/{self.model}:generateContent"
        params = {"key": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(endpoint, params=params, json=payload)

            if resp.status_code != 200:
                error_body = resp.json() if resp.content else {}
                return {"url": notion_url, "error": f"Gemini HTTP {resp.status_code}: {error_body.get('error', {}).get('message', '')}"}

            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_text)
            if json_match:
                raw_text = json_match.group(1).strip()

            return json.loads(raw_text)

        except Exception as e:
            logger.error(f"Notion extraction failed for {notion_url}: {e}", exc_info=True)
            return {"url": notion_url, "error": str(e)}


gemini_service = GeminiVideoAnalyzerService()
