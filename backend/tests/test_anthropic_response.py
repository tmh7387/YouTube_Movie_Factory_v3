"""
Reading Claude's answer when the first block is not the answer.

A live run failed with:

    AttributeError: 'ThinkingBlock' object has no attribute 'text'

Every Claude call in this codebase did `response.content[0].text`. A model with
extended thinking puts a ThinkingBlock at index 0, so the creative brief, the bible,
the QA gate, video inspiration, skill synthesis and every analysis path would crash
on the configured model. Stubbed tests never saw it, because a stub returns whatever
shape the test author wrote — so these tests use the real block shapes.
"""
from types import SimpleNamespace

import pytest

from app.services.anthropic_response import (
    NoTextInResponse,
    response_text,
    strip_code_fences,
)


def _thinking(text="Let me consider the frame..."):
    """A ThinkingBlock exposes .thinking, never .text."""
    return SimpleNamespace(type="thinking", thinking=text, signature="sig")


def _redacted():
    return SimpleNamespace(type="redacted_thinking", data="encrypted")


def _text(value):
    return SimpleNamespace(type="text", text=value)


def _response(*blocks):
    return SimpleNamespace(content=list(blocks), model="claude-sonnet-5")


# --- the reported failure ----------------------------------------------------

def test_a_thinking_block_at_index_zero_no_longer_breaks_it():
    response = _response(_thinking(), _text('{"pass": true}'))
    assert response_text(response) == '{"pass": true}'


def test_index_zero_alone_would_have_raised():
    """Shows the old code path really was broken, so this test is not vacuous."""
    response = _response(_thinking(), _text("answer"))
    with pytest.raises(AttributeError):
        _ = response.content[0].text


def test_redacted_thinking_is_also_skipped():
    response = _response(_redacted(), _thinking(), _text("answer"))
    assert response_text(response) == "answer"


# --- ordinary shapes ---------------------------------------------------------

def test_a_plain_text_response_is_unchanged():
    assert response_text(_response(_text("hello"))) == "hello"


def test_several_text_blocks_are_joined():
    response = _response(_text('{"a": 1,'), _text(' "b": 2}'))
    assert response_text(response) == '{"a": 1, "b": 2}'


def test_a_block_carrying_text_but_an_odd_type_still_works():
    """An unfamiliar SDK shape should degrade, not fail."""
    response = _response(SimpleNamespace(type="output_text", text="answer"))
    assert response_text(response) == "answer"


# --- nothing usable ----------------------------------------------------------

def test_a_response_with_no_text_raises_a_clear_error():
    with pytest.raises(NoTextInResponse) as excinfo:
        response_text(_response(_thinking()))
    assert "thinking" in str(excinfo.value)


def test_an_empty_response_raises():
    with pytest.raises(NoTextInResponse):
        response_text(_response())


def test_a_response_with_no_content_attribute_raises():
    with pytest.raises(NoTextInResponse):
        response_text(SimpleNamespace())


# --- fence stripping ---------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ('{"a": 1}', '{"a": 1}'),
        ('```json\n{"a": 1}\n```', '{"a": 1}'),
        ('```\n{"a": 1}\n```', '{"a": 1}'),
        ('  ```json\n{"a": 1}\n```  ', '{"a": 1}'),
    ],
)
def test_code_fences_are_stripped(raw, expected):
    assert strip_code_fences(raw) == expected


# --- every caller uses the helper -------------------------------------------

def test_no_service_indexes_content_zero_any_more(backend_root):
    """
    The regression guard. Thirteen call sites had this bug; a fourteenth must not
    appear.
    """
    offenders = []
    for directory in ("app", "tasks"):
        for path in sorted((backend_root / directory).rglob("*.py")):
            if path.name == "anthropic_response.py":
                continue  # its docstring quotes the broken form on purpose
            if "content[0]" in path.read_text(encoding="utf-8"):
                offenders.append(str(path.relative_to(backend_root)))
    assert offenders == [], (
        "these files index the first content block directly, which breaks on any "
        "model that emits a thinking block: " + ", ".join(offenders)
    )


async def test_the_qa_gate_survives_a_thinking_block(monkeypatch, tmp_path):
    """End to end for the path the live run actually failed on."""
    import json

    from app.services.qa_service import qa_service

    verdict = {
        "pass": True, "character_match": 0.9, "style_match": 0.9,
        "prompt_adherence": 0.9, "artifacts": [], "notes": "clean",
    }

    class _Client:
        def __init__(self):
            self.messages = SimpleNamespace(create=self._create)

        async def _create(self, **_kwargs):
            return _response(_thinking(), _text(json.dumps(verdict)))

    monkeypatch.setattr(qa_service, "_client", _Client())

    frame = tmp_path / "frame.jpg"
    frame.write_bytes(b"\xff\xd8jpeg")

    result = await qa_service._ask_claude(frame, "review this")
    assert result == verdict


async def test_the_creative_brief_survives_a_thinking_block(monkeypatch):
    import json

    from app.services.claude_service import claude_service

    brief = {"title": "T", "storyboard": []}

    class _Client:
        def __init__(self):
            self.messages = SimpleNamespace(create=self._create)

        async def _create(self, **_kwargs):
            return _response(_thinking(), _text(json.dumps(brief)))

    monkeypatch.setattr(claude_service, "client", _Client())

    result = await claude_service.generate_creative_brief("analysis")
    assert result == brief
