"""
SkillLoaderService — Bridge between on-disk production skills and runtime Claude calls.

Reads .agent/skills/{slug}/SKILL.md files (hand-crafted) and VideoProductionSkill DB rows
(tutorial-extracted), then builds compact prompt injection blocks for Claude's system prompt.

Disk skills take priority over DB skills when the same slug exists in both.
"""
import logging
import re
from pathlib import Path
from typing import Optional

from sqlalchemy import select, desc

from app.db.session import AsyncSessionLocal
from app.models import VideoProductionSkill

logger = logging.getLogger(__name__)

# .agent/skills/ directory — sibling to backend/
AGENT_SKILLS_ROOT = Path(__file__).parent.parent.parent.parent / ".agent" / "skills"

# Auto-selection rules: model keyword → skill slugs to inject
MODEL_SKILL_MAP: dict[str, list[str]] = {
    "seedance": [
        "seedance2-director",
        "multi-shot-camera-coverage",
    ],
    "kling": [
        "music-video-producer",
        "multi-shot-camera-coverage",
    ],
    "higgsfield": [
        "higgsfield-creator",
    ],
}

# Skills to always consider for specific contexts
CONTEXT_SKILL_MAP: dict[str, list[str]] = {
    "lip_sync": ["audio-driven-lip-sync-video"],
    "dialogue": ["audio-driven-lip-sync-video"],
    "beat_sync": ["audio-driven-lip-sync-video"],
    "music_video": ["music-video-producer"],
    "storyboard": [
        "multi-shot-storyboard-extraction",
        "multi-shot-camera-coverage",
    ],
    "character_consistency": [
        "style-reference-character-transplant",
        "multi-shot-camera-coverage",
    ],
    "project_bible": ["project-bible"],
    "bible": ["project-bible"],
    "ripple_edit": ["ripple-edit"],
    "global_change": ["ripple-edit"],
}


class SkillLoaderService:
    """Loads production skills from disk and DB, builds Claude prompt injection blocks."""

    # ─── Disk skill loading ──────────────────────────────────────────────

    @staticmethod
    def _parse_skill_md(path: Path) -> Optional[dict]:
        """Parse a SKILL.md file into a dict with frontmatter fields + body."""
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read {path}: {e}")
            return None

        # Split YAML frontmatter from body
        frontmatter: dict[str, str] = {}
        body = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                fm_text = parts[1].strip()
                body = parts[2].strip()
                # Parse YAML frontmatter with multiline >- support
                current_key: Optional[str] = None
                for line in fm_text.splitlines():
                    # New key: line starts with non-space and contains colon
                    if not line.startswith(" ") and ":" in line:
                        key, val = line.split(":", 1)
                        current_key = key.strip()
                        val_stripped = val.strip()
                        # YAML multiline: >- means join continuation lines with spaces
                        if val_stripped in (">-", ">", "|-", "|"):
                            frontmatter[current_key] = ""
                        else:
                            frontmatter[current_key] = val_stripped
                            current_key = None
                    elif current_key and line.startswith("  "):
                        # Continuation line for multiline value
                        existing = frontmatter.get(current_key, "")
                        sep = " " if existing else ""
                        frontmatter[current_key] = existing + sep + line.strip()

        return {
            "slug": frontmatter.get("name", path.parent.name),
            "name": frontmatter.get("name", path.parent.name),
            "description": frontmatter.get("description", ""),
            "priority": frontmatter.get("priority", "MEDIUM"),
            "body": body,
            "source": "disk",
        }

    def load_disk_skill(self, slug: str) -> Optional[dict]:
        """Load a single skill from .agent/skills/{slug}/SKILL.md."""
        skill_path = AGENT_SKILLS_ROOT / slug / "SKILL.md"
        return self._parse_skill_md(skill_path)

    def load_disk_skills(self, slugs: list[str]) -> list[dict]:
        """Load multiple skills from disk, skipping any that don't exist."""
        results = []
        for slug in slugs:
            skill = self.load_disk_skill(slug)
            if skill:
                results.append(skill)
            else:
                logger.debug(f"Disk skill not found: {slug}")
        return results

    # ─── DB skill loading ────────────────────────────────────────────────

    async def load_db_skills(
        self,
        video_type: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict]:
        """Load top skills from the VideoProductionSkill DB table."""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(VideoProductionSkill).order_by(
                    desc(VideoProductionSkill.confidence_score)
                )
                if video_type:
                    stmt = stmt.where(
                        VideoProductionSkill.applicable_video_types.contains([video_type])
                    )
                stmt = stmt.limit(limit)
                result = await session.execute(stmt)
                rows = result.scalars().all()

            return [
                {
                    "slug": r.slug,
                    "name": r.name,
                    "description": r.description or "",
                    "prompt_template": r.prompt_template or "",
                    "workflow_steps": r.workflow_steps or [],
                    "pro_tip": self._extract_section(r.skill_body, "Pro tip"),
                    "source": "db",
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning(f"DB skill loading failed (non-fatal): {e}")
            return []

    # ─── Skill selection logic ───────────────────────────────────────────

    def select_skill_slugs(
        self,
        animation_model: str = "",
        contexts: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Auto-select relevant skill slugs based on the animation model
        and any additional context keywords.
        """
        slugs: list[str] = []
        model_lower = animation_model.lower() if animation_model else ""

        for keyword, skill_slugs in MODEL_SKILL_MAP.items():
            if keyword in model_lower:
                slugs.extend(skill_slugs)

        for ctx in (contexts or []):
            ctx_lower = ctx.lower().replace(" ", "_")
            if ctx_lower in CONTEXT_SKILL_MAP:
                slugs.extend(CONTEXT_SKILL_MAP[ctx_lower])

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for s in slugs:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        return unique

    # ─── Prompt block builders ───────────────────────────────────────────

    def build_compact_block(self, skills: list[dict]) -> str:
        """
        Build a compact prompt injection block from loaded skills.
        Extracts only the most useful sections to stay under ~2K tokens:
        - Camera controls / native syntax tables
        - Prompt templates + examples
        - Pro tips
        - Creative principles
        """
        if not skills:
            return ""

        lines = [
            "## Production Skills — Apply these techniques where relevant\n"
        ]

        for skill in skills:
            lines.append(f"### {skill.get('name', skill.get('slug', 'Unknown'))}")

            if skill.get("description"):
                lines.append(skill["description"])
                lines.append("")

            body = skill.get("body", "")
            if body:
                # Extract the most valuable sections from the full body
                for section_name in [
                    # Seedance v2.0
                    "SEEDANCE NATIVE CAMERA CONTROLS",
                    "SMART CUTS & CUT DISCIPLINE",
                    "THE HOOK RULE",
                    "CREATIVE PRINCIPLES",
                    "DURATION CALIBRATION",
                    "Speed precision guide",
                    # Higgsfield
                    "Core Camera System",
                    "Movement × Narrative Beat Pairing",
                    "Integrated Color Grading",
                    # Music Video Producer
                    "IMAGE-TO-VIDEO PROMPTS",
                    "PRODUCTION PRINCIPLES",
                    # Project Bible
                    "Schema",
                    "INJECT Bible into Clip Prompts",
                    # Ripple Edit
                    "Workflows",
                    "Diff Summary Format",
                    "Safety Rules",
                    # Common
                    "Prompt template",
                    "Example",
                    "Pro tip",
                    "Core technique",
                ]:
                    section = self._extract_section(body, section_name)
                    if section:
                        lines.append(f"#### {section_name}")
                        lines.append(section.strip())
                        lines.append("")
            else:
                # DB skill — use structured fields
                if skill.get("prompt_template"):
                    lines.append("#### Prompt template")
                    lines.append(f"```\n{skill['prompt_template']}\n```")
                    lines.append("")
                if skill.get("pro_tip"):
                    lines.append(f"#### Pro tip")
                    lines.append(skill["pro_tip"])
                    lines.append("")

            lines.append("---\n")

        return "\n".join(lines)

    def build_motion_prompt_default(self, animation_model: str = "") -> str:
        """
        Build a Seedance-aware default motion prompt to replace
        the hardcoded 'cinematic camera movement, smooth motion'.
        """
        model_lower = animation_model.lower() if animation_model else ""

        if "seedance" in model_lower:
            return (
                "slow dolly in, cinematic lighting with warm 3200K tones, "
                "subtle depth of field shift from background to subject, "
                "smooth motion, atmospheric haze"
            )
        # Kling or generic
        return "cinematic camera movement, smooth dolly, natural motion"

    # ─── Combined loader ─────────────────────────────────────────────────

    async def build_prompt_block(
        self,
        animation_model: str = "",
        video_type: Optional[str] = None,
        contexts: Optional[list[str]] = None,
        include_db_skills: bool = True,
    ) -> str:
        """
        Main entry point: auto-select and load skills from both disk and DB,
        then produce a single prompt injection block for Claude.

        Disk skills take priority — if a slug exists on disk AND in DB, only
        the disk version is included.
        """
        # 1. Auto-select disk skill slugs
        slugs = self.select_skill_slugs(animation_model, contexts)
        disk_skills = self.load_disk_skills(slugs)
        disk_slugs = {s["slug"] for s in disk_skills}

        # 2. Load DB skills (filtered to avoid duplicates)
        db_skills = []
        if include_db_skills:
            all_db = await self.load_db_skills(video_type=video_type, limit=5)
            db_skills = [s for s in all_db if s["slug"] not in disk_slugs]

        # 3. Merge: disk first (priority), then DB
        all_skills = disk_skills + db_skills

        if all_skills:
            logger.info(
                f"Loaded {len(all_skills)} skill(s) for injection: "
                f"{[s['slug'] for s in all_skills]} "
                f"(model={animation_model})"
            )

        return self.build_compact_block(all_skills)

    # ─── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _extract_section(body: Optional[str], heading: str) -> Optional[str]:
        """Extract content under a markdown heading (##, ###, or ####)."""
        if not body:
            return None
        # Match ## through #### headings with the given name
        pattern = rf"(?:^|\n)(##{{1,3}})\s+{re.escape(heading)}\s*(?:—[^\n]*)?\n+(.*?)(?=\n##{{1,3}}\s|\Z)"
        m = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
        return m.group(2).strip() if m else None


skill_loader_service = SkillLoaderService()
