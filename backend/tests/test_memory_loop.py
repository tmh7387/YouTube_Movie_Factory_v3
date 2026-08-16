"""
Item 5 acceptance — approvals persist and the learning loop closes.

Scene approvals lived in a React useState Set and were never sent to the server, skill
confidence_score was set once by Claude and never touched again, and the five memory
files under .agent/music-video-director/memory/ were read by no code at all.
"""
import json
from types import SimpleNamespace

import pytest

import tasks.production as production
from app.services.claude_service import claude_service
from app.services.memory_service import (
    CONFIDENCE_PRIOR_WEIGHT,
    LESSON_REPEAT_THRESHOLD,
    MemoryService,
    memory_service,
)
from tests.test_landmines import _CapturingAnthropicClient


def _outcome(qa_pass=None, user_approved=None):
    return SimpleNamespace(qa_pass=qa_pass, user_approved=user_approved)


def _scene(number, qa_status="pass", artifacts=None, user_feedback=None, user_approved=None):
    notes = json.dumps({"artifacts": artifacts or [], "pass": qa_status == "pass"})
    return SimpleNamespace(
        scene_number=number,
        qa_status=qa_status,
        qa_notes=notes,
        user_feedback=user_feedback,
        user_approved=user_approved,
        reference_inputs={"mode": "reference"},
        beat_start_sec=1.0,
    )


# --- memory injection --------------------------------------------------------

def test_memory_block_reads_the_files_that_were_read_by_nothing():
    block = memory_service.build_memory_block()
    assert block, "memory block is empty — the memory files are not being read"
    assert "Director Memory" in block


def test_memory_block_respects_the_token_budget():
    block = memory_service.build_memory_block(char_budget=400)
    # The header is fixed overhead; the memory content itself must obey the budget.
    assert len(block) < 400 + 500


def test_memory_block_is_empty_when_there_is_no_memory(monkeypatch):
    monkeypatch.setattr(MemoryService, "_read", staticmethod(lambda _name: ""))
    assert MemoryService().build_memory_block() == ""


def test_trimming_keeps_newest_sections_and_never_splits_one():
    markdown = "preamble\n\n" + "".join(
        f"## Entry {i}\n\nbody text for entry {i}\n\n" for i in range(1, 6)
    )
    trimmed = MemoryService._newest_first_sections(markdown, budget=80)
    assert "## Entry 1" in trimmed
    assert "## Entry 5" not in trimmed
    # No half-written section survived the trim.
    assert trimmed.count("## ") == trimmed.count("body text for entry")


async def test_memory_block_reaches_the_assembled_system_prompt(monkeypatch):
    """Assert on the prompt string, not on model output."""
    fake = _CapturingAnthropicClient({"title": "T", "storyboard": []})
    monkeypatch.setattr(claude_service, "client", fake)

    await claude_service.generate_creative_brief(
        "analysis",
        memory_block="## Director Memory — what previous productions taught us\n\nSENTINEL-LESSON",
    )

    assert "SENTINEL-LESSON" in fake.captured_system


async def test_curation_passes_memory_into_the_brief(backend_root):
    source = (backend_root / "tasks" / "curation.py").read_text(encoding="utf-8")
    assert "memory_service.build_memory_block()" in source
    assert "memory_block=memory_block" in source


# --- confidence scoring ------------------------------------------------------

def test_confidence_rises_with_passing_outcomes():
    outcomes = [_outcome(qa_pass=True) for _ in range(10)]
    score = MemoryService.score_outcomes(outcomes, prior=0.5)
    assert score > 0.5


def test_confidence_falls_with_failing_outcomes():
    outcomes = [_outcome(qa_pass=False) for _ in range(10)]
    score = MemoryService.score_outcomes(outcomes, prior=0.9)
    assert score < 0.5


def test_a_human_verdict_counts_double():
    machine_only = MemoryService.score_outcomes([_outcome(qa_pass=False)], prior=1.0)
    with_human = MemoryService.score_outcomes(
        [_outcome(qa_pass=False, user_approved=False)], prior=1.0
    )
    assert with_human < machine_only


def test_a_human_approval_offsets_a_qa_failure():
    """A clip QA disliked but a human kept is half a success, not a total loss."""
    both_bad = MemoryService.score_outcomes([_outcome(qa_pass=False, user_approved=False)], prior=None)
    split = MemoryService.score_outcomes([_outcome(qa_pass=False, user_approved=True)], prior=None)
    assert both_bad == 0.0
    assert split == pytest.approx(0.5)


def test_one_bad_scene_cannot_wipe_out_a_confident_skill():
    score = MemoryService.score_outcomes([_outcome(qa_pass=False)], prior=1.0)
    expected = CONFIDENCE_PRIOR_WEIGHT / (CONFIDENCE_PRIOR_WEIGHT + 1.0)
    assert score == pytest.approx(round(expected, 4))


def test_scoring_with_no_signal_at_all_returns_none():
    assert MemoryService.score_outcomes([], prior=None) is None
    assert MemoryService.score_outcomes([_outcome()], prior=None) is None


# --- project log -------------------------------------------------------------

def test_failure_categories_are_counted_across_scenes():
    scenes = [
        _scene(1, "fail", artifacts=["Six fingers", "warped face"]),
        _scene(2, "fail", artifacts=["six  fingers"]),
        _scene(3, "pass"),
    ]
    counts = MemoryService._failure_categories(scenes)
    assert counts["six fingers"] == 2
    assert counts["warped face"] == 1


def test_passing_scenes_contribute_no_failure_categories():
    assert MemoryService._failure_categories([_scene(1, "pass", artifacts=["ignored"])]) == {}


def test_log_filename_is_deterministic():
    svc = MemoryService()
    first = svc.log_path_for("abcdef12-0000-0000-0000-000000000000", "Chrome Runway", None)
    second = svc.log_path_for("abcdef12-0000-0000-0000-000000000000", "Chrome Runway", None)
    assert first == second
    assert "chrome-runway" in first.name
    assert "abcdef12" in first.name


def test_rendered_log_reports_what_the_job_did():
    scenes = [_scene(1, "fail", artifacts=["warped face"], user_feedback="hands are wrong"),
              _scene(2, "pass", user_approved=True)]
    body = MemoryService.render_project_log({
        "job_id": "job-1", "title": "Chrome Runway", "status": "qa_review",
        "completed_at": "2026-08-16T00:00:00+00:00", "scenes": scenes,
        "qa_pass": 1, "qa_fail": 1, "qa_skipped": 0,
        "approved": 1, "rejected": 0, "unreviewed": 1,
        "reference_scenes": 2, "beat_scenes": 2, "tempo_bpm": 128.0,
        "failure_categories": MemoryService._failure_categories(scenes),
    })
    assert "# Chrome Runway" in body
    assert "<!-- job:job-1 -->" in body
    assert "warped face — 1 scene(s)" in body
    assert "hands are wrong" in body
    assert "128.0 BPM" in body


def test_lessons_are_appended_newest_first_and_only_once(tmp_path, monkeypatch):
    lessons = tmp_path / "LESSONS.md"
    lessons.write_text(
        "# LESSONS.md — Accumulated Director Wisdom\n\npreamble text\n\n"
        "## 2026-08-14 — Older lesson\n\nolder body\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("app.services.memory_service.MEMORY_ROOT", tmp_path)

    svc = MemoryService()
    assert svc.append_lessons(["warped face recurred on 4 scenes"], "job-9", "Chrome Runway") is True

    body = lessons.read_text(encoding="utf-8")
    assert body.startswith("# LESSONS.md")
    assert "preamble text" in body
    assert body.index("Chrome Runway") < body.index("Older lesson"), "new lesson must go on top"

    # Idempotent: the same job never lands twice.
    assert svc.append_lessons(["warped face recurred on 4 scenes"], "job-9", "Chrome Runway") is False
    assert lessons.read_text(encoding="utf-8").count("<!-- job:job-9 -->") == 1


def test_no_lesson_is_written_without_entries(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.memory_service.MEMORY_ROOT", tmp_path)
    assert MemoryService().append_lessons([], "job-1", "Anything") is False
    assert not (tmp_path / "LESSONS.md").exists()


def test_the_repeat_threshold_is_what_promotes_a_failure_to_a_lesson():
    assert LESSON_REPEAT_THRESHOLD == 3


# --- outcome rows ------------------------------------------------------------

class _RecordingDb:
    def __init__(self, existing=None):
        self.added = []
        self.existing = existing

    async def execute(self, _stmt):
        row = self.existing
        return SimpleNamespace(scalar_one_or_none=lambda: row)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass


async def test_one_outcome_row_is_written_per_scene(monkeypatch):
    async def _noop(_slugs):
        return None

    monkeypatch.setattr(production.memory_service, "increment_usage", _noop)

    scene = SimpleNamespace(
        id="scene-1", job_id="job-1", animation_model="doubao-seedance-2-0",
        reference_inputs={"mode": "reference"}, beat_start_sec=2.0,
        qa_status="pass",
        qa_notes=json.dumps({"character_match": 0.9, "style_match": 0.8, "artifacts": []}),
    )
    db = _RecordingDb()
    await production._record_generation_outcome(db, scene, "slow dolly in", "doubao-seedance-2-0")

    assert len(db.added) == 1
    row = db.added[0]
    assert row.scene_id == "scene-1"
    assert row.reference_mode == "reference"
    assert row.beat_aligned is True
    assert row.qa_pass is True
    assert row.qa_scores["character_match"] == 0.9
    assert "seedance2-director" in row.skill_slugs


async def test_re_animating_updates_the_existing_outcome_row(monkeypatch):
    async def _noop(_slugs):
        return None

    monkeypatch.setattr(production.memory_service, "increment_usage", _noop)

    existing = SimpleNamespace(
        scene_id="scene-1", job_id=None, model=None, prompt=None, reference_mode=None,
        beat_aligned=None, qa_pass=None, qa_scores=None, skill_slugs=None,
    )
    scene = SimpleNamespace(
        id="scene-1", job_id="job-1", animation_model="kling-v2-master",
        reference_inputs=None, beat_start_sec=None, qa_status="fail", qa_notes="{}",
    )
    db = _RecordingDb(existing=existing)
    await production._record_generation_outcome(db, scene, "push in", "kling_video")

    assert db.added == []
    assert existing.qa_pass is False
    assert existing.reference_mode is None
    assert existing.beat_aligned is False


async def test_a_skipped_qa_verdict_leaves_qa_pass_unknown(monkeypatch):
    async def _noop(_slugs):
        return None

    monkeypatch.setattr(production.memory_service, "increment_usage", _noop)

    scene = SimpleNamespace(
        id="s", job_id="j", animation_model="", reference_inputs=None,
        beat_start_sec=None, qa_status="skipped", qa_notes="{}",
    )
    db = _RecordingDb()
    await production._record_generation_outcome(db, scene, "p", "m")
    assert db.added[0].qa_pass is None


# --- the approval endpoint ---------------------------------------------------

def test_approve_route_exists_with_the_documented_shape():
    from app.api import production as production_api

    route = next(
        r for r in production_api.router.routes
        if getattr(r, "path", "") == "/scene/{scene_id}/approve"
    )
    assert "PUT" in route.methods
    assert set(production_api.SceneApprovalRequest.model_fields) == {"approved", "feedback"}


def test_the_frontend_sends_approvals_to_the_server(repo_root):
    service = (repo_root / "frontend" / "src" / "services" / "production.ts").read_text()
    page = (repo_root / "frontend" / "src" / "pages" / "Production.tsx").read_text()

    assert "approveScene" in service
    assert "/approve" in service
    # Approval state comes off the server row, not a local Set.
    assert "useState<Set<string>>" not in page
    assert "s.user_approved === true" in page


def test_the_amber_copy_is_now_true(repo_root):
    """
    The 'approve before assembling' line used to sit on top of a pipeline that had
    already assembled. With the QA gate in place, assembly genuinely waits.
    """
    page = (repo_root / "frontend" / "src" / "pages" / "Production.tsx").read_text()
    backend = (repo_root / "backend" / "tasks" / "production.py").read_text()

    assert "Preview and approve each scene before assembling" in page
    assert 'await _update_status(job_id, "qa_review")' in backend
    gate_at = backend.index("failed = await _count_qa_failures(job_id)")
    assemble_at = backend.index("await _assemble_video(job_id, scene_ids, music_url)")
    assert gate_at < assemble_at
