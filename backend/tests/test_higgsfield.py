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
from app.services.higgsfield_service import (
    IMAGE_REFERENCE_FLAGS,
    HiggsfieldService,
    higgsfield_service,
)


@pytest.fixture
def cli(monkeypatch, tmp_path):
    """Stub the CLI subprocess; record the argv of every call."""
    calls = []

    def _install(stdout="", returncode=0, stderr=""):
        def _run(argv, **_kwargs):
            calls.append(list(argv))
            return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

        monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _run)
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
    assert IMAGE_REFERENCE_FLAGS[0] in argv
    assert reference in argv
    assert "--json" in argv and "--wait" in argv


async def test_no_reference_uses_the_plain_image_model(cli):
    calls = cli(stdout=json.dumps({"url": "https://cdn.hf/x.png"}))

    result = await higgsfield_service.generate_image("a kelp forest")

    assert result["character_consistent"] is False
    assert calls[0][3] == settings.HIGGSFIELD_IMAGE_MODEL
    assert not any(f in calls[0] for f in IMAGE_REFERENCE_FLAGS)


async def test_references_are_capped(cli, tmp_path):
    paths = []
    for i in range(5):
        p = tmp_path / f"r{i}.png"
        p.write_bytes(b"x")
        paths.append(str(p))
    calls = cli(stdout=json.dumps({"url": "https://cdn.hf/x.png"}))

    await higgsfield_service.generate_image("a diver", reference_paths=paths)
    assert calls[0].count(IMAGE_REFERENCE_FLAGS[0]) == settings.HIGGSFIELD_MAX_REFERENCES


async def test_a_missing_reference_file_is_dropped_not_sent(cli):
    calls = cli(stdout=json.dumps({"url": "https://cdn.hf/x.png"}))
    result = await higgsfield_service.generate_image("a diver", reference_paths=["/nope.png"])

    assert IMAGE_REFERENCE_FLAGS[0] not in calls[0]
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


# --- the media flag differs per model ----------------------------------------

async def test_a_rejected_media_flag_is_retried_with_the_next_name(monkeypatch, reference):
    """
    nano_banana_2 answers "Unknown params: image-references" even though the CLI's own
    help advertises that flag. Hardcoding one name breaks the moment a model declares a
    different one, so the service works through a candidate list and remembers the
    winner.
    """
    calls = []

    def _run(argv, **_kwargs):
        calls.append(list(argv))
        # Reject everything except the second candidate.
        if IMAGE_REFERENCE_FLAGS[1] in argv:
            return SimpleNamespace(returncode=0, stdout='{"url": "https://cdn.hf/x.png"}', stderr="")
        return SimpleNamespace(
            returncode=1, stdout="",
            stderr="Error: Unknown params: image\nHint: Run: higgsfield model get x",
        )

    monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _run)
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
    monkeypatch.setattr(higgsfield_service, "_authenticated", True)
    monkeypatch.setattr(higgsfield_service, "_media_flag", {})
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)

    result = await higgsfield_service.generate_image("a diver", reference_paths=[reference])

    assert result["url"] == "https://cdn.hf/x.png"
    assert len(calls) == 2, "should have stopped at the first flag that worked"
    # And it is remembered, so the next scene does not repeat the search.
    assert higgsfield_service._media_flag[settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL] == \
        IMAGE_REFERENCE_FLAGS[1]


async def test_a_real_failure_is_not_retried_as_a_flag_problem(monkeypatch, reference):
    """Only "Unknown params" means the flag was wrong. Everything else stops at once."""
    calls = []

    def _run(argv, **_kwargs):
        calls.append(list(argv))
        return SimpleNamespace(returncode=1, stdout="", stderr="Error: insufficient credits")

    monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _run)
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
    monkeypatch.setattr(higgsfield_service, "_authenticated", True)
    monkeypatch.setattr(higgsfield_service, "_media_flag", {})
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)

    result = await higgsfield_service.generate_image("a diver", reference_paths=[reference])

    assert "insufficient credits" in result["error"]
    assert len(calls) == 1, "retried a failure that had nothing to do with the flag name"


async def test_exhausting_every_flag_names_the_command_that_would_answer(
    monkeypatch, reference
):
    def _run(_argv, **_kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="Error: Unknown params: image")

    monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _run)
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
    monkeypatch.setattr(higgsfield_service, "_authenticated", True)
    monkeypatch.setattr(higgsfield_service, "_media_flag", {})
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)

    result = await higgsfield_service.generate_image("a diver", reference_paths=[reference])
    assert "higgsfield model get" in result["error"]


# --- the Windows event loop trap ---------------------------------------------

def test_the_cli_is_not_spawned_through_the_asyncio_subprocess_api(backend_root):
    """
    On Windows psycopg forces the Selector event loop, and asyncio subprocesses are
    not supported there — they raise NotImplementedError. The app needs the database
    and this CLI in the same loop, so the async subprocess API is unavailable to it.

    Using it made every Higgsfield call fail on Windows, and the failure surfaced as
    "not signed in" because is_authenticated could not tell the two apart. Blocking
    subprocess.run in a thread works on every loop, and is what assembly_service and
    qa_service already do.
    """
    import ast

    source = (backend_root / "app" / "services" / "higgsfield_service.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Walk the AST rather than grepping: the docstring explains the trap by name.
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "create_subprocess_exec" not in called
    assert "to_thread" in called


async def test_a_launch_failure_is_reported_as_itself_not_as_signed_out(monkeypatch):
    def _explode(*_a, **_kw):
        raise NotImplementedError("subprocess not supported on this event loop")

    monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _explode)
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
    monkeypatch.setattr(higgsfield_service, "_authenticated", None)
    monkeypatch.setattr(higgsfield_service, "_auth_error", "")
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)

    assert await higgsfield_service.is_authenticated() is False
    assert "NotImplementedError" in higgsfield_service.last_auth_error
    assert "not signed in" not in higgsfield_service.last_auth_error


async def test_a_genuinely_signed_out_cli_still_says_so(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        "app.services.higgsfield_service.subprocess.run",
        lambda *_a, **_kw: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
    monkeypatch.setattr(higgsfield_service, "_authenticated", None)
    monkeypatch.setattr(higgsfield_service, "_auth_error", "")

    assert await higgsfield_service.is_authenticated() is False
    assert higgsfield_service.last_auth_error == "no token stored"
