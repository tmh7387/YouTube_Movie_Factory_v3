"""
Job 2 — the vendor call shapes, pinned.

These assert on the request we build and how we read the response, not on any live
service. Each one corresponds to a defect that only ever surfaces as an HTTP 400 or a
crash against the real API, which is exactly the class of bug the stubbed smoke gate
cannot see.
"""
import json

import httpx
import pytest

from app.core.config import settings
from app.services.gpt_image_service import MAX_REFERENCES, gpt_image_service
from app.services.media_gen_service import media_gen_service


def _multipart_fields(request: httpx.Request) -> list[tuple[str, str]]:
    """(name, value-or-filename) for each part of a multipart body, in order."""
    body = request.content.decode("latin-1")
    fields = []
    for chunk in body.split("--")[1:]:
        if 'name="' not in chunk:
            continue
        name = chunk.split('name="', 1)[1].split('"', 1)[0]
        if 'filename="' in chunk:
            value = chunk.split('filename="', 1)[1].split('"', 1)[0]
        else:
            value = chunk.split("\r\n\r\n", 1)[-1].rsplit("\r\n", 1)[0]
        fields.append((name, value))
    return fields


@pytest.fixture
def openai_capture(monkeypatch):
    """Capture the request gpt_image_service builds; return a canned success."""
    captured = {}

    async def _handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        captured.setdefault("urls", []).append(str(request.url))
        return httpx.Response(200, json={"data": [{"b64_json": "ZmFrZQ=="}]})

    transport = httpx.MockTransport(_handler)
    real_client = httpx.AsyncClient

    def _client(*_args, **kwargs):
        kwargs["transport"] = transport
        return real_client(**kwargs)

    monkeypatch.setattr("app.services.gpt_image_service.httpx.AsyncClient", _client)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    return captured


@pytest.fixture
def reference_files(tmp_path):
    paths = []
    for i in range(4):
        p = tmp_path / f"ref{i}.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n reference bytes")
        paths.append(str(p))
    return paths


# --- defect 1: response_format is rejected by gpt-image models ---------------

async def test_generation_does_not_send_response_format(openai_capture):
    """
    gpt-image models reject response_format with
    {"error": {"message": "Unknown parameter: 'response_format'."}} — a hard 400.
    They return base64 regardless.
    """
    result = await gpt_image_service.generate_image("a diver")
    assert "error" not in result, result

    payload = json.loads(openai_capture["request"].content)
    assert "response_format" not in payload
    assert payload["model"] == settings.OPENAI_IMAGE_MODEL


async def test_reference_generation_does_not_send_response_format(
    openai_capture, reference_files
):
    await gpt_image_service.generate_with_character(
        prompt="a diver", character_description="tall", reference_image_paths=reference_files[:1]
    )
    names = [name for name, _ in _multipart_fields(openai_capture["request"])]
    assert "response_format" not in names


# --- defect 2: multiple references need a repeated image[] field -------------

async def test_every_reference_is_sent_as_its_own_image_field(
    openai_capture, reference_files
):
    """
    The edits endpoint reads an array of images from repeated `image[]` parts. Naming
    them image[], image[1], image[2] sends three different fields and silently drops
    two of the three references.
    """
    await gpt_image_service.generate_with_character(
        prompt="a diver",
        character_description="tall",
        reference_image_paths=reference_files[:3],
    )

    fields = _multipart_fields(openai_capture["request"])
    image_fields = [(name, value) for name, value in fields if name.startswith("image")]

    assert [name for name, _ in image_fields] == ["image[]"] * 3
    assert [value for _, value in image_fields] == ["ref0.png", "ref1.png", "ref2.png"]


async def test_references_are_capped(openai_capture, reference_files):
    await gpt_image_service.generate_with_character(
        prompt="a diver", character_description="", reference_image_paths=reference_files
    )
    fields = _multipart_fields(openai_capture["request"])
    assert len([n for n, _ in fields if n == "image[]"]) == MAX_REFERENCES


async def test_missing_reference_files_fall_back_to_plain_generation(openai_capture):
    result = await gpt_image_service.generate_with_character(
        prompt="a diver", character_description="", reference_image_paths=["/nope/missing.png"]
    )
    assert "error" not in result
    assert openai_capture["urls"] == ["https://api.openai.com/v1/images/generations"]


async def test_an_empty_character_description_is_not_appended(openai_capture, reference_files):
    await gpt_image_service.generate_with_character(
        prompt="a diver", character_description="  ", reference_image_paths=reference_files[:1]
    )
    prompt = dict(_multipart_fields(openai_capture["request"]))["prompt"]
    assert prompt == "a diver"
    assert "maintain exactly" not in prompt


# --- defect 3: responses were indexed blindly -------------------------------

@pytest.mark.parametrize(
    "body",
    [{}, {"data": []}, {"data": [{}]}, {"data": "not a list"}],
)
async def test_a_malformed_openai_response_is_an_error_not_a_crash(monkeypatch, body):
    async def _handler(_request):
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(_handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        "app.services.gpt_image_service.httpx.AsyncClient",
        lambda *_a, **kw: real_client(**{**kw, "transport": transport}),
    )
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")

    result = await gpt_image_service.generate_image("a diver")
    assert "error" in result


@pytest.mark.parametrize(
    "body",
    [{}, {"data": []}, {"data": [{}]}, {"data": [{"revised_prompt": "x"}]}],
)
async def test_a_malformed_cometapi_image_response_is_an_error_not_a_crash(monkeypatch, body):
    """
    generate_image's contract is "return {'error': ...} on failure". Indexing
    data["data"][0]["url"] broke that contract with a KeyError that propagated into
    the pipeline instead of failing the one scene.
    """
    async def _handler(_request):
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(_handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        "app.services.media_gen_service.httpx.AsyncClient",
        lambda *_a, **kw: real_client(**{**kw, "transport": transport}),
    )

    result = await media_gen_service.generate_image("a diver")
    assert "error" in result, result


async def test_a_well_formed_cometapi_response_still_works(monkeypatch):
    async def _handler(_request):
        return httpx.Response(200, json={"data": [{"url": "https://cdn/x.jpg", "revised_prompt": "r"}]})

    transport = httpx.MockTransport(_handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        "app.services.media_gen_service.httpx.AsyncClient",
        lambda *_a, **kw: real_client(**{**kw, "transport": transport}),
    )

    result = await media_gen_service.generate_image("a diver")
    assert result["url"] == "https://cdn/x.jpg"
    assert result["revised_prompt"] == "r"


# --- the dependency that was never declared ---------------------------------

def test_supabase_is_a_declared_dependency(backend_root):
    """
    supabase_storage_service imports `supabase` lazily inside _get_client, so a missing
    package showed up as a request-time ModuleNotFoundError on the first audio or
    reference-sheet upload rather than at import.
    """
    requirements = (backend_root / "requirements.txt").read_text()
    assert "supabase" in requirements
