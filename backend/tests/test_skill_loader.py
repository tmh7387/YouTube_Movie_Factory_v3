"""
Item 1 acceptance — the disk skill loader must actually reach skills/ on disk.

Before this pass AGENT_SKILLS_ROOT pointed at <repo>/.agent/skills, which does not
exist, so every disk-skill lookup returned None and build_prompt_block() emitted a
DB-only block that is empty on a fresh database.
"""
import pytest

from app.services.skill_loader_service import (
    AGENT_SKILLS_ROOT,
    CONTEXT_SKILL_MAP,
    MODEL_SKILL_MAP,
    SkillLoaderService,
)


def _all_mapped_slugs() -> list[str]:
    slugs: set[str] = set()
    for mapped in MODEL_SKILL_MAP.values():
        slugs.update(mapped)
    for mapped in CONTEXT_SKILL_MAP.values():
        slugs.update(mapped)
    return sorted(slugs)


def test_skills_root_exists_and_is_the_repo_skills_dir():
    assert AGENT_SKILLS_ROOT.name == "skills"
    assert AGENT_SKILLS_ROOT.is_dir(), f"{AGENT_SKILLS_ROOT} does not exist"


def test_mapped_slug_count_is_nine():
    # Guards against a slug being silently dropped from the maps.
    assert len(_all_mapped_slugs()) == 9


@pytest.mark.parametrize("slug", _all_mapped_slugs())
def test_every_mapped_slug_resolves_to_a_readable_skill_file(slug):
    path = SkillLoaderService.resolve_skill_path(slug)
    assert path is not None, f"slug '{slug}' does not resolve to any SKILL.md"
    assert path.is_file()
    assert path.read_text(encoding="utf-8").strip(), f"{path} is empty"


@pytest.mark.parametrize("slug", _all_mapped_slugs())
def test_every_mapped_slug_parses_into_a_skill_dict(slug):
    skill = SkillLoaderService().load_disk_skill(slug)
    assert skill is not None, f"slug '{slug}' failed to parse"
    assert skill["source"] == "disk"
    assert skill["body"].strip()


def test_versioned_directory_resolves_via_prefix_glob():
    """seedance2-director lives in seedance2-director-v2/ — pass 3 must find it."""
    path = SkillLoaderService.resolve_skill_path("seedance2-director")
    assert path is not None
    assert path.parent.name == "seedance2-director-v2"


def test_unknown_slug_resolves_to_none():
    assert SkillLoaderService.resolve_skill_path("no-such-skill-anywhere") is None
    assert SkillLoaderService().load_disk_skill("no-such-skill-anywhere") is None


async def test_seedance_prompt_block_carries_native_camera_controls():
    """
    Acceptance: a Seedance animation model must pull the Seedance camera-control
    section into the injected block, with no DB rows available.
    """
    block = await SkillLoaderService().build_prompt_block(
        animation_model="doubao-seedance-2-0",
    )
    assert "SEEDANCE NATIVE CAMERA CONTROLS" in block


def test_compact_block_is_empty_for_no_skills():
    assert SkillLoaderService().build_compact_block([]) == ""
