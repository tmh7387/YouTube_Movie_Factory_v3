"""
Item 2 acceptance — bible reference images must reach the generator.

Before this pass no user-supplied or bible-supplied image reached any generator:
media_gen_service.generate_image() takes (prompt, model, size) and cannot accept a
reference, and gpt_image_service.generate_with_character() — which posts real image
bytes to OpenAI /images/edits — had zero importers.
"""
import uuid
from types import SimpleNamespace

import pytest

import tasks.production as production
from app.services.intake_normalizer import normalize_to_research_context


# --- fakes -------------------------------------------------------------------

class _FakeScene:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.job_id = kwargs.get("job_id", uuid.uuid4())
        self.image_prompt = kwargs.get("image_prompt", "a diver in a kelp forest")
        self.image_model = None
        self.image_url = None
        self.local_image_path = None
        self.animation_status = "pending"
        self.reference_inputs = None
        self.bible_character = kwargs.get("bible_character")
        self.bible_environment = kwargs.get("bible_environment")


class _FakeBible:
    def __init__(self, characters=None, environments=None, char_sheets=None, env_sheets=None):
        self.characters = characters or []
        self.environments = environments or []
        self.character_sheet_urls = char_sheets or []
        self.environment_sheet_urls = env_sheets or []


class _FakeDb:
    def __init__(self, scene):
        self._scene = scene
        self.commits = 0

    async def execute(self, _stmt):
        scene = self._scene
        return SimpleNamespace(scalar_one_or_none=lambda: scene)

    async def commit(self):
        self.commits += 1

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False


@pytest.fixture
def wire_scene(monkeypatch):
    """Point tasks.production at an in-memory scene and neutralise the network."""

    def _wire(scene, bible):
        monkeypatch.setattr(production, "async_session_factory", lambda: _FakeDb(scene))

        async def _load_bible(_db, _scene):
            return bible

        monkeypatch.setattr(production, "_load_scene_bible", _load_bible)

        async def _download(_url, dest):
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"\x89PNG\r\n\x1a\n fake reference bytes")
            return True

        monkeypatch.setattr(production, "_download_image", _download)

    return _wire


# --- acceptance --------------------------------------------------------------

async def test_scene_with_matching_character_uses_reference_generation(
    wire_scene, monkeypatch, tmp_path
):
    monkeypatch.setattr(production, "REFERENCE_CACHE_DIR", tmp_path / "refs")
    monkeypatch.setattr(production, "IMAGE_CACHE_DIR", tmp_path / "images")
    monkeypatch.setattr(production.settings, "OPENAI_API_KEY", "test-openai-key")

    scene = _FakeScene(bible_character="The Diver")
    bible = _FakeBible(
        characters=[{
            "name": "The Diver",
            "physical": "tall, weathered, close-cropped grey hair",
            "wardrobe": "patched navy wetsuit",
            "ref_sheet_url": "https://example.test/diver-sheet.png",
        }],
    )
    wire_scene(scene, bible)

    calls = {}

    async def _generate_with_character(*, prompt, character_description, reference_image_paths, **_kw):
        calls["prompt"] = prompt
        calls["character_description"] = character_description
        calls["reference_image_paths"] = list(reference_image_paths)
        return {"b64_json": "ZmFrZQ==", "character_consistent": True}

    async def _save(b64_json, output_path):
        calls["saved_b64"] = b64_json
        return output_path

    async def _must_not_run(*_a, **_kw):
        raise AssertionError("media_gen_service.generate_image must not be called")

    monkeypatch.setattr(production.gpt_image_service, "generate_with_character", _generate_with_character)
    monkeypatch.setattr(production.gpt_image_service, "save_b64_to_file", _save)
    monkeypatch.setattr(production.media_gen_service, "generate_image", _must_not_run)

    await production._generate_scene_image(str(scene.id))

    expected_ref = tmp_path / "refs" / f"{scene.id}_ref0.png"
    assert calls["reference_image_paths"] == [str(expected_ref)]
    assert calls["prompt"] == scene.image_prompt
    assert "patched navy wetsuit" in calls["character_description"]
    assert "close-cropped grey hair" in calls["character_description"]

    assert scene.reference_inputs == {
        "mode": "reference",
        "refs": ["https://example.test/diver-sheet.png"],
        "service": "gpt_image_2",
    }
    assert scene.local_image_path == str(tmp_path / "images" / f"{scene.id}.jpg")
    assert scene.image_url is None


async def test_scene_with_no_bible_falls_back_to_text_generation(
    wire_scene, monkeypatch, tmp_path
):
    monkeypatch.setattr(production, "REFERENCE_CACHE_DIR", tmp_path / "refs")
    monkeypatch.setattr(production, "IMAGE_CACHE_DIR", tmp_path / "images")
    monkeypatch.setattr(production.settings, "OPENAI_API_KEY", "test-openai-key")

    scene = _FakeScene()
    wire_scene(scene, None)

    async def _must_not_run(*_a, **_kw):
        raise AssertionError("gpt_image_service must not be touched without references")

    async def _generate_image(prompt, model=None, **_kw):
        return {"url": "https://cdn.test/generated.jpg", "model": model}

    monkeypatch.setattr(production.gpt_image_service, "generate_with_character", _must_not_run)
    monkeypatch.setattr(production.gpt_image_service, "save_b64_to_file", _must_not_run)
    monkeypatch.setattr(production.media_gen_service, "generate_image", _generate_image)

    await production._generate_scene_image(str(scene.id))

    assert scene.image_url == "https://cdn.test/generated.jpg"
    assert scene.reference_inputs == {"mode": "text", "refs": [], "service": "cometapi"}


async def test_references_are_ignored_without_an_openai_key(wire_scene, monkeypatch, tmp_path):
    monkeypatch.setattr(production, "REFERENCE_CACHE_DIR", tmp_path / "refs")
    monkeypatch.setattr(production, "IMAGE_CACHE_DIR", tmp_path / "images")
    monkeypatch.setattr(production.settings, "OPENAI_API_KEY", "")

    scene = _FakeScene(bible_character="The Diver")
    bible = _FakeBible(characters=[{"name": "The Diver", "ref_sheet_url": "https://example.test/d.png"}])
    wire_scene(scene, bible)

    async def _must_not_run(*_a, **_kw):
        raise AssertionError("gpt_image_service must not be called without an API key")

    async def _generate_image(prompt, model=None, **_kw):
        return {"url": "https://cdn.test/generated.jpg"}

    monkeypatch.setattr(production.gpt_image_service, "generate_with_character", _must_not_run)
    monkeypatch.setattr(production.media_gen_service, "generate_image", _generate_image)

    await production._generate_scene_image(str(scene.id))
    assert scene.reference_inputs["mode"] == "text"


async def test_reference_failure_falls_back_and_records_text_mode(
    wire_scene, monkeypatch, tmp_path
):
    monkeypatch.setattr(production, "REFERENCE_CACHE_DIR", tmp_path / "refs")
    monkeypatch.setattr(production, "IMAGE_CACHE_DIR", tmp_path / "images")
    monkeypatch.setattr(production.settings, "OPENAI_API_KEY", "test-openai-key")

    scene = _FakeScene(bible_character="The Diver")
    bible = _FakeBible(characters=[{"name": "The Diver", "ref_sheet_url": "https://example.test/d.png"}])
    wire_scene(scene, bible)

    async def _fail(**_kw):
        return {"error": "OpenAI is down"}

    async def _generate_image(prompt, model=None, **_kw):
        return {"url": "https://cdn.test/fallback.jpg"}

    monkeypatch.setattr(production.gpt_image_service, "generate_with_character", _fail)
    monkeypatch.setattr(production.media_gen_service, "generate_image", _generate_image)

    await production._generate_scene_image(str(scene.id))

    assert scene.reference_inputs == {"mode": "text", "refs": [], "service": "cometapi"}
    assert scene.image_url == "https://cdn.test/fallback.jpg"


# --- reference resolution ----------------------------------------------------

def test_environment_reference_follows_the_character_reference():
    scene = _FakeScene(bible_character="The Diver", bible_environment="Kelp Forest")
    bible = _FakeBible(
        characters=[{"name": "The Diver", "ref_sheet_url": "char.png"}],
        environments=[{"name": "Kelp Forest", "ref_sheet_url": "env.png"}],
    )
    urls, character = production._collect_reference_urls(bible, scene)
    assert urls == ["char.png", "env.png"]
    assert character["name"] == "The Diver"


def test_bible_level_sheets_are_the_fallback_when_an_entity_has_none():
    scene = _FakeScene(bible_character="The Diver", bible_environment="Kelp Forest")
    bible = _FakeBible(
        characters=[{"name": "The Diver"}],
        environments=[{"name": "Kelp Forest"}],
        char_sheets=["fallback-char.png"],
        env_sheets=["fallback-env.png"],
    )
    urls, _ = production._collect_reference_urls(bible, scene)
    assert urls == ["fallback-char.png", "fallback-env.png"]


def test_reference_count_is_capped_at_three():
    scene = _FakeScene(bible_character="X")
    bible = _FakeBible(
        characters=[{"name": "X"}],
        char_sheets=[f"c{i}.png" for i in range(6)],
    )
    urls, _ = production._collect_reference_urls(bible, scene)
    assert len(urls) == production.MAX_SCENE_REFERENCES


def test_no_bible_yields_no_references():
    assert production._collect_reference_urls(None, _FakeScene()) == ([], None)


@pytest.mark.parametrize(
    "tag, expected",
    [
        ("The Diver", True),
        ("the diver", True),
        ("The Diver (close-up)", True),
        ("The Elder", False),
    ],
)
def test_character_matching_tolerates_case_and_qualifiers(tag, expected):
    entries = [{"name": "The Diver"}]
    assert (production._match_bible_entry(entries, tag) is not None) is expected


# --- 2.6 Image Board key alignment -------------------------------------------

async def test_image_board_urls_reach_the_research_context():
    context = await normalize_to_research_context(
        source_type="image_board",
        source_data={"image_urls": ["https://x.test/a.png", "https://x.test/b.png"], "notes": "moody"},
        topic="reference board",
    )
    assert context["image_urls"] == ["https://x.test/a.png", "https://x.test/b.png"]
    # Setting image_urls alone drops them — nothing downstream reads that key.
    assert "https://x.test/a.png" in context["text_content"]
    assert "moody" in context["text_content"]


async def test_image_board_still_accepts_the_legacy_urls_key():
    context = await normalize_to_research_context(
        source_type="image_board",
        source_data={"urls": ["https://x.test/legacy.png"]},
        topic="reference board",
    )
    assert context["image_urls"] == ["https://x.test/legacy.png"]
    assert "legacy.png" in context["text_content"]


def test_frontend_posts_the_key_the_normalizer_reads(repo_root):
    source = (repo_root / "frontend" / "src" / "components" / "ResearchIntake.tsx").read_text()
    assert "sourceData.image_urls = urls" in source
    assert "sourceData.urls = urls" not in source
