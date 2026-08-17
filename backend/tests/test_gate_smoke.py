"""
Gate 8.4 — end-to-end smoke run. The one that actually matters.

Boots the FastAPI app against a real PostgreSQL database with the real Alembic
migrations applied, and drives research -> brief -> approve -> production with every
external API stubbed. SQLite is not an option: half the columns this pass wired are
JSONB.

Nothing here stubs the code under test. The prompt assembly, the beat grid, the
reference resolution, the QA gate and the memory writes all run for real; only the
network edges — CometAPI, Anthropic, OpenAI, Supabase, YouTube, ffmpeg — are replaced.
"""
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import httpx
import numpy as np
import pytest
import soundfile as sf
from sqlalchemy import select, text

import tasks.production as production
from app.db.session import AsyncSessionLocal
from app.models import GenerationOutcome

pytestmark = pytest.mark.smoke


BRIEF = {
    "title": "Descent Through the Kelp",
    "hook": "A diver drops into green light.",
    "narrative_goal": "Awe, then unease.",
    "music_mood": "Ambient, tidal",
    "color_palette": ["#0a3", "#023"],
    "storyboard": [
        {
            "scene_index": i,
            "narration": f"Beat {i}",
            "visual_prompt": f"The Diver descends past a kelp wall, shaft of light, shot {i}",
            "motion_prompt": "slow dolly in, 35mm anamorphic",
            "pacing": "Slow",
            "duration": 6,
            "bible_character": "The Diver",
            "bible_environment": "Kelp Forest",
        }
        for i in range(1, 5)
    ],
}

BIBLE = {
    "characters": [{
        "name": "The Diver",
        "physical": "tall, weathered, close-cropped grey hair",
        "wardrobe": "patched navy wetsuit",
        "expressions": ["resolute"],
        "role": "protagonist",
        "ref_sheet_url": None,
    }],
    "environments": [{
        "name": "Kelp Forest",
        "description": "a green cathedral of kelp",
        "lighting": "dappled god rays",
        "mood": "serene, faintly menacing",
        "time_of_day": "day",
        "ref_sheet_url": None,
    }],
    "style_lock": {
        "color_palette": ["#0a3", "#023"],
        "visual_rules": ["shallow depth of field"],
        "negative_prompt": "text, watermark",
        "looks": "cinematic film grain",
        "angles": "low angle",
    },
    "surreal_motifs": [],
    "camera_specs": {
        "default_lens": "35mm anamorphic",
        "default_movement": "slow dolly",
        "lighting_setup": "natural + fill",
    },
}

PASSING_VERDICT = {
    "pass": True,
    "character_match": 0.9,
    "style_match": 0.85,
    "prompt_adherence": 0.88,
    "artifacts": [],
    "notes": "Clean.",
}


class _FakeAnthropic:
    """Returns a fixed JSON payload for whatever it is asked, and records the prompt."""

    def __init__(self, payload):
        self.captured_system = None
        self._payload = payload
        self.messages = SimpleNamespace(create=self._create)

    async def _create(self, *, system=None, **_kwargs):
        self.captured_system = system
        return SimpleNamespace(content=[SimpleNamespace(text=json.dumps(self._payload))])


# --- infrastructure ----------------------------------------------------------

def _click_track(path: Path, bpm=120.0, seconds=24.0, sr=22050):
    interval = 60.0 / bpm
    y = np.zeros(int(seconds * sr), dtype=np.float32)
    click_len = int(0.02 * sr)
    click = (np.exp(-np.linspace(0, 12, click_len))
             * np.sin(2 * np.pi * 2000 * np.arange(click_len) / sr)).astype(np.float32)
    t = 0.0
    while t < seconds:
        start = int(t * sr)
        end = min(start + click_len, len(y))
        y[start:end] += click[: end - start]
        t += interval
    sf.write(path, y, sr)


@pytest.fixture
def stub_external_apis(monkeypatch, tmp_path):
    """Replace every network edge. Nothing inside the pipeline is stubbed."""
    from app.services import bible_service
    from app.services.ai_service import ai_service
    from app.services.assembly_service import assembly_service
    from app.services.claude_service import claude_service
    from app.services.media_gen_service import media_gen_service
    from app.services.qa_service import qa_service

    captured = {}

    # -- Anthropic ------------------------------------------------------
    async def _analyze_content(topic, text_content, source_type):
        return {
            "raw_analysis": f"Analysis of {topic} ({source_type}): {text_content[:200]}",
            "model": "stub",
            "analysis_type": "general_content",
        }

    monkeypatch.setattr(ai_service, "analyze_content", _analyze_content)

    brief_client = _FakeAnthropic(BRIEF)
    monkeypatch.setattr(claude_service, "client", brief_client)
    captured["brief_client"] = brief_client

    bible_client = _FakeAnthropic(BIBLE)
    monkeypatch.setattr(bible_service, "AsyncAnthropic", lambda **_kw: bible_client)

    # -- CometAPI -------------------------------------------------------
    async def _generate_image(prompt, model=None, **_kw):
        return {"url": f"https://cdn.stub/{abs(hash(prompt)) % 10**8}.jpg", "model": model}

    async def _animate_image(image_url, prompt, model, duration, mode, **_kw):
        captured.setdefault("durations", []).append(duration)
        return {"url": f"https://cdn.stub/clip-{len(captured['durations'])}.mp4", "task_id": "t"}

    monkeypatch.setattr(media_gen_service, "generate_image", _generate_image)
    monkeypatch.setattr(media_gen_service, "animate_image", _animate_image)

    # -- file transfers -------------------------------------------------
    async def _download_image(_url, dest: Path):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"\xff\xd8stub jpeg")
        return True

    async def _download_music(job_id, _url, _filename):
        dest = tmp_path / f"{job_id}.wav"
        _click_track(dest)
        return dest

    monkeypatch.setattr(production, "IMAGE_CACHE_DIR", tmp_path / "images")
    monkeypatch.setattr(production, "REFERENCE_CACHE_DIR", tmp_path / "refs")
    monkeypatch.setattr(production, "_download_image", _download_image)
    monkeypatch.setattr(production, "_download_music", _download_music)

    # -- QA vision ------------------------------------------------------
    def _capture(_source, dest: Path):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"\xff\xd8stub frame")
        return True

    async def _verdict(_frame, prompt):
        captured.setdefault("qa_prompts", []).append(prompt)
        return dict(PASSING_VERDICT)

    monkeypatch.setattr(qa_service, "capture_midpoint_frame", _capture)
    monkeypatch.setattr(qa_service, "_ask_claude", _verdict)

    # -- ffmpeg ---------------------------------------------------------
    async def _download_file(_url, dest: Path):
        dest.write_bytes(b"stub mp4")
        return None

    def _run_ffmpeg(concat_list: Path, _music, output_path: Path):
        captured["concat"] = Path(concat_list).read_text()
        output_path.write_bytes(b"stub assembled mp4")
        return {"output_path": str(output_path), "duration": 24.0, "file_size_bytes": 17}

    monkeypatch.setattr(assembly_service, "jobs_dir", tmp_path / "jobs")
    monkeypatch.setattr(assembly_service, "_download_file", _download_file)
    monkeypatch.setattr(assembly_service, "_ffmpeg_available", lambda: True)
    monkeypatch.setattr(assembly_service, "_run_ffmpeg", _run_ffmpeg)

    # -- memory: read the real files, write into the test's tmp dir ------
    # Copied rather than redirected, so the injection path still sees real content
    # while write_project_log and append_lessons cannot touch the repo.
    from app.services import memory_service as memory_module

    memory_copy = tmp_path / "memory"
    shutil.copytree(memory_module.MEMORY_ROOT, memory_copy)
    monkeypatch.setattr(memory_module, "MEMORY_ROOT", memory_copy)
    monkeypatch.setattr(memory_module, "PROJECT_LOG_DIR", memory_copy / "PROJECT_LOG")

    return captured


@pytest.fixture
def real_ffmpeg(stub_external_apis, monkeypatch, tmp_path):
    """
    Un-stub the two legs that shell out to ffmpeg.

    The stubbed run proves the wiring executes; it cannot prove the ffmpeg invocations
    are correct. In particular the beat-window trim rides on the concat demuxer's
    `outpoint` directive, which was chosen from the docs and never executed. This
    fixture hands the pipeline real MP4s and lets assembly and QA frame extraction run
    for real, so a wrong flag fails the gate instead of shipping.
    """
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        pytest.skip("ffmpeg/ffprobe not on PATH — cannot run the real-media smoke leg")

    from app.services.assembly_service import assembly_service
    from app.services.media_gen_service import media_gen_service
    from app.services.qa_service import qa_service

    clips_dir = tmp_path / "real_clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    def _make_clip(index: int, seconds: int) -> Path:
        dest = clips_dir / f"clip_{index}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=size=320x180:rate=24:duration={seconds}",
             "-f", "lavfi", "-i", f"sine=frequency={220 * (index + 1)}:duration={seconds}",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
             str(dest), "-loglevel", "error"],
            check=True, capture_output=True, timeout=120,
        )
        return dest

    # The generator returns a real file on disk instead of a CDN URL, so QA's ffprobe
    # and frame extraction have something to actually read.
    async def _animate_image(image_url, prompt, model, duration, mode, **_kw):
        stub_external_apis.setdefault("durations", []).append(duration)
        index = len(stub_external_apis["durations"]) - 1
        return {"url": str(_make_clip(index, duration)), "task_id": "t"}

    # Still the network edge: assembly "downloads" by copying from disk. The music URL
    # is the one input with no local original, so it resolves to a real click track —
    # which means ffmpeg's audio mix runs for real too.
    music_file = tmp_path / "real_music.wav"
    _click_track(music_file)

    async def _download_file(url, dest: Path):
        source = Path(url)
        shutil.copyfile(source if source.is_file() else music_file, dest)
        return None

    monkeypatch.setattr(media_gen_service, "animate_image", _animate_image)
    monkeypatch.setattr(assembly_service, "_download_file", _download_file)

    # Put the real implementations back over the stubs installed above.
    for target, name in (
        (assembly_service, "_ffmpeg_available"),
        (assembly_service, "_run_ffmpeg"),
        (qa_service, "capture_midpoint_frame"),
    ):
        original = getattr(type(target), name)
        monkeypatch.setattr(target, name, original.__get__(target))

    return stub_external_apis


@pytest.fixture
async def api(clean_database, stub_external_apis):
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://smoke") as client:
        yield client


# --- the run -----------------------------------------------------------------

async def _drive_pipeline(api) -> dict:
    """research -> brief -> approve -> production. Returns the final job detail."""
    research = await api.post("/api/research/start", json={
        "topic": "a diver descending through a kelp forest",
        "source_type": "text_brief",
        "source_data": {"text": "Slow, green, tidal. One character. No dialogue."},
    })
    assert research.status_code == 200, research.text
    research_id = research.json()["id"]

    # BackgroundTasks run inside the ASGI call, so the job is terminal on return.
    detail = await api.get(f"/api/research/{research_id}")
    assert detail.json()["status"] == "completed", detail.text

    curation = await api.post("/api/curation/start", json={"research_job_id": research_id})
    assert curation.status_code == 200, curation.text
    curation_id = curation.json()["id"]

    brief_state = await api.get(f"/api/curation/{curation_id}")
    assert brief_state.json()["status"] == "completed", brief_state.text
    assert brief_state.json()["num_scenes"] == len(BRIEF["storyboard"])

    approved = await api.put(f"/api/curation/{curation_id}/approve", json={})
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    started = await api.post(
        "/api/production/start",
        params={"music_url": "https://stub/track.wav", "music_filename": "track.wav"},
        json={"curation_job_id": curation_id, "animation_mode": "std", "beat_sync_enabled": True},
    )
    assert started.status_code == 200, started.text
    production_id = started.json()["id"]

    final = await api.get(f"/api/production/{production_id}")
    assert final.status_code == 200, final.text
    return final.json()


async def test_full_pipeline_reaches_a_terminal_state_with_every_column_populated(
    api, stub_external_apis
):
    detail = await _drive_pipeline(api)
    job, scenes = detail["job"], detail["scenes"]

    assert job["status"] in ("completed", "qa_review"), job["error_message"]
    assert len(scenes) == len(BRIEF["storyboard"])

    for scene in scenes:
        assert scene["animation_status"] is not None
        assert scene["qa_status"] is not None
        assert scene["reference_inputs"] is not None
        assert scene["reference_inputs"]["mode"] in ("reference", "text")

    # Music was supplied, so the beat grid must be populated.
    assert job["tempo_bpm"] is not None
    assert abs(job["tempo_bpm"] - 120.0) <= 2.0
    for scene in scenes:
        assert scene["beat_start_sec"] is not None
        assert scene["beat_end_sec"] is not None

    async with AsyncSessionLocal() as session:
        outcomes = (await session.execute(
            select(GenerationOutcome).where(GenerationOutcome.job_id == job["id"])
        )).scalars().all()

    assert len(outcomes) == len(scenes), "expected exactly one outcome row per scene"
    for outcome in outcomes:
        assert outcome.qa_pass is not None
        assert outcome.reference_mode in ("reference", "text")
        assert outcome.beat_aligned is True


async def test_clip_durations_come_from_the_beat_grid_not_a_hardcoded_five(
    api, stub_external_apis
):
    await _drive_pipeline(api)
    durations = stub_external_apis["durations"]

    assert len(durations) == len(BRIEF["storyboard"])
    assert all(isinstance(d, int) for d in durations)
    # 24s of 120 BPM audio over 4 scenes is a 6s window each — not the old fixed 5.
    assert durations == [6, 6, 6, 6], durations


async def test_assembly_trims_each_clip_to_its_beat_window(api, stub_external_apis):
    await _drive_pipeline(api)
    concat = stub_external_apis["concat"]
    outpoints = [ln for ln in concat.splitlines() if ln.startswith("outpoint")]
    assert len(outpoints) == len(BRIEF["storyboard"])


async def test_the_brief_prompt_carries_skills_bible_camera_specs_and_memory(
    api, stub_external_apis
):
    await _drive_pipeline(api)
    system = stub_external_apis["brief_client"].captured_system

    # CurationJob.video_model defaults to kling-v3, so the kling skill set is selected.
    assert "Production Skills" in system, "no disk skills reached the brief"
    assert "music-video-producer" in system
    assert "multi-shot-camera-coverage" in system

    assert "The Diver" in system, "bible characters did not reach the brief"
    assert "35mm anamorphic" in system, "camera_specs did not reach the brief"
    assert "Director Memory" in system, "memory did not reach the brief"


async def test_a_seedance_job_pulls_the_seedance_camera_controls(api, stub_external_apis):
    """The other half of skill selection: a Seedance model gets the Seedance block."""
    from app.services.skill_loader_service import skill_loader_service

    block = await skill_loader_service.build_prompt_block(
        animation_model="doubao-seedance-2-0", include_db_skills=False
    )
    assert "SEEDANCE NATIVE CAMERA CONTROLS" in block


async def test_the_qa_prompt_carries_the_bible_constraints(api, stub_external_apis):
    await _drive_pipeline(api)
    prompts = stub_external_apis["qa_prompts"]

    assert len(prompts) == len(BRIEF["storyboard"])
    assert "The Diver" in prompts[0]
    assert "patched navy wetsuit" in prompts[0]
    assert "shallow depth of field" in prompts[0]


async def test_an_approval_survives_a_reload_and_reaches_the_outcome_row(api):
    detail = await _drive_pipeline(api)
    scene_id = detail["scenes"][0]["id"]

    approve = await api.put(
        f"/api/production/scene/{scene_id}/approve",
        json={"approved": True, "feedback": "the light is right"},
    )
    assert approve.status_code == 200, approve.text
    assert approve.json()["outcome_recorded"] is True

    # Re-read through the API: this is the "reload the page" half of the acceptance.
    reloaded = await api.get(f"/api/production/{detail['job']['id']}")
    scene = next(s for s in reloaded.json()["scenes"] if s["id"] == scene_id)
    assert scene["user_approved"] is True
    assert scene["user_feedback"] == "the light is right"

    async with AsyncSessionLocal() as session:
        outcome = (await session.execute(
            select(GenerationOutcome).where(GenerationOutcome.scene_id == scene_id)
        )).scalar_one()
    assert outcome.user_approved is True


async def test_a_failing_qa_verdict_holds_the_job_and_blocks_assembly(
    api, stub_external_apis, monkeypatch
):
    from app.services.qa_service import qa_service

    async def _failing(_frame, _prompt):
        return {
            "pass": False, "character_match": 0.1, "style_match": 0.2,
            "prompt_adherence": 0.3, "artifacts": ["face melts"], "notes": "unusable",
        }

    monkeypatch.setattr(qa_service, "_ask_claude", _failing)

    detail = await _drive_pipeline(api)
    assert detail["job"]["status"] == "qa_review"
    assert detail["job"]["assembled_video_path"] is None
    assert all(s["qa_status"] == "fail" for s in detail["scenes"])
    assert "concat" not in stub_external_apis, "assembly ran despite a failing QA verdict"

    # The override is the only way past the gate.
    override = await api.post(f"/api/production/{detail['job']['id']}/assemble-anyway")
    assert override.status_code == 200, override.text
    assert override.json()["qa_failures_overridden"] == len(detail["scenes"])
    assert "concat" in stub_external_apis


async def test_qa_disabled_reproduces_todays_behaviour(api, stub_external_apis, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "QA_ENABLED", False)

    detail = await _drive_pipeline(api)
    assert detail["job"]["status"] == "completed"
    assert all(s["qa_status"] == "skipped" for s in detail["scenes"])


async def test_a_job_with_no_music_completes_with_null_beat_columns(api, stub_external_apis):
    research = await api.post("/api/research/start", json={
        "topic": "silent descent", "source_type": "text_brief",
        "source_data": {"text": "No music."},
    })
    research_id = research.json()["id"]
    curation = await api.post("/api/curation/start", json={"research_job_id": research_id})
    curation_id = curation.json()["id"]
    await api.put(f"/api/curation/{curation_id}/approve", json={})

    started = await api.post("/api/production/start", json={
        "curation_job_id": curation_id, "animation_mode": "std", "beat_sync_enabled": False,
    })
    job_id = started.json()["id"]

    detail = (await api.get(f"/api/production/{job_id}")).json()
    assert detail["job"]["status"] == "completed", detail["job"]["error_message"]
    assert detail["job"]["tempo_bpm"] is None

    for scene in detail["scenes"]:
        assert scene["beat_start_sec"] is None
        assert scene["beat_end_sec"] is None
        assert scene["beat_duration_sec"] is None
        assert scene["beat_drift_ms"] is None

    # The brief's per-scene duration is the fallback, not the old hardcoded 5.
    assert stub_external_apis["durations"] == [6, 6, 6, 6]


async def test_the_project_log_is_written_once_per_job(api, stub_external_apis, tmp_path):
    from app.services.memory_service import memory_service

    detail = await _drive_pipeline(api)
    log_dir = tmp_path / "memory" / "PROJECT_LOG"

    def _logs():
        return sorted(p for p in log_dir.glob("*.md") if p.name != "README.md")

    logs = _logs()
    assert len(logs) == 1, [p.name for p in logs]
    assert "Descent Through the Kelp" in logs[0].read_text()

    # write_project_log is idempotent: a second call produces one file, not two.
    await memory_service.write_project_log(detail["job"]["id"])
    assert len(_logs()) == 1


async def test_migrations_produced_the_columns_this_pass_added(clean_database):
    async with AsyncSessionLocal() as session:
        rows = await session.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'production_scenes'"
        ))
        columns = {r[0] for r in rows}

    assert {"reference_inputs", "user_approved", "user_feedback"} <= columns

    async with AsyncSessionLocal() as session:
        rows = await session.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'generation_outcome'"
        ))
        outcome_columns = {r[0] for r in rows}

    assert {"scene_id", "job_id", "model", "prompt", "reference_mode",
            "beat_aligned", "qa_pass", "qa_scores", "user_approved"} <= outcome_columns


# --- real media: the ffmpeg legs, un-stubbed ---------------------------------

async def test_the_real_pipeline_produces_a_playable_video(api, real_ffmpeg):
    """
    Same drive as above, but assembly and QA frame extraction shell out to real ffmpeg
    against real MP4s. This is the leg that proves the invocations are right, not just
    that the code reaches them.
    """
    detail = await _drive_pipeline(api)
    job = detail["job"]

    assert job["status"] == "completed", job["error_message"]
    output = Path(job["assembled_video_path"])
    assert output.is_file() and output.stat().st_size > 10_000, "no real video was written"

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(output)],
        capture_output=True, text=True, timeout=60,
    )
    duration = float(probe.stdout.strip())

    # Four 6s beat windows over a 24s track.
    expected = sum(s["beat_end_sec"] - s["beat_start_sec"] for s in detail["scenes"])
    assert abs(duration - expected) < 1.0, f"assembled {duration:.2f}s, expected ~{expected:.2f}s"

    # QA read a real frame out of each real clip rather than being handed a stub.
    assert len(real_ffmpeg["qa_prompts"]) == len(detail["scenes"])
    assert all(s["qa_status"] == "pass" for s in detail["scenes"])
