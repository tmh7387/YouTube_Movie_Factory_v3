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
    ARRAY_ELEMENT_SHAPES,
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
            # An array-style parameter uploads first; answer that leg with a media id
            # so the test exercises the generate call it is actually about.
            if "upload" in argv:
                return SimpleNamespace(
                    returncode=0, stdout=json.dumps({"id": "media-123"}), stderr=""
                )
            return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

        monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _run)
        monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
        monkeypatch.setattr(higgsfield_service, "_authenticated", True)
        monkeypatch.setattr(higgsfield_service, "_params", {})
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

    # The file is uploaded first, then referenced as a media OBJECT — input_images is an
    # array of objects. A bare path is refused ("should be array"), and so is a bare id
    # ("params.input_images.0: Input should be a valid object").
    upload_argv, generate_argv = calls[0], calls[-1]
    assert upload_argv[1:3] == ["upload", "create"]
    assert reference in upload_argv

    assert generate_argv[1:4] == ["generate", "create", settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL]
    flag = IMAGE_REFERENCE_FLAGS[0][0]
    sent = json.loads(generate_argv[generate_argv.index(flag) + 1])
    assert sent == [ARRAY_ELEMENT_SHAPES[0][2]({"id": "media-123", "url": ""})]
    assert isinstance(sent[0], dict), "elements must be objects, not bare ids"
    assert "--json" in generate_argv and "--wait" in generate_argv


async def test_no_reference_uses_the_plain_image_model(cli):
    calls = cli(stdout=json.dumps({"url": "https://cdn.hf/x.png"}))

    result = await higgsfield_service.generate_image("a kelp forest")

    assert result["character_consistent"] is False
    assert calls[0][3] == settings.HIGGSFIELD_IMAGE_MODEL
    assert not any(f in calls[0] for f, _ in IMAGE_REFERENCE_FLAGS)


async def test_references_are_capped(cli, tmp_path):
    paths = []
    for i in range(5):
        p = tmp_path / f"r{i}.png"
        p.write_bytes(b"x")
        paths.append(str(p))
    calls = cli(stdout=json.dumps({"url": "https://cdn.hf/x.png"}))

    await higgsfield_service.generate_image("a diver", reference_paths=paths)
    generate_argv = calls[-1]
    flag = IMAGE_REFERENCE_FLAGS[0][0]
    sent = json.loads(generate_argv[generate_argv.index(flag) + 1])
    assert len(sent) == settings.HIGGSFIELD_MAX_REFERENCES


async def test_a_missing_reference_file_is_dropped_not_sent(cli):
    calls = cli(stdout=json.dumps({"url": "https://cdn.hf/x.png"}))
    result = await higgsfield_service.generate_image("a diver", reference_paths=["/nope.png"])

    assert IMAGE_REFERENCE_FLAGS[0][0] not in calls[0]
    assert result["character_consistent"] is False


async def test_animation_sends_the_local_start_frame_and_duration(cli, reference):
    calls = cli(stdout=json.dumps({"url": "https://cdn.hf/clip.mp4"}))

    result = await higgsfield_service.animate_image(reference, prompt="slow dolly", duration=6)

    assert result["url"] == "https://cdn.hf/clip.mp4"
    # Not calls[0]: the model's parameter list is read first, to decide which
    # optional arguments this model will accept.
    argv = next(c for c in calls if "generate" in c)
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


# --- the still we sent in is never the clip we asked for ----------------------

def test_the_echoed_input_still_is_not_returned_as_the_video():
    """
    A --wait reply repeats the job record, so the picture we uploaded is in it with a
    perfectly good URL. Returning that made animation "succeed" by handing back its own
    input: a 256x256 PNG, zero seconds long, reported as a finished clip.
    """
    reply = {
        "params": {"medias": [{"url": "https://cdn.hf/user/in.png"}], "prompt": "dolly"},
        "results": [{"url": "https://cdn.hf/user/out.mp4"}],
    }
    assert HiggsfieldService.extract_url(reply, want="video") == "https://cdn.hf/user/out.mp4"


def test_a_still_is_rejected_rather_than_returned_when_no_clip_is_present():
    """
    Asked for a video, a .png is not a fallback — it is a wrong answer. None makes the
    caller report "no video URL in the reply", which is the truth and is actionable.
    """
    reply = {"params": {"medias": [{"url": "https://cdn.hf/user/in.png"}]}}
    assert HiggsfieldService.extract_url(reply, want="video") is None


def test_an_extensionless_url_still_counts_as_a_candidate():
    """Signed and extensionless URLs are common. Only the WRONG kind is dropped."""
    reply = {"results": [{"url": "https://cdn.hf/user/asset?token=abc"}]}
    assert HiggsfieldService.extract_url(reply, want="video") == "https://cdn.hf/user/asset?token=abc"


def test_the_request_echo_is_searched_when_nothing_else_carries_a_url():
    """Tolerance survives: skipping the echo must not blind the parser to a lone URL."""
    reply = {"params": {"output": {"url": "https://cdn.hf/user/out.mp4"}}}
    assert HiggsfieldService.extract_url(reply, want="video") == "https://cdn.hf/user/out.mp4"


async def test_animation_reports_an_error_when_only_the_input_still_comes_back(cli, reference):
    """The end-to-end shape of the bug: a pass that was really a failure."""
    cli(stdout=json.dumps({"params": {"medias": [{"url": "https://cdn.hf/in.png"}]}}))

    result = await higgsfield_service.animate_image(reference, prompt="dolly", duration=4)

    assert "error" in result, "returning the input still as the clip is a silent failure"
    assert "no video URL" in result["error"]


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

async def test_animation_sends_the_size_a_model_that_declares_it_requires(monkeypatch, reference):
    """
    seedance_2_5 answers "Missing required params: height, width" and says so only after
    a failed call. Its parameter list is read once and the size is sent.
    """
    calls = []

    def _run(argv, **_kwargs):
        calls.append(list(argv))
        if argv[1:3] == ["model", "get"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"params": {
                    "prompt": {}, "duration": {}, "medias": {}, "width": {}, "height": {},
                }}),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout='{"url": "https://cdn.hf/c.mp4"}', stderr="")

    monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _run)
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
    monkeypatch.setattr(higgsfield_service, "_authenticated", True)
    monkeypatch.setattr(higgsfield_service, "_media_flag", {})
    monkeypatch.setattr(higgsfield_service, "_params", {})
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)
    monkeypatch.setattr(settings, "HIGGSFIELD_VIDEO_WIDTH", 1280)
    monkeypatch.setattr(settings, "HIGGSFIELD_VIDEO_HEIGHT", 720)

    result = await higgsfield_service.animate_image(reference, prompt="slow dolly", duration=6)

    assert result["url"] == "https://cdn.hf/c.mp4"
    argv = [c for c in calls if "generate" in c][0]
    assert argv[argv.index("--width") + 1] == "1280"
    assert argv[argv.index("--height") + 1] == "720"

    # The parameter list is read once, not once per scene.
    await higgsfield_service.animate_image(reference, prompt="slow dolly", duration=6)
    assert sum(1 for c in calls if c[1:3] == ["model", "get"]) == 1


async def test_animation_withholds_size_from_a_model_that_declares_none(monkeypatch, reference):
    """
    The other half of the same rule. A model with no width parameter answers "Unknown
    params: width" — sending it unconditionally trades one failure for another.
    """
    calls = []

    def _run(argv, **_kwargs):
        calls.append(list(argv))
        if argv[1:3] == ["model", "get"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"params": [{"name": "prompt"}, {"name": "medias"}]}),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout='{"url": "https://cdn.hf/c.mp4"}', stderr="")

    monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _run)
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
    monkeypatch.setattr(higgsfield_service, "_authenticated", True)
    monkeypatch.setattr(higgsfield_service, "_media_flag", {})
    monkeypatch.setattr(higgsfield_service, "_params", {})
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)

    await higgsfield_service.animate_image(reference, prompt="slow dolly", duration=6)

    argv = [c for c in calls if "generate" in c][0]
    assert "--width" not in argv and "--height" not in argv
    assert "--duration" not in argv, "duration is not declared either"


async def test_an_unreadable_parameter_list_does_not_silence_the_arguments(monkeypatch, reference):
    """
    "We could not ask" must not be read as "this model has nothing". Failing to describe
    a model would otherwise strip every optional argument off every call it makes.
    """
    calls = []

    def _run(argv, **_kwargs):
        calls.append(list(argv))
        if argv[1:3] == ["model", "get"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="Error: service unavailable")
        return SimpleNamespace(returncode=0, stdout='{"url": "https://cdn.hf/c.mp4"}', stderr="")

    monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _run)
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
    monkeypatch.setattr(higgsfield_service, "_authenticated", True)
    monkeypatch.setattr(higgsfield_service, "_media_flag", {})
    monkeypatch.setattr(higgsfield_service, "_params", {})
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)

    await higgsfield_service.animate_image(reference, prompt="slow dolly", duration=6)

    argv = [c for c in calls if "generate" in c][0]
    assert "--width" in argv and "--duration" in argv
    # And the failed lookup is not cached as an answer.
    assert higgsfield_service._params == {}


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
        if "upload" in argv:
            return SimpleNamespace(returncode=0, stdout=json.dumps({"id": "media-123"}), stderr="")
        # Reject everything except the second candidate.
        if IMAGE_REFERENCE_FLAGS[1][0] in argv:
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
    generates = [c for c in calls if "generate" in c]
    # The first candidate is exhausted (one call per element shape), then the second
    # works and the search stops there — nothing is tried after it.
    assert IMAGE_REFERENCE_FLAGS[1][0] in generates[-1]
    assert sum(1 for c in generates if IMAGE_REFERENCE_FLAGS[1][0] in c) == 1
    assert not any(IMAGE_REFERENCE_FLAGS[2][0] in c for c in generates)
    # And it is remembered, so the next scene does not repeat the search.
    remembered = higgsfield_service._media_flag[settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL]
    assert remembered[:2] == IMAGE_REFERENCE_FLAGS[1]


async def test_a_rejected_element_shape_is_retried_with_the_next_shape(monkeypatch, reference):
    """
    The flag name being right is not enough. nano_banana_2 accepts `--input_images` and
    accepts an array, then rejects the elements: "params.input_images.0: Input should be
    a valid object". So the element shape is searched too, and the winner remembered.
    """
    wanted = ARRAY_ELEMENT_SHAPES[2]          # not the first one tried
    calls = []

    def _run(argv, **_kwargs):
        calls.append(list(argv))
        if "upload" in argv:
            return SimpleNamespace(
                returncode=0, stdout=json.dumps({"id": "media-123"}), stderr=""
            )
        flag = IMAGE_REFERENCE_FLAGS[0][0]
        if flag in argv:
            sent = json.loads(argv[argv.index(flag) + 1])
            if sent == [wanted[2]({"id": "media-123", "url": ""})]:
                return SimpleNamespace(
                    returncode=0, stdout='{"url": "https://cdn.hf/x.png"}', stderr=""
                )
        return SimpleNamespace(
            returncode=1, stdout="",
            stderr="Error: params.input_images.0: Input should be a valid object",
        )

    monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _run)
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
    monkeypatch.setattr(higgsfield_service, "_authenticated", True)
    monkeypatch.setattr(higgsfield_service, "_media_flag", {})
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)

    result = await higgsfield_service.generate_image("a diver", reference_paths=[reference])

    assert result["url"] == "https://cdn.hf/x.png"
    # The picture is uploaded once, not once per shape tried.
    assert sum(1 for c in calls if "upload" in c) == 1
    remembered = higgsfield_service._media_flag[settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL]
    assert remembered == (IMAGE_REFERENCE_FLAGS[0][0], "array", wanted[0])


async def test_the_reply_names_the_accepted_type_and_that_type_is_used(monkeypatch, reference):
    """
    A rejected enum lists what it does accept:

        Input should be 'media', 'headshot_job', 'soul_cast_job', 'wan2_7_job'

    That list is the answer. It is read out of the reply and tried, instead of guessing
    a sixth shape the model has already ruled out. Non-job kinds go first: an uploaded
    file is not the output of a job.
    """
    calls = []

    def _run(argv, **_kwargs):
        calls.append(list(argv))
        if "upload" in argv:
            return SimpleNamespace(
                returncode=0, stdout=json.dumps({"id": "media-123"}), stderr=""
            )
        flag = IMAGE_REFERENCE_FLAGS[0][0]
        if flag in argv:
            sent = json.loads(argv[argv.index(flag) + 1])
            if sent == [{"id": "media-123", "type": "media"}]:
                return SimpleNamespace(
                    returncode=0, stdout='{"url": "https://cdn.hf/x.png"}', stderr=""
                )
        return SimpleNamespace(
            returncode=1, stdout="",
            stderr=(
                "Error: input_images.0.type: Input should be 'headshot_job', "
                "'media', 'soul_cast_job', 'wan2_7_job'"
            ),
        )

    monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _run)
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
    monkeypatch.setattr(higgsfield_service, "_authenticated", True)
    monkeypatch.setattr(higgsfield_service, "_media_flag", {})
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)

    result = await higgsfield_service.generate_image("a diver", reference_paths=[reference])

    assert result["url"] == "https://cdn.hf/x.png"
    remembered = higgsfield_service._media_flag[settings.HIGGSFIELD_REFERENCE_IMAGE_MODEL]
    assert remembered[2] == "id+type=media"


def test_a_long_cli_reply_keeps_its_front_not_its_tail(monkeypatch, tmp_path):
    """
    The field that was wrong is named at the FRONT of a CLI reply, and the list of
    accepted values that follows can run for hundreds of characters. Keeping the tail
    threw the field name away and left an unreadable fragment.
    """
    monkeypatch.setattr(settings, "JOB_FILES_DIR", str(tmp_path))
    message = "input_images.0.type: Input should be " + ", ".join(
        f"'kind_{i}_job'" for i in range(300)
    )

    kept = HiggsfieldService._record(message)

    assert kept.startswith("input_images.0.type: Input should be")
    assert "full reply in" in kept, "a truncated reply must say where the whole one is"
    assert (tmp_path / "higgsfield_last_error.txt").read_text(encoding="utf-8") == message


def test_accepted_values_are_read_out_of_a_reply_with_plain_kinds_first():
    values = HiggsfieldService._types_from_reply(
        "input_images.0.type: Input should be 'headshot_job', 'media', 'soul_cast_job'"
    )
    assert values == ["media", "headshot_job", "soul_cast_job"]
    # No enum, nothing to read — the caller falls back to its own shape list.
    assert HiggsfieldService._types_from_reply("Error: insufficient credits") == []


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
    generates = [c for c in calls if "generate" in c]
    assert len(generates) == 1, "retried a failure that had nothing to do with the flag name"


async def test_exhausting_every_flag_names_the_command_that_would_answer(
    monkeypatch, reference
):
    def _run(argv, **_kwargs):
        if "upload" in argv:
            return SimpleNamespace(returncode=0, stdout=json.dumps({"id": "media-123"}), stderr="")
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


# --- the real parameter names, read off the account --------------------------

def test_the_leading_flags_match_what_the_models_actually_declare():
    """
    Taken from `higgsfield model get` against a live account:

      nano_banana_2 -> aspect_ratio, folder_id, input_images, prompt, resolution
      seedance_2_5  -> ..., duration, medias, mode, prompt, resolution, ...

    Neither declares image-references, which the CLI's own help advertises. The first
    candidate must be the one the model really takes, so the common path costs no
    wasted calls.
    """
    from app.services.higgsfield_service import START_IMAGE_FLAGS

    assert IMAGE_REFERENCE_FLAGS[0] == ("--input_images", "array")
    assert START_IMAGE_FLAGS[0] == ("--start-image", "repeat")
    # The discredited name is kept as a fallback, never as the first try.
    names = [flag for flag, _ in IMAGE_REFERENCE_FLAGS]
    assert "--image-references" in names
    assert names.index("--image-references") > 0


# --- array-typed parameters --------------------------------------------------

@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"id": "a"}, "a"),
        ({"media_id": "b"}, "b"),
        ({"data": {"id": "c"}}, "c"),
        ([{"upload_id": "d"}], "d"),
    ],
)
async def test_an_upload_reply_yields_a_media_id_whatever_the_key(
    monkeypatch, payload, expected
):
    monkeypatch.setattr(
        "app.services.higgsfield_service.subprocess.run",
        lambda *_a, **_kw: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr=""),
    )
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")

    result = await higgsfield_service.upload_media(__file__)
    assert result["id"] == expected


async def test_an_upload_reply_with_no_id_is_an_error(monkeypatch):
    monkeypatch.setattr(
        "app.services.higgsfield_service.subprocess.run",
        lambda *_a, **_kw: SimpleNamespace(
            returncode=0, stdout=json.dumps({"status": "queued"}), stderr=""
        ),
    )
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")

    result = await higgsfield_service.upload_media(__file__)
    assert "error" in result


async def test_a_wrong_value_type_moves_to_the_next_candidate(monkeypatch, reference):
    """
    "Invalid types: input_images should be array, got string" means the name was right
    and the shape was wrong. That is a candidate failure, not a hard stop — same as an
    unknown parameter name.
    """
    calls = []

    def _run(argv, **_kwargs):
        calls.append(list(argv))
        if "upload" in argv:
            return SimpleNamespace(returncode=0, stdout=json.dumps({"id": "m1"}), stderr="")
        if IMAGE_REFERENCE_FLAGS[1][0] in argv:
            return SimpleNamespace(returncode=0, stdout='{"url": "https://cdn.hf/x.png"}', stderr="")
        return SimpleNamespace(
            returncode=1, stdout="",
            stderr="Error: Invalid types: input_images should be array, got string",
        )

    monkeypatch.setattr("app.services.higgsfield_service.subprocess.run", _run)
    monkeypatch.setattr(higgsfield_service, "_binary", "higgsfield")
    monkeypatch.setattr(higgsfield_service, "_authenticated", True)
    monkeypatch.setattr(higgsfield_service, "_media_flag", {})
    monkeypatch.setattr(settings, "HIGGSFIELD_ENABLED", True)

    result = await higgsfield_service.generate_image("a diver", reference_paths=[reference])
    assert result["url"] == "https://cdn.hf/x.png"
