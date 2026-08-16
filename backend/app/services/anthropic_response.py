"""
Reading the answer out of an Anthropic response.

`response.content[0]` is not the answer. It is the first block, and a model with
extended thinking enabled puts a ThinkingBlock there — so `response.content[0].text`
raises:

    AttributeError: 'ThinkingBlock' object has no attribute 'text'

Every Claude call in this codebase indexed [0] directly, which meant the creative
brief, the pre-production bible, the QA gate, video inspiration, skill synthesis and
the intake analysis would all crash the moment a thinking-capable model was
configured. The failure is silent in tests, because a stubbed client returns whatever
shape the test author wrote.

Use response_text() instead of indexing.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class NoTextInResponse(RuntimeError):
    """The model replied, but with no text block — nothing usable to parse."""


def response_text(response: Any) -> str:
    """
    Return the model's text, ignoring thinking and other non-text blocks.

    Joins every text block rather than taking the first, since a long answer can be
    split across several. Raises NoTextInResponse when there is no text at all, which
    every caller already turns into an {"error": ...} result.
    """
    blocks = getattr(response, "content", None) or []

    texts = [
        block.text
        for block in blocks
        if getattr(block, "type", None) == "text" and isinstance(getattr(block, "text", None), str)
    ]
    if not texts:
        # Belt and braces: honour any block exposing .text even if it is not typed
        # "text", so an unfamiliar SDK shape degrades rather than fails.
        texts = [
            block.text for block in blocks if isinstance(getattr(block, "text", None), str)
        ]

    if not texts:
        kinds = [getattr(block, "type", type(block).__name__) for block in blocks]
        raise NoTextInResponse(
            f"Anthropic response carried no text block (blocks: {kinds or 'none'})"
        )

    return "".join(texts)


def strip_code_fences(raw: str) -> str:
    """
    Remove a leading ```json fence, if the model wrapped its JSON in one.

    Six services carried their own copy of this. They are now one function.
    """
    text = raw.strip()
    if not text.startswith("```"):
        return text
    parts = text.split("```", 2)
    if len(parts) < 2:
        return text
    body = parts[1]
    if body.startswith("json"):
        body = body[4:]
    return body.rsplit("```", 1)[0].strip()
