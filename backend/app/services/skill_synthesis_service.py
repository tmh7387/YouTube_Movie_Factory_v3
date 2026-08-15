import json
import logging
import re
import textwrap
from pathlib import Path
from typing import Optional
from anthropic import AsyncAnthropic
from app.core.config import settings

logger = logging.getLogger(__name__)

# Root of the on-disk skills repository, sibling to the backend/ directory
SKILLS_ROOT = Path(__file__).parent.parent.parent.parent / "skills"

SKILL_SYNTHESIS_PROMPT = """\
You are a skills librarian for an AI video production system called YouTube Movie Factory.

Your job is to review a tutorial analysis and synthesize 1–3 discrete, reusable, \
tool-agnostic production skills from it. Each skill is a self-contained technique \
that a video production pipeline can apply at scene-generation time.

## Rules

**Tool-agnostic:** The skill body must describe techniques in terms of what to achieve, \
not which specific tool to use. Reference tools only in the `## Tool compatibility` \
section at the end of the skill body.

**Discrete:** Each skill should be one technique, not a summary of the whole video. \
If the tutorial demonstrates 3 genuinely separate techniques, produce 3 skills.

**Reusable:** The prompt_template must use {placeholder} syntax so it can be filled \
in for any production job.

**Description is the trigger:** The description field (SKILL.md frontmatter) is how \
the production pipeline decides whether to apply this skill. Write it to clearly \
cover both WHAT the skill does AND WHEN to use it. Be a little pushy — include \
multiple phrasings and contexts so it triggers reliably.

## Output format

Return a JSON array (no markdown fences) where each item is one skill:

[
  {
    "slug": "kebab-case-skill-name",
    "name": "Human Readable Skill Name",
    "description": "Frontmatter description: what it does and when to use it. \
Should be 2-4 sentences covering multiple trigger contexts.",
    "category": "general",
    "applicable_video_types": ["music_video", "product_brand", "asmr", "general"],
    "tags": ["tag1", "tag2", "tag3"],
    "prompt_template": "The reusable prompt with {placeholders} for variable parts.",
    "example_prompts": ["Verbatim example 1 from the video", "Verbatim example 2"],
    "workflow_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
    "tools_tested_with": ["Tool A v2", "Tool B"],
    "difficulty": "intermediate",
    "confidence_score": 0.9,
    "skill_body_markdown": "Full SKILL.md body — see format below"
  }
]

## skill_body_markdown format

Write the body in this structure (use real markdown, keep under 300 lines):

# {Skill Name}

{One sentence — what this technique achieves and why it matters.}

## When to use
- Bullet 1
- Bullet 2

## Core technique
{Explain the technique in tool-agnostic terms. WHY it works, not just what to do.}

## Prompt template
```
{prompt_template with {placeholders}}
```

## Example
```
{one or two verbatim example prompts from the source video}
```

## Workflow
1. Step one
2. Step two
3. Step three

## Pro tip
{The single most non-obvious insight — the thing that makes this skill valuable.}

## Tool compatibility
Works with any {img2video / image generation / audio} model.
Verified with: {list of tools from source video}
"""


class SkillSynthesisService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def synthesize_skills(
        self,
        knowledge_entry_id: str,
        gemini_analysis: dict,
        source_video_url: str,
    ) -> list[dict]:
        """
        Takes raw Gemini extraction from a tutorial and uses Claude Sonnet to
        synthesize 1-3 tool-agnostic SKILL.md-formatted skills.
        Returns a list of skill dicts ready to be saved to the DB and disk.
        """
        # Build a focused summary for the synthesis prompt
        analysis_summary = self._format_analysis_for_synthesis(gemini_analysis)

        user_message = f"""Here is the tutorial analysis to synthesize into skills:

SOURCE VIDEO: {source_video_url}
TITLE: {gemini_analysis.get('title_detected', 'Unknown')}
CREATOR: {gemini_analysis.get('creator_name', 'Unknown')}
CATEGORY: {gemini_analysis.get('category', 'general')}
DIFFICULTY: {gemini_analysis.get('difficulty_level', 'intermediate')}

TOOLS MENTIONED: {', '.join(gemini_analysis.get('tool_names', []))}

STANDOUT TIP: {gemini_analysis.get('standout_tip', '')}

WORKFLOW STEPS:
{chr(10).join(gemini_analysis.get('workflow_sequence', []))}

EXACT PROMPTS SHOWN IN VIDEO:
{chr(10).join(f'  • {p}' for p in gemini_analysis.get('exact_prompts_shown', []))}

KEY SETTINGS: {json.dumps(gemini_analysis.get('key_settings', {}), indent=2)}

CATEGORY-SPECIFIC TECHNIQUES:
{json.dumps(gemini_analysis.get('category_specific', {}), indent=2)}

FULL TECHNIQUE SUMMARY:
{gemini_analysis.get('full_technique_summary', '')}

Now synthesize 1–3 discrete, reusable, tool-agnostic skills from this analysis. \
Return ONLY the JSON array, no other text."""

        try:
            response = await self.client.messages.create(
                model=settings.CLAUDE_FAST_MODEL,
                max_tokens=8192,
                system=SKILL_SYNTHESIS_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )

            raw = response.content[0].text.strip()
            # Only strip fences when the whole response is wrapped in them
            if raw.startswith("```"):
                m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
                if m:
                    raw = m.group(1).strip()

            skills_raw = json.loads(raw)
            logger.info(
                f"Synthesized {len(skills_raw)} skill(s) from {source_video_url}"
            )

            # Enrich each skill with provenance before returning
            skills = []
            for s in skills_raw:
                s["source_video_url"] = source_video_url
                s["source_knowledge_entry_id"] = knowledge_entry_id
                skills.append(s)

            return skills

        except json.JSONDecodeError as e:
            logger.error(f"Skill synthesis JSON parse error: {e}\nRaw: {raw[:500]}")
            return []
        except Exception as e:
            logger.error(f"Skill synthesis failed: {e}", exc_info=True)
            return []

    def write_skill_to_disk(self, skill: dict) -> str:
        """
        Writes a skill to the on-disk skills repository as a SKILL.md file.
        Path: skills/{category}/{slug}/SKILL.md
        Returns the relative file path.
        """
        category = skill.get("category", "general")
        slug = skill["slug"]
        skill_dir = SKILLS_ROOT / category / slug
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Build the full SKILL.md content with frontmatter
        frontmatter = textwrap.dedent(f"""\
            ---
            name: {slug}
            description: {skill['description']}
            ---
            """)

        skill_md_path = skill_dir / "SKILL.md"
        skill_md_path.write_text(
            frontmatter + "\n" + skill.get("skill_body_markdown", ""),
            encoding="utf-8",
        )

        rel_path = str(skill_md_path.relative_to(SKILLS_ROOT.parent))
        logger.info(f"Wrote skill to disk: {rel_path}")
        return rel_path

    def _format_analysis_for_synthesis(self, analysis: dict) -> str:
        """Compact representation of the Gemini analysis for the synthesis prompt."""
        return json.dumps(
            {k: v for k, v in analysis.items() if k != "gemini_analysis"},
            indent=2,
        )[:6000]


skill_synthesis_service = SkillSynthesisService()
