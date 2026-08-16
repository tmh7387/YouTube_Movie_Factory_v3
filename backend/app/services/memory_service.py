"""
MemoryService — close the loop between what a job produced and what the next brief knows.

Three jobs:

  build_memory_block()      read LESSONS.md / PATTERNS.md / PREFERENCE_PROFILE.md and
                            produce a capped injection block for the brief prompt.
  update_skill_confidence() move VideoProductionSkill.confidence_score off Claude's
                            one-shot guess and onto observed generation_outcome rows.
  write_project_log()       append a per-job summary to PROJECT_LOG/, and distil a rule
                            into LESSONS.md when the same failure repeats.

The five memory files under .agent/music-video-director/memory/ were read by no code
before this. They are append-and-distil, never overwrite: write_project_log() reads
what is already there and inserts, and running it twice for one job changes nothing
the second time.
"""
import json
import logging
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import (
    CurationJob,
    GenerationOutcome,
    ProductionJob,
    ProductionScene,
    VideoProductionSkill,
)

logger = logging.getLogger(__name__)

MEMORY_ROOT = (
    Path(__file__).parent.parent.parent.parent
    / ".agent" / "music-video-director" / "memory"
)
PROJECT_LOG_DIR = MEMORY_ROOT / "PROJECT_LOG"

# Files injected into the brief prompt, in the order they are read.
BRIEF_MEMORY_FILES = ("PATTERNS.md", "PREFERENCE_PROFILE.md", "LESSONS.md")

# ~2,000 tokens. Counted in characters because that is what we can measure here
# without a tokenizer; 4 chars/token is the usual English approximation.
MEMORY_CHAR_BUDGET = 8_000

# Weight given to Claude's initial confidence_score, in units of observed scenes. Three
# means a single bad scene cannot halve a skill's score, but a dozen will move it.
CONFIDENCE_PRIOR_WEIGHT = 3.0

# A failure category has to recur this many times in one job before it becomes a lesson.
LESSON_REPEAT_THRESHOLD = 3


def _slugify(text: str, max_length: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug[:max_length].strip("-") or "untitled"


class MemoryService:

    # -- reading memory into a brief ---------------------------------------

    @staticmethod
    def _read(name: str) -> str:
        path = MEMORY_ROOT / name
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
        except Exception as e:
            logger.warning(f"Memory read failed for {name}: {e}")
            return ""

    @staticmethod
    def _newest_first_sections(markdown: str, budget: int) -> str:
        """
        Trim a memory file to `budget` characters at section boundaries.

        LESSONS.md is maintained newest-at-top, so taking whole `## ` sections from the
        front keeps the most recent lessons and drops the oldest — never a half sentence.
        """
        if len(markdown) <= budget:
            return markdown

        parts = re.split(r"(?m)^(?=## )", markdown)
        kept: List[str] = []
        used = 0
        for part in parts:
            if used + len(part) > budget:
                break
            kept.append(part)
            used += len(part)
        if not kept:
            return markdown[:budget].rsplit("\n", 1)[0]
        return "".join(kept).rstrip()

    def build_memory_block(self, char_budget: int = MEMORY_CHAR_BUDGET) -> str:
        """
        Assemble the director-memory block for injection into a brief system prompt.

        Returns "" when there is nothing to say, so callers can concatenate blindly.
        """
        sections: List[str] = []
        remaining = char_budget

        for name in BRIEF_MEMORY_FILES:
            if remaining <= 0:
                break
            body = self._read(name).strip()
            if not body:
                continue
            body = self._newest_first_sections(body, remaining)
            remaining -= len(body)
            sections.append(body)

        if not sections:
            return ""

        return (
            "## Director Memory — what previous productions taught us\n\n"
            "These are accumulated lessons, recurring patterns and this director's\n"
            "standing preferences. Apply them unless the brief explicitly overrides one.\n\n"
            + "\n\n---\n\n".join(sections)
            + "\n"
        )

    # -- skill confidence ---------------------------------------------------

    @staticmethod
    def score_outcomes(outcomes: Iterable[Any], prior: Optional[float]) -> Optional[float]:
        """
        Rolling mean of qa_pass, weighted by the human verdict where one exists.

        A scene a human reviewed counts double and averages the machine and human
        verdicts; a scene nobody reviewed contributes its QA result alone. Claude's
        original confidence_score enters as a prior worth CONFIDENCE_PRIOR_WEIGHT
        scenes, so one bad run nudges the score rather than replacing it.

        Returns None when there is nothing observed and no prior.
        """
        total_weight = 0.0
        total_value = 0.0

        for outcome in outcomes:
            if outcome.qa_pass is None and outcome.user_approved is None:
                continue
            machine = 1.0 if outcome.qa_pass else 0.0
            if outcome.user_approved is None:
                weight, value = 1.0, machine
            else:
                human = 1.0 if outcome.user_approved else 0.0
                weight, value = 2.0, (machine + human) / 2.0
            total_weight += weight
            total_value += weight * value

        if prior is not None:
            total_weight += CONFIDENCE_PRIOR_WEIGHT
            total_value += CONFIDENCE_PRIOR_WEIGHT * float(prior)

        if total_weight == 0:
            return None
        return round(total_value / total_weight, 4)

    async def update_skill_confidence(self, slugs: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Recompute confidence_score for the named skills (or every skill) from the
        generation_outcome rows of jobs that used them. Returns {slug: new_score}.
        """
        updated: Dict[str, float] = {}
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(VideoProductionSkill)
                if slugs:
                    stmt = stmt.where(VideoProductionSkill.slug.in_(slugs))
                skills = (await session.execute(stmt)).scalars().all()

                for skill in skills:
                    rows = (await session.execute(
                        select(GenerationOutcome).where(
                            GenerationOutcome.skill_slugs.contains([skill.slug])
                        )
                    )).scalars().all()
                    if not rows:
                        continue

                    prior = float(skill.confidence_score) if skill.confidence_score is not None else None
                    score = self.score_outcomes(rows, prior)
                    if score is None:
                        continue
                    skill.confidence_score = score
                    updated[skill.slug] = score

                if updated:
                    await session.commit()
        except Exception as e:
            logger.warning(f"Skill confidence update failed (non-fatal): {e}")

        if updated:
            logger.info(f"Skill confidence updated: {updated}")
        return updated

    async def increment_usage(self, slugs: List[str]) -> None:
        """
        Count a skill as used because the pipeline used it — not because a human opened
        its detail page, which was the only thing that moved usage_count before.
        """
        if not slugs:
            return
        try:
            async with AsyncSessionLocal() as session:
                rows = (await session.execute(
                    select(VideoProductionSkill).where(VideoProductionSkill.slug.in_(slugs))
                )).scalars().all()
                for skill in rows:
                    skill.usage_count = (skill.usage_count or 0) + 1
                if rows:
                    await session.commit()
        except Exception as e:
            logger.warning(f"Skill usage increment failed (non-fatal): {e}")

    # -- project log --------------------------------------------------------

    @staticmethod
    def _failure_categories(scenes: Iterable[Any]) -> Counter:
        """Count artifact phrases across every scene that failed QA."""
        counter: Counter = Counter()
        for scene in scenes:
            if scene.qa_status != "fail" or not scene.qa_notes:
                continue
            try:
                verdict = json.loads(scene.qa_notes)
            except (TypeError, ValueError):
                continue
            for artifact in verdict.get("artifacts") or []:
                category = re.sub(r"\s+", " ", str(artifact)).strip().lower()
                if category:
                    counter[category] += 1
        return counter

    def log_path_for(self, job_id: str, title: str, created_at: Optional[datetime]) -> Path:
        """
        Deterministic filename, so re-running produces one log file rather than two.
        The job id suffix keeps two same-day projects with the same title apart.
        """
        stamp = (created_at or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
        return PROJECT_LOG_DIR / f"{stamp}-{_slugify(title)}-{str(job_id)[:8]}.md"

    @staticmethod
    def render_project_log(context: Dict[str, Any]) -> str:
        scenes = context["scenes"]
        failures = context["failure_categories"]
        lines = [
            f"# {context['title']}",
            "",
            f"<!-- job:{context['job_id']} -->",
            f"- Job: `{context['job_id']}`",
            f"- Completed: {context['completed_at']}",
            f"- Status: {context['status']}",
            f"- Scenes: {len(scenes)}",
            f"- QA: {context['qa_pass']} pass / {context['qa_fail']} fail / {context['qa_skipped']} skipped",
            f"- Human review: {context['approved']} approved / {context['rejected']} rejected / "
            f"{context['unreviewed']} unreviewed",
            f"- Reference-anchored scenes: {context['reference_scenes']} of {len(scenes)}",
            f"- Beat-aligned scenes: {context['beat_scenes']} of {len(scenes)}",
        ]
        if context.get("tempo_bpm"):
            lines.append(f"- Tempo: {context['tempo_bpm']:.1f} BPM")

        lines += ["", "## Failure categories", ""]
        if failures:
            lines += [f"- {category} — {count} scene(s)" for category, count in failures.most_common()]
        else:
            lines.append("- None recorded.")

        feedback = [(s.scene_number, s.user_feedback) for s in scenes if s.user_feedback]
        if feedback:
            lines += ["", "## Human feedback", ""]
            lines += [f"- Scene {number}: {text}" for number, text in feedback]

        return "\n".join(lines) + "\n"

    def append_lessons(self, entries: List[str], job_id: str, title: str) -> bool:
        """
        Insert a distilled lesson above the newest existing entry.

        LESSONS.md is maintained newest-at-top, so the new section goes immediately
        before the first `## ` heading — the preamble is preserved and nothing is
        overwritten. The job marker makes a second run a no-op.
        """
        if not entries:
            return False

        path = MEMORY_ROOT / "LESSONS.md"
        existing = self._read("LESSONS.md")
        marker = f"<!-- job:{job_id} -->"
        if marker in existing:
            return False

        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        block = "\n".join(
            [f"## {stamp} — {title}", "", marker, ""]
            + [f"- {entry}" for entry in entries]
            + [""]
        )

        match = re.search(r"(?m)^## ", existing)
        if match:
            updated = existing[: match.start()] + block + "\n" + existing[match.start():]
        else:
            updated = (existing.rstrip() + "\n\n" if existing.strip() else "") + block

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(updated, encoding="utf-8")
            return True
        except Exception as e:
            logger.warning(f"LESSONS.md append failed: {e}")
            return False

    async def write_project_log(self, job_id: str) -> Optional[Path]:
        """
        Write the per-job markdown summary and distil repeated failures into LESSONS.md.

        Idempotent: the filename is derived from the job, so a second call rewrites the
        same file, and the lesson entry is skipped when its job marker is already present.
        """
        try:
            async with AsyncSessionLocal() as session:
                job = (await session.execute(
                    select(ProductionJob).where(ProductionJob.id == job_id)
                )).scalar_one_or_none()
                if not job:
                    return None

                curation = (await session.execute(
                    select(CurationJob).where(CurationJob.id == job.curation_job_id)
                )).scalar_one_or_none()

                scenes = (await session.execute(
                    select(ProductionScene)
                    .where(ProductionScene.job_id == job_id)
                    .order_by(ProductionScene.scene_number)
                )).scalars().all()
        except Exception as e:
            logger.warning(f"Project log skipped — could not load job {job_id}: {e}")
            return None

        brief = {}
        if curation:
            brief = curation.user_approved_brief or curation.creative_brief or {}
        title = brief.get("title") or f"Production {str(job_id)[:8]}"

        failures = self._failure_categories(scenes)
        context = {
            "job_id": str(job_id),
            "title": title,
            "status": job.status,
            "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "scenes": scenes,
            "qa_pass": sum(1 for s in scenes if s.qa_status == "pass"),
            "qa_fail": sum(1 for s in scenes if s.qa_status == "fail"),
            "qa_skipped": sum(1 for s in scenes if s.qa_status == "skipped"),
            "approved": sum(1 for s in scenes if s.user_approved is True),
            "rejected": sum(1 for s in scenes if s.user_approved is False),
            "unreviewed": sum(1 for s in scenes if s.user_approved is None),
            "reference_scenes": sum(
                1 for s in scenes if (s.reference_inputs or {}).get("mode") == "reference"
            ),
            "beat_scenes": sum(1 for s in scenes if s.beat_start_sec is not None),
            "tempo_bpm": float(job.tempo_bpm) if job.tempo_bpm is not None else None,
            "failure_categories": failures,
        }

        path = self.log_path_for(job_id, title, job.created_at)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.render_project_log(context), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Project log write failed for {job_id}: {e}")
            return None

        repeated = [
            f"{category} recurred on {count} scenes in '{title}' — "
            f"tighten the negative prompt or the reference anchor for this pattern."
            for category, count in failures.items()
            if count >= LESSON_REPEAT_THRESHOLD
        ]
        self.append_lessons(repeated, str(job_id), title)

        logger.info(f"Project log written: {path.name}")
        return path


memory_service = MemoryService()
