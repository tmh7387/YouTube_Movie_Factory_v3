"""
Item 6 acceptance — the dead imports, unreachable stubs and orphaned modules are gone,
and camera_specs actually reaches Claude.
"""
import json
from types import SimpleNamespace

import pytest

import tasks.production as production_tasks
from app.services import bible_service
from app.services.claude_service import claude_service


# --- 6.1 — suno_service was called without ever being imported ----------------

def test_production_tasks_have_no_music_generation_function():
    assert not hasattr(production_tasks, "_generate_music_track")


def test_production_tasks_do_not_reference_suno(backend_root):
    source = (backend_root / "tasks" / "production.py").read_text(encoding="utf-8")
    # The only permitted mention is the comment explaining why it is gone.
    code_lines = [
        line for line in source.splitlines()
        if "suno" in line.lower() and not line.lstrip().startswith("#")
    ]
    assert code_lines == []


# --- 6.2 — bible_service stub ------------------------------------------------

def test_bible_constraint_stub_is_removed():
    assert not hasattr(bible_service, "build_bible_constraint_block")


# --- 6.3 / 6.4 — deleted modules ---------------------------------------------

@pytest.mark.parametrize(
    "module_name",
    ["app.services.ytdlp_service", "app.services.inspiration_aggregator_service"],
)
def test_deleted_modules_are_actually_deleted(module_name):
    with pytest.raises(ModuleNotFoundError):
        __import__(module_name)


def test_no_501_aggregate_inspiration_route():
    from app.api import bible as bible_api

    paths = {getattr(r, "path", "") for r in bible_api.router.routes}
    assert "/aggregate-inspiration" not in paths


def test_no_notimplementederror_stubs_remain_in_services(backend_root):
    offenders = []
    for path in sorted((backend_root / "app" / "services").glob("*.py")):
        if "raise NotImplementedError" in path.read_text(encoding="utf-8"):
            offenders.append(path.name)
    assert offenders == []


# --- 6.5 — camera_specs must reach the system prompt -------------------------

class _CapturingAnthropicClient:
    """Minimal stand-in for AsyncAnthropic that records the system prompt."""

    def __init__(self, payload: dict):
        self.captured_system: str | None = None
        self._payload = payload
        self.messages = SimpleNamespace(create=self._create)

    async def _create(self, *, system, **_kwargs):
        self.captured_system = system
        return SimpleNamespace(
            content=[SimpleNamespace(text=json.dumps(self._payload))]
        )


async def test_camera_specs_render_into_the_bible_block(monkeypatch):
    fake = _CapturingAnthropicClient({"title": "T", "storyboard": []})
    monkeypatch.setattr(claude_service, "client", fake)

    bible = {
        "characters": [{"name": "The Diver", "physical": "tall", "wardrobe": "wetsuit"}],
        "environments": [{"name": "Kelp Forest", "description": "green", "lighting": "dappled"}],
        "style_lock": {"color_palette": ["#0af"], "visual_rules": ["shallow DOF"], "negative_prompt": "text"},
        "camera_specs": {
            "default_lens": "35mm anamorphic",
            "default_movement": "slow dolly",
            "lighting_setup": "natural + fill",
        },
    }

    await claude_service.generate_creative_brief("analysis", bible=bible)

    system = fake.captured_system
    assert system is not None
    assert "35mm anamorphic" in system
    assert "slow dolly" in system
    assert "natural + fill" in system


async def test_bible_block_without_camera_specs_does_not_crash(monkeypatch):
    fake = _CapturingAnthropicClient({"title": "T", "storyboard": []})
    monkeypatch.setattr(claude_service, "client", fake)

    await claude_service.generate_creative_brief(
        "analysis",
        bible={"characters": [], "environments": [], "style_lock": {}},
    )

    assert "Camera Specs" in fake.captured_system
    assert "Not specified" in fake.captured_system
