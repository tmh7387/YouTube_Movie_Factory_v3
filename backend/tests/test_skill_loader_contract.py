"""Every skill folder must be loadable.

`SkillLoaderService` looks for exactly `SKILL.md` under each entry in
`SKILL_ROOTS`. A folder without one is silently skipped — no error, no warning,
just one fewer skill injected into every generation prompt.

That is not hypothetical. Four folders were invisible for an unknown length of
time:

  * `seedance2-director-v2` held `SKILL (1).md`, a browser download whose ` (1)`
    was never removed. A model-selection fix was written into it and could never
    have reached a generation.
  * `higgsfield-creator` held only a `.skill` zip.
  * `music-video-producer` held `music-video-producer.md`.
  * `claude-movie-director` was a plugin manifest, not a skill at all.

These tests fail loudly on the same mistake.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL_ROOTS = [
    REPO / "skills" / "general",
    REPO / "skills" / "music_video",
    REPO / "skills" / "product_brand",
    REPO / "skills" / "asmr",
]

# Directory names under a skill root that are not skills.
NOT_SKILLS = {"__pycache__"}


def skill_dirs() -> list[Path]:
    out: list[Path] = []
    for root in SKILL_ROOTS:
        if not root.is_dir():
            continue
        out += [
            d for d in sorted(root.iterdir())
            if d.is_dir() and not d.name.startswith((".", "_")) and d.name not in NOT_SKILLS
        ]
    return out


def test_at_least_one_skill_is_discoverable():
    """Guards against the roots themselves moving or being renamed."""
    assert skill_dirs(), f"no skill folders found under any of {SKILL_ROOTS}"


@pytest.mark.parametrize("d", skill_dirs(), ids=lambda d: d.name)
def test_skill_folder_has_a_loadable_skill_md(d: Path):
    skill_md = d / "SKILL.md"
    if skill_md.is_file():
        return

    strays = sorted(p.name for p in d.iterdir() if p.is_file() and p.suffix in (".md", ".skill"))
    hint = ""
    near = [s for s in strays if s.lower().replace(" ", "") .startswith("skill")]
    if near:
        hint = f" Did you mean to rename {near[0]!r} to 'SKILL.md'?"
    elif any(s.endswith(".skill") for s in strays):
        hint = " This looks like a packaged .skill zip — unpack it into SKILL.md + references/."
    elif not strays:
        hint = " The folder holds no markdown at all — is it a skill?"
    else:
        hint = f" Files present: {', '.join(strays)}."

    pytest.fail(
        f"{d.relative_to(REPO)} has no SKILL.md, so SkillLoaderService cannot see it "
        f"and it is silently missing from every generation prompt.{hint}"
    )


@pytest.mark.parametrize("d", skill_dirs(), ids=lambda d: d.name)
def test_skill_md_has_name_and_description(d: Path):
    """Frontmatter drives auto-selection. Missing fields load, but never trigger."""
    skill_md = d / "SKILL.md"
    if not skill_md.is_file():
        pytest.skip("covered by test_skill_folder_has_a_loadable_skill_md")

    head = skill_md.read_text(encoding="utf-8", errors="ignore")[:4000]
    assert head.lstrip().startswith("---"), (
        f"{d.name}/SKILL.md does not open with YAML frontmatter"
    )
    for field in ("name:", "description:"):
        assert field in head, f"{d.name}/SKILL.md frontmatter is missing {field!r}"

MAX_DESCRIPTION = 1024


@pytest.mark.parametrize("d", skill_dirs(), ids=lambda d: d.name)
def test_description_fits_the_platform_limit(d: Path):
    """claude.ai rejects a skill whose description exceeds 1024 characters.

    The limit applies to the flattened value, not the wrapped source lines, so a
    folded block that looks short in the file can still be over.
    """
    skill_md = d / "SKILL.md"
    if not skill_md.is_file():
        pytest.skip("covered by test_skill_folder_has_a_loadable_skill_md")

    text = skill_md.read_text(encoding="utf-8", errors="ignore")
    if not text.lstrip().startswith("---"):
        pytest.skip("covered by test_skill_md_has_name_and_description")
    fm = text.split("---", 2)[1]

    folded = re.search(
        r"^description:[^\S\n]*(?:>-|>|\|-|\|)?[^\S\n]*\n((?:[^\S\n]+\S.*\n)+)",
        fm,
        re.M,
    )
    if folded:
        flat = " ".join(line.strip() for line in folded.group(1).strip().splitlines())
    else:
        m = re.search(r"^description:[^\S\n]*(\S.*)$", fm, re.M)
        if not m:
            pytest.skip("covered by test_skill_md_has_name_and_description")
        flat = m.group(1).strip()

    assert len(flat) <= MAX_DESCRIPTION, (
        f"{d.name}/SKILL.md description is {len(flat)} characters, over the "
        f"{MAX_DESCRIPTION} limit by {len(flat) - MAX_DESCRIPTION}. claude.ai will "
        f"reject the upload. Trim prose and duplicate trigger phrases — keep every "
        f"distinct trigger."
    )
