"""
Item 4 acceptance — a real QA gate.

Nothing used to distinguish a good clip from a garbled one: the only success criterion
was that an HTTP call returned and a URL could be extracted. qa_status and qa_notes
were columns with zero assignments anywhere.
"""
import json
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

import tasks.production as production
from app.services.qa_service import FAIL, PASS, SKIPPED, qa_service

PASSING_VERDICT = {
    "pass": True,
    "character_match": 0.92,
    "style_match": 0.88,
    "prompt_adherence": 0.9,
    "artifacts": [],
    "notes": "Clean frame, character and palette on model.",
}

FAILING_VERDICT = {
    "pass": False,
    "character_match": 0.21,
    "style_match": 0.35,
    "prompt_adherence": 0.4,
    "artifacts": ["face melts at the jaw", "seven fingers"],
    "notes": "Wrong character and visible hand deformation.",
}


class _FakeScene:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.job_id = kwargs.get("job_id", uuid.uuid4())
        self.image_prompt = "a diver in a kelp forest"
        self.bible_character = kwargs.get("bible_character")
        self.bible_environment = None
        self.local_video_path = kwargs.get("local_video_path", "https://cdn.test/clip.mp4")
        self.animation_status = "completed"
        self.qa_status = "pending"
        self.qa_notes = None


class _FakeDb:
    async def commit(self):
        pass


# --- classification ----------------------------------------------------------

def test_a_clean_verdict_passes():
    assert qa_service.classify(PASSING_VERDICT) == PASS


def test_an_explicit_failure_fails():
    assert qa_service.classify(FAILING_VERDICT) == FAIL


def test_a_low_character_score_fails_even_when_the_model_says_pass(monkeypatch):
    monkeypatch.setattr(production.settings, "QA_FAIL_THRESHOLD", 0.6)
    verdict = dict(PASSING_VERDICT, character_match=0.4)
    assert qa_service.classify(verdict) == FAIL


def test_a_low_style_score_fails_even_when_the_model_says_pass():
    verdict = dict(PASSING_VERDICT, style_match=0.1)
    assert qa_service.classify(verdict) == FAIL


def test_prompt_adherence_is_recorded_but_not_gated():
    verdict = dict(PASSING_VERDICT, prompt_adherence=0.05)
    assert qa_service.classify(verdict) == PASS


def test_the_threshold_is_configurable(monkeypatch):
    from app.core.config import settings

    verdict = dict(PASSING_VERDICT, style_match=0.7)
    monkeypatch.setattr(settings, "QA_FAIL_THRESHOLD", 0.6)
    assert qa_service.classify(verdict) == PASS
    monkeypatch.setattr(settings, "QA_FAIL_THRESHOLD", 0.8)
    assert qa_service.classify(verdict) == FAIL


def test_unparseable_scores_do_not_crash_the_gate():
    assert qa_service.classify(dict(PASSING_VERDICT, character_match="high")) == PASS


# --- the review call ---------------------------------------------------------

def test_review_prompt_carries_the_bible_constraints():
    prompt = qa_service.build_review_prompt(
        image_prompt="a diver descends",
        style_lock={
            "color_palette": ["#0af", "#023"],
            "visual_rules": ["shallow depth of field"],
            "negative_prompt": "text, watermark",
        },
        character={"name": "The Diver", "physical": "tall, grey hair", "wardrobe": "navy wetsuit"},
    )
    assert "a diver descends" in prompt
    assert "The Diver" in prompt
    assert "navy wetsuit" in prompt
    assert "shallow depth of field" in prompt
    assert "text, watermark" in prompt


def test_review_prompt_without_a_character_says_so():
    prompt = qa_service.build_review_prompt("a wide shot", {}, None)
    assert "none specified" in prompt


async def test_review_is_skipped_when_qa_is_disabled(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "QA_ENABLED", False)
    result = await qa_service.review_scene(video_source="https://cdn.test/clip.mp4")
    assert result["status"] == SKIPPED


async def test_review_is_skipped_when_there_is_no_clip():
    result = await qa_service.review_scene(video_source=None)
    assert result["status"] == SKIPPED


async def test_review_is_skipped_when_frame_extraction_fails(monkeypatch):
    monkeypatch.setattr(qa_service, "capture_midpoint_frame", lambda *_a, **_kw: False)
    result = await qa_service.review_scene(video_source="https://cdn.test/clip.mp4")
    assert result["status"] == SKIPPED
    assert "frame extraction" in result["verdict"]["reason"]


async def test_review_is_skipped_when_the_vision_call_raises(monkeypatch):
    def _fake_capture(_source, dest: Path):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"\xff\xd8fake jpeg")
        return True

    async def _boom(*_a, **_kw):
        raise RuntimeError("anthropic is down")

    monkeypatch.setattr(qa_service, "capture_midpoint_frame", _fake_capture)
    monkeypatch.setattr(qa_service, "_ask_claude", _boom)

    result = await qa_service.review_scene(video_source="https://cdn.test/clip.mp4")
    assert result["status"] == SKIPPED


@pytest.fixture
def stub_vision(monkeypatch):
    """Stub the ffmpeg + Claude legs of qa_service, returning a fixed verdict."""

    def _stub(verdict):
        def _fake_capture(_source, dest: Path):
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"\xff\xd8fake jpeg")
            return True

        async def _fake_ask(_frame, _prompt):
            return verdict

        monkeypatch.setattr(qa_service, "capture_midpoint_frame", _fake_capture)
        monkeypatch.setattr(qa_service, "_ask_claude", _fake_ask)

    return _stub


async def test_a_stubbed_failing_verdict_produces_a_fail(stub_vision):
    stub_vision(FAILING_VERDICT)
    result = await qa_service.review_scene(video_source="https://cdn.test/clip.mp4")
    assert result["status"] == FAIL
    assert result["verdict"]["artifacts"] == FAILING_VERDICT["artifacts"]


# --- persistence onto the scene ---------------------------------------------

async def _review(scene, bible, monkeypatch):
    async def _load(_db, _scene):
        return bible

    monkeypatch.setattr(production, "_load_scene_bible", _load)
    return await production._qa_review_scene(_FakeDb(), scene)


async def test_a_failing_verdict_is_persisted(stub_vision, monkeypatch):
    stub_vision(FAILING_VERDICT)
    scene = _FakeScene(bible_character="The Diver")
    bible = SimpleNamespace(
        characters=[{"name": "The Diver", "physical": "tall", "wardrobe": "wetsuit"}],
        environments=[],
        style_lock={"color_palette": ["#0af"]},
    )

    status = await _review(scene, bible, monkeypatch)

    assert status == FAIL
    assert scene.qa_status == FAIL
    assert json.loads(scene.qa_notes)["artifacts"] == FAILING_VERDICT["artifacts"]


async def test_a_passing_verdict_is_persisted(stub_vision, monkeypatch):
    stub_vision(PASSING_VERDICT)
    scene = _FakeScene()
    status = await _review(scene, None, monkeypatch)

    assert status == PASS
    assert scene.qa_status == PASS
    assert json.loads(scene.qa_notes)["character_match"] == pytest.approx(0.92)


async def test_qa_disabled_marks_the_scene_skipped(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "QA_ENABLED", False)
    scene = _FakeScene()
    status = await _review(scene, None, monkeypatch)

    assert status == SKIPPED
    assert scene.qa_status == SKIPPED
    assert json.loads(scene.qa_notes)["reason"] == "QA_ENABLED is false"


# --- the assembly gate -------------------------------------------------------

def test_the_pipeline_stops_before_assembly_on_a_failure(backend_root):
    source = (backend_root / "tasks" / "production.py").read_text(encoding="utf-8")
    gate_at = source.index("failed = await _count_qa_failures(job_id)")
    assemble_at = source.index("await _assemble_video(job_id, scene_ids, music_url)")
    assert gate_at < assemble_at, "the QA gate must sit before Phase 4"
    between = source[gate_at:assemble_at]
    assert 'await _update_status(job_id, "qa_review")' in between
    assert "return" in between


def test_only_fail_counts_as_a_qa_failure(backend_root):
    """A skipped review must not hold a job — it is an absence of judgement."""
    source = (backend_root / "tasks" / "production.py").read_text(encoding="utf-8")
    assert 'ProductionScene.qa_status == "fail"' in source
    assert 'ProductionScene.qa_status != "pass"' not in source


def test_assemble_anyway_route_exists_and_assemble_is_an_alias():
    from app.api import production as production_api

    paths = {getattr(r, "path", "") for r in production_api.router.routes}
    assert "/{job_id}/assemble-anyway" in paths
    assert "/{job_id}/assemble" in paths
