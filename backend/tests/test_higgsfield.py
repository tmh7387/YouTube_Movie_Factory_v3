"""
Higgsfield as the primary generator, CometAPI as the fallback.

Higgsfield publishes no HTTP API, so the app drives its CLI — the same way it already
drives ffmpeg, ffprobe and yt-dlp. These tests stub the subprocess, so they assert on
the command we build and on how we read the reply, which is where the breakage lives.

The reply schema is undocumented. The parser is deliberately tolerant, and these tests
pin that tolerance so a key moving one level deeper does not stop production.
"""
import json
from types import SimpleNamespace

import pytest

import tasks.production as production
from app.core.config import settings
from app.services.higgsfield_service import HiggsfieldService, higgsfield_service


@pytest.fixture
def cli(monkeypatch, tmp_path):
    """Stub the CLI subprocess; record the argv of every call."""
    calls = []

    def _install(stdout="", returncode=0, stderr=""):
        class _Process:
            def __init__(self, out, err, code):
                self._out, self._err = out, err
                self.returncode = code

            async def communicate(self):
                return self._out, self._err

        async def _exec(binary, *args, **_kwargs):
            calls.append([binary, *args])
            return _Process(stdout.encode(), stderr.encode(), returncode)

        monkeypatch.setattr(
            "app.services.higgsfield_service.asyncio.create_subprocess_exec", _exec
        )
        monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
        monkeypatch.setattr(higgsfield_service, "_authenticated", True)
        monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)
        return calls

    return _install


@pytest.fixture
def reference(tmp_path):
    path = tmp_path / "diver.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n reference")
    return str(path)


# --- the command we build ----------------------------------------------------

async def test_a_reference_uses_the_reference_model_and_passes_the_file(cli, reference):
    calls = cli(stdout=json.dumps({"results": [{"url": "https://cdn.hf/x.png"}]}))

    result = await higgsfield_service.generate_image("a diver", reference_paths=[reference])

    assert result["url"] == "https://cdn.hf/x.png"
    assert result["character_consistent"] is True
    argv = calls[0]
    assert argv[1:4] == ["generate", "create", settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL]
    assert "--image-references" in argv
    assert "--json" in argv and "--wait" in argv


async def test_no_reference_uses_the_plain_image_model(cli):
    calls = cli(stdout=json.dumps({"url": "https://cdn.hf/x.png"}))

    result = await higgsfield_service.generate_image("a kelp forest")

    assert result["character_consistent"] is False
    assert calls[0][3] == settings.HIGGSFIELD_IMAGE_MODEL
    assert "--image-references" not in calls[0]


async def test_references_are_capped(cli, tmp_path):
    paths = []
    for i in range(5):
        p = tmp_path / f"r{i}.png"
        p.write_bytes(b"x")
        paths.append(str(p))
    calls = cli(stdout=json.dumps({"url": "https://cdn.hf/x.png"}))

    await higgsfield_service.generate_image("a diver", reference_paths=paths)
    assert calls[0].count("--image-references") == settings.HIGGSFIELD_MAX_REFERENCES


async def test_a_missing_reference_file_is_dropped_not_sent(cli):
    calls = cli(stdout=json.dumps({"url": "https://cdn.hf/x.png"}))
    result = await higgsfield_service.generate_image("a diver", reference_paths=["/nope.png"])

    assert "--image-references" not in calls[0]
    assert result["character_consistent"] is False


async def test_animation_sends_the_local_start_frame_and_duration(cli, reference):
    calls = cli(stdout=json.dumps({"url": "https://cdn.hf/clip.mp4"}))

    result = await higgsfield_service.animate_image(reference, prompt="slow dolly", duration=6)

    assert result["url"] == "https://cdn.hf/clip.mp4"
    argv = calls[0]
    assert argv[3] == settings.HIGGSFIELD_VIDEO_MODEL
    assert "--start-image" in argv
    assert argv[argv.index("--duration") + 1] == "6"


async def test_animating_a_missing_file_is_an_error_not_a_crash(cli):
    cli(stdout="{}")
    result = await higgsfield_service.animate_image("/nope.png")
    assert "error" in result


# --- how we read the reply ---------------------------------------------------

@pytest.mark.parametrize(
    "payload",
    [
        {"url": "https://cdn.hf/a.png"},
        {"results": [{"url": "https://cdn.hf/a.png"}]},
        {"data": {"output": {"result_url": "https://cdn.hf/a.png"}}},
        [{"jobs": [{"assets": [{"download_url": "https://cdn.hf/a.png"}]}]}],
        {"job": {"deeply": {"nested": {"anything": "https://cdn.hf/a.png"}}}},
    ],
)
def test_the_asset_url_is_found_wherever_it_sits(payload):
    assert HiggsfieldService.extract_url(payload) == "https://cdn.hf/a.png"


def test_a_video_url_is_preferred_when_several_are_present():
    payload = {"results": [{"url": "https://cdn.hf/thumb.png"}, {"url": "https://cdn.hf/clip.mp4"}]}
    assert HiggsfieldService.extract_url(payload, want="video") == "https://cdn.hf/clip.mp4"


def test_no_url_returns_none():
    assert HiggsfieldService.extract_url({"status": "queued"}) is None


@pytest.mark.parametrize(
    "stdout",
    [
        '{"url": "https://cdn.hf/a.png"}',
        'waiting for job...\nstill waiting\n{"url": "https://cdn.hf/a.png"}',
        'noise\n{"url": "https://cdn.hf/a.png"}\ntrailing noise',
    ],
)
def test_progress_lines_before_the_json_are_tolerated(stdout):
    """--wait prints progress while it polls, so the payload is not always line one."""
    payload = HiggsfieldService.parse_json(stdout)
    assert HiggsfieldService.extract_url(payload) == "https://cdn.hf/a.png"


def test_unparseable_output_is_none_not_an_exception():
    assert HiggsfieldService.parse_json("command not found") is None
    assert HiggsfieldService.parse_json("") is None


async def test_a_nonzero_exit_becomes_an_error_result(cli):
    cli(stdout="", returncode=1, stderr="model not available on this plan")
    result = await higgsfield_service.generate_image("a diver")
    assert "error" in result
    assert "model not available" in result["error"]


async def test_a_reply_with_no_url_is_an_error_not_a_silent_pass(cli):
    cli(stdout=json.dumps({"status": "queued"}))
    result = await higgsfield_service.generate_image("a diver")
    assert "error" in result


# --- availability ------------------------------------------------------------

async def test_the_service_is_unavailable_when_switched_off(monkeypatch):
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", False)
    assert await higgsfield_service.available() is False


async def test_the_service_is_unavailable_without_the_binary(monkeypatch):
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)
    monkeypatch.setattr(higgsfield_service, "_binary", "")
    assert await higgsfield_service.available() is False


# --- the pipeline prefers it, and falls back ---------------------------------

class _FakeScene:
    def __init__(self):
        import uuid

        self.id = uuid.uuid4()
        self.job_id = uuid.uuid4()
        self.image_prompt = "a diver in a kelp forest"
        self.image_model = None
        self.image_url = None
        self.local_image_path = None
        self.animation_status = "pending"
        self.reference_inputs = None
        self.bible_character = None
        self.bible_environment = None


class _FakeDb:
    async def execute(self, _stmt):
        return SimpleNamespace(scalar_one_or_none=lambda: _FakeDb.scene)

    async def commit(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False


@pytest.fixture
def scene_pipeline(monkeypatch, tmp_path):
    scene = _FakeScene()
    _FakeDb.scene = scene
    monkeypatch.setattr(production, "async_session_factory", lambda: _FakeDb())
    monkeypatch.setattr(production, "IMAGE_CACHE_DIR", tmp_path / "images")
    monkeypatch.setattr(production, "REFERENCE_CACHE_DIR", tmp_path / "refs")

    async def _no_bible(_db, _scene):
        return None

    async def _download(_url, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"\xff\xd8jpeg")
        return True

    monkeypatch.setattr(production, "_load_scene_bible", _no_bible)
    monkeypatch.setattr(production, "_download_image", _download)
    return scene


async def test_the_pipeline_uses_higgsfield_first(scene_pipeline, monkeypatch):
    async def _available():
        return True

    async def _generate(prompt, reference_paths=None, **_kw):
        return {
            "url": "https://cdn.hf/scene.png", "model": "seedream_v5_pro",
            "service": "higgsfield", "ref_count": 0, "character_consistent": False,
        }

    async def _must_not_run(*_a, **_kw):
        raise AssertionError("fell through to CometAPI while Higgsfield was working")

    monkeypatch.setattr(production.higgsfield_service, "available", _available)
    monkeypatch.setattr(production.higgsfield_service, "generate_image", _generate)
    monkeypatch.setattr(production.media_gen_service, "generate_image", _must_not_run)

    await production._generate_scene_image(str(scene_pipeline.id))

    assert scene_pipeline.image_url == "https://cdn.hf/scene.png"
    assert scene_pipeline.reference_inputs["service"] == "higgsfield"
    assert scene_pipeline.reference_inputs["model"] == "seedream_v5_pro"


async def test_the_pipeline_falls_back_to_cometapi_when_higgsfield_fails(
    scene_pipeline, monkeypatch
):
    async def _available():
        return True

    async def _fail(**_kw):
        return {"error": "higgsfield is down"}

    async def _comet(prompt, model=None, **_kw):
        return {"url": "https://cdn.comet/scene.jpg"}

    monkeypatch.setattr(production.higgsfield_service, "available", _available)
    monkeypatch.setattr(production.higgsfield_service, "generate_image", _fail)
    monkeypatch.setattr(production.media_gen_service, "generate_image", _comet)

    await production._generate_scene_image(str(scene_pipeline.id))

    assert scene_pipeline.image_url == "https://cdn.comet/scene.jpg"
    assert scene_pipeline.reference_inputs["service"] == "cometapi"


async def test_cometapi_runs_alone_when_higgsfield_is_unavailable(
    scene_pipeline, monkeypatch
):
    async def _unavailable():
        return False

    async def _must_not_run(**_kw):
        raise AssertionError("called Higgsfield while it was unavailable")

    async def _comet(prompt, model=None, **_kw):
        return {"url": "https://cdn.comet/scene.jpg"}

    monkeypatch.setattr(production.higgsfield_service, "available", _unavailable)
    monkeypatch.setattr(production.higgsfield_service, "generate_image", _must_not_run)
    monkeypatch.setattr(production.media_gen_service, "generate_image", _comet)

    await production._generate_scene_image(str(scene_pipeline.id))
    assert scene_pipeline.reference_inputs["service"] == "cometapi"


def test_the_configured_model_ids_are_higgsfield_style(backend_root):
    """
    Higgsfield ids use underscores (seedance_2_5). The CometAPI names
    (doubao-seedance-2-5) are a different vendor's and will be refused.
    """
    for value in (
        settings.HIGGSFIELD_IMAGE_MODEL,
        settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL,
        settings.HIGGSFIELD_VIDEO_MODEL,
    ):
        assert "-" not in value, f"{value} looks like a CometAPI id, not a Higgsfield one"
