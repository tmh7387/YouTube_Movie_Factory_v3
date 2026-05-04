import logging
from typing import Dict, Any, List, Optional
from anthropic import AsyncAnthropic
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System Prompts
# ---------------------------------------------------------------------------

VIDEO_SCENE_DECONSTRUCTOR_PROMPT = """\
You are a professional cinematographer, film director, and AI video production \
specialist. Your job is to analyze a YouTube video using its metadata, transcript, \
and description, then produce a complete technical deconstruction that lets someone \
recreate each scene from scratch using AI generation tools (Kling, Seedance, Veo, etc.).

Because you are working from metadata + transcript (NOT raw frames), infer scene \
structure from narrative beats, topic shifts, described visuals, and temporal cues \
in the transcript. State clearly when you are inferring rather than observing.

## Scene Detection

Split scenes on:
- Narrative topic shifts or segment transitions
- Described location or environment changes
- Timestamps or chapter markers in the transcript
- Tone or energy shifts (e.g., intro → body → conclusion)

For rapid montage-style segments, group as a single "montage sequence."

## Output Format

For EACH scene, provide all eight analysis blocks:

### Scene [N] — [Brief descriptive title]

**Timestamp:** [estimated start] - [estimated end] (duration: ~Xs)

#### 1. Environment & Setting
- Location type (interior/exterior, natural/built, specific setting)
- Time of day and atmospheric conditions (inferred)
- Background elements, props, set dressing
- Color palette and overall visual tone (dominant 3-4 colors)
- Mood and emotional register

#### 2. Subject & Performance
- People/subjects: appearance, clothing, positioning
- Pose, expression, body language (inferred from transcript tone)
- Movement and interaction between subjects

#### 3. Camera & Framing
- Shot type: ECU / CU / MCU / Medium / Medium-wide / Wide / Extreme wide / Establishing
- Camera angle: Eye-level / High / Low / Bird's eye / Dutch tilt / OTS
- Camera movement: Static / Pan / Tilt / Dolly / Truck / Crane / Zoom / Handheld / Steadicam / Tracking / Orbital
- Movement speed: Slow creep / Moderate / Fast whip
- Lens character: Wide-angle / Normal (50mm) / Telephoto
- Depth of field: Shallow (bokeh) / Medium / Deep

#### 4. Lighting
- Source type: Natural / Artificial / Mixed
- Direction: Front / Side / Back / Rim / Rembrandt / Split / Butterfly
- Quality: Hard / Soft / Mixed
- Key-to-fill ratio estimate
- Special: Colored gels, lens flares, volumetric haze, god rays

#### 5. Color Grade & Mood
- Temperature: Warm / Cool / Neutral
- Saturation: Desaturated / Natural / Vibrant / Selective
- Grade style: Teal & orange / Bleach bypass / Vintage / Film emulation / Neon noir / etc.
- Contrast: Low / Medium / High (crushed blacks)
- Split-toning notes

#### 6. Transition
- How scene begins (cut, fade in, dissolve)
- How scene ends (hard cut, fade out, match cut, whip pan)
- Pacing note

#### 7. Audio & Sound Context
- Dialogue, voiceover, or silence
- Music mood and energy
- Sound design notes (ambient, SFX, risers, impacts)
- Audio-visual sync points

#### 8. AI Recreation Prompt

Write a single, dense, ready-to-paste prompt synthesizing the above:

```
[Shot type + angle], [subject with pose/action], [environment], \
[lighting], [camera movement + speed], [color grade + mood], \
[lens/DOF]. [Duration]s.
```

## After All Scenes

Provide a **Style Summary**:
- Overall visual identity and consistent style choices
- Recurring camera techniques or signature moves
- Color grading consistency
- Editing rhythm and pacing pattern
- Recommended presets if recreating as a series

Then provide a **Pre-Production Bible Seed**:
- Characters: name/role, appearance, wardrobe
- Environments: name, description, palette
- Style lock: grade style, contrast, grain, aspect ratio
- Negative prompts: what to avoid

Return the analysis as structured markdown. Be thorough — every scene matters."""

GENERAL_CONTENT_ANALYSIS_PROMPT = """\
You are a creative director for an AI video production pipeline called \
YouTube Movie Factory. Your job is to analyze source material and extract \
everything needed to produce a compelling video.

Structure your response as follows:

## Content Summary
Brief overview of the source material.

## Key Themes & Insights
The most important ideas, facts, or narrative threads.

## Visual Direction
- Suggested visual style, mood, and color palette
- Environment/setting recommendations
- Character or subject archetypes

## Narrative Angles
2-3 distinct approaches for turning this content into a 5-10 minute video, \
each with a different tone or structure.

## Pre-Production Considerations
- Potential challenges or ambiguities
- Recommended reference material to seek
- Music/audio mood suggestions

Return your analysis as structured markdown."""


CHANNEL_DNA_PROMPT = """\
You are a creative strategist for an original AI video production studio.

You have been given transcripts from a YouTube channel's top-performing videos.
Your task is to extract the channel's creative DNA — the storytelling principles,
narrative voice, and structural techniques that make this content resonate — as
transferable inspiration for producing original work on entirely different topics.

Think of this the way a filmmaker studies Kubrick not to imitate his films, but to
understand his principles of spatial tension and deliberate pacing, then applies
those insights to a completely new story.

IMPORTANT: Do not produce a formula for replication. Produce creative principles
that can be repurposed. The output will be used to inspire original production
work, not to reproduce this channel's content.

Return ONLY a valid JSON object with this exact schema (no markdown fences):
{
  "channel_name": "The channel name from the transcripts",
  "videos_analyzed_titles": ["title 1", "title 2"],
  "style_brief": "A 2-3 paragraph creative brief capturing this channel's essence — what makes it work emotionally, what creative tension it creates, what kind of experience it delivers. Written as inspiration for a creative director, not a description of the channel.",
  "narrative_dna": {
    "opening_hook_style": "How do they grab attention in the first 30 seconds? Describe the underlying technique, not the specific content.",
    "storytelling_approach": "How do they structure their narrative arc? What tension or question propels the viewer forward?",
    "pacing_cadence": "Information density and rhythm — how do they control the pace? Dense/punchy, slow-burn, conversational, escalating?",
    "tone_and_voice": "The emotional register and voice — authoritative, intimate, provocative, wondering, urgent? What feeling does it create?",
    "content_format": "How content is organised — list-based, story-driven, essay, narration, revelation-based?",
    "emotional_register": "What emotions do they consistently evoke, and what structural techniques create those emotions?"
  },
  "transferable_principles": [
    "Each entry is an actionable creative principle stated in a way that works for any subject matter. E.g.: 'Open by establishing a gap between what the audience assumes and what is actually true — then spend the video closing that gap'. Include 4-6 principles. Each should stand alone as a directing insight."
  ],
  "what_makes_it_distinctive": "1-2 sentences on the single most distinctive quality of this channel's creative approach — the thing that would be hardest to find elsewhere.",
  "bible_narrative_style": {
    "tone": "Concise tone description suitable for a production bible — 1 sentence",
    "opening_hook": "Concise hook pattern description — 1 sentence",
    "storytelling_approach": "Concise approach description — 1 sentence",
    "pacing": "Concise pacing description — 1 sentence",
    "principles": [
      "Condensed transferable principle 1 — 1-2 sentences suitable for bible injection",
      "Condensed transferable principle 2",
      "Condensed transferable principle 3",
      "Condensed transferable principle 4"
    ]
  }
}

Base your analysis strictly on the transcripts provided. Where transcripts are
unavailable for a video, work from titles and context but note the limitation.
Do not invent characteristics not supported by the content.
"""


class AIService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def analyze_transcripts(
        self, topic: str, transcripts: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze multiple transcripts to extract key insights and a summary.
        Used by the YouTube search pipeline.
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
            response = await self.client.messages.create(
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
            logger.error(
                f"Anthropic analysis error: {type(e).__name__}: {e}",
                exc_info=True,
            )
            return {"error": f"{type(e).__name__}: {e}"}

    async def analyze_single_video(
        self,
        topic: str,
        video_analysis: Optional[Dict] = None,
        text_content: str = "",
    ) -> Dict[str, Any]:
        """
        Deep scene-by-scene deconstruction of a single YouTube video.

        Uses the Video Scene Deconstructor skill as its system prompt.
        Input is transcript + metadata (not raw frames), so the AI infers
        scene structure from narrative cues.
        """
        parts = [f"Topic / creative intent: {topic}", ""]

        if video_analysis:
            parts.append(f"Video Title: {video_analysis.get('title', 'Unknown')}")
            parts.append(f"Video URL: {video_analysis.get('url', '')}")
            parts.append(f"Duration: {video_analysis.get('duration', 'Unknown')}")
            parts.append(f"Views: {video_analysis.get('view_count', 'Unknown')}")
            desc = video_analysis.get("description", "")
            if desc:
                parts.append(f"\n--- VIDEO DESCRIPTION ---\n{desc[:2000]}")
            tags = video_analysis.get("tags", [])
            if tags:
                parts.append(f"\nTags: {', '.join(tags[:20])}")
            parts.append("")

        if text_content:
            parts.append("--- TRANSCRIPT + METADATA ---")
            parts.append(text_content[:12000])

        user_message = "\n".join(parts)

        try:
            response = await self.client.messages.create(
                model=settings.CLAUDE_CREATIVE_MODEL,
                max_tokens=8192,
                system=VIDEO_SCENE_DECONSTRUCTOR_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            logger.info(
                f"Single video analysis complete: "
                f"{len(response.content[0].text)} chars, "
                f"model={response.model}"
            )
            return {
                "raw_analysis": response.content[0].text,
                "model": response.model,
                "analysis_type": "video_scene_deconstruction",
            }
        except Exception as e:
            logger.error(
                f"Single video analysis error: {type(e).__name__}: {e}",
                exc_info=True,
            )
            return {"error": f"{type(e).__name__}: {e}"}

    async def analyze_content(
        self,
        topic: str,
        text_content: str,
        source_type: str,
    ) -> Dict[str, Any]:
        """
        General-purpose creative analysis for non-video source types
        (text brief, web article, image board, audio track, existing bible).
        """
        user_message = (
            f"Source type: {source_type}\n"
            f"Topic / creative intent: {topic}\n\n"
            f"--- SOURCE CONTENT ---\n{text_content[:10000]}"
        )

        try:
            response = await self.client.messages.create(
                model=settings.CLAUDE_FAST_MODEL,
                max_tokens=4000,
                system=GENERAL_CONTENT_ANALYSIS_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            logger.info(
                f"Content analysis complete ({source_type}): "
                f"{len(response.content[0].text)} chars"
            )
            return {
                "raw_analysis": response.content[0].text,
                "model": response.model,
                "analysis_type": "general_content",
            }
        except Exception as e:
            logger.error(
                f"Content analysis error: {type(e).__name__}: {e}",
                exc_info=True,
            )
            return {"error": f"{type(e).__name__}: {e}"}

    async def analyze_channel_dna(
        self,
        topic: str,
        text_content: str,
        video_analysis: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Analyse a channel's top transcripts to extract transferable creative
        principles for inspiring original production work.

        Returns structured Channel DNA JSON stored in research_brief,
        with style_brief text also stored in research_summary.
        """
        channel_name = (
            video_analysis.get('channel_name', 'Unknown')
            if video_analysis else 'Unknown'
        )
        creative_intent = (
            video_analysis.get('creative_intent', topic)
            if video_analysis else topic
        )
        videos_info = (
            video_analysis.get('videos_sampled', [])
            if video_analysis else []
        )

        user_message = (
            f"Channel: {channel_name}\n"
            f"Creative intent for our production: {creative_intent}\n"
            f"Videos sampled: {len(videos_info)}\n\n"
            f"--- TRANSCRIPT CONTENT ---\n"
            f"{text_content[:14000]}"
        )

        try:
            response = await self.client.messages.create(
                model=settings.CLAUDE_CREATIVE_MODEL,
                max_tokens=4096,
                system=CHANNEL_DNA_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )

            raw = response.content[0].text.strip()

            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.rsplit("```", 1)[0].strip()

            import json
            dna = json.loads(raw)

            logger.info(
                f"Channel DNA extracted: {channel_name} | "
                f"{len(dna.get('transferable_principles', []))} principles"
            )

            return {
                "raw_analysis": dna.get("style_brief", ""),
                "research_brief": dna,
                "model": response.model,
                "analysis_type": "channel_dna",
            }

        except Exception as e:
            logger.error(
                f"Channel DNA analysis error: {type(e).__name__}: {e}",
                exc_info=True,
            )
            return {"error": f"{type(e).__name__}: {e}"}


ai_service = AIService()
