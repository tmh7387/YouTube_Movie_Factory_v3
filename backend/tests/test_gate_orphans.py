"""
Gate 8.2 — orphan detector.

Every module under backend/app/services/ must have at least one importer outside
itself, unless it is on ALLOWED_ORPHANS. Each allowlisted module must carry a
docstring that says, in so many words, that it is staged and unwired — so the
allowlist can never quietly become a dumping ground.

This is the check that would have caught the six services that shipped green and
were reachable from nothing.
"""
import ast
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = BACKEND_ROOT / "app" / "services"

# Modules deliberately not wired in this pass. Keep this short. Every entry must
# state in its module docstring why it is staged — test_allowed_orphans_are_documented
# enforces that, and the entry must be deleted the moment the module is wired.
ALLOWED_ORPHANS = {
    "stem_service",     # demucs + torch + GPU; STEM_SEPARATION_ENABLED defaults False
    "upscale_service",  # realesrgan native binary; UPSCALING_ENABLED defaults False
    "suno_service",     # music is user-upload-only today; num_tracks is hardcoded 0
}

_STAGED_MARKER = "STAGED — DELIBERATELY UNWIRED"


def _service_modules() -> list[str]:
    return sorted(
        path.stem
        for path in SERVICES_DIR.glob("*.py")
        if path.stem != "__init__"
    )


def _importers(module_name: str) -> set[str]:
    """Files that import app.services.<module_name>, excluding the module itself."""
    dotted = f"app.services.{module_name}"
    found: set[str] = set()

    for path in sorted(BACKEND_ROOT.rglob("*.py")):
        if path == SERVICES_DIR / f"{module_name}.py":
            continue
        if ".venv" in path.parts or "alembic" in path.parts:
            continue

        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == dotted:
                found.add(str(path.relative_to(BACKEND_ROOT)))
            elif isinstance(node, ast.Import):
                if any(alias.name == dotted for alias in node.names):
                    found.add(str(path.relative_to(BACKEND_ROOT)))
            elif isinstance(node, ast.ImportFrom) and node.module == "app.services":
                if any(alias.name == module_name for alias in node.names):
                    found.add(str(path.relative_to(BACKEND_ROOT)))

    return found


def test_no_unexpected_orphan_services():
    orphans = {name for name in _service_modules() if not _importers(name)}
    unexpected = sorted(orphans - ALLOWED_ORPHANS)
    assert unexpected == [], (
        "services with zero importers and no allowlist entry: " + ", ".join(unexpected)
    )


def test_allowlist_has_no_stale_entries():
    """An allowlisted module that has since been wired must leave the allowlist."""
    stale = sorted(name for name in ALLOWED_ORPHANS if _importers(name))
    assert stale == [], (
        "these modules now have importers and must be removed from ALLOWED_ORPHANS: "
        + ", ".join(stale)
    )


def test_allowlist_entries_all_exist():
    missing = sorted(ALLOWED_ORPHANS - set(_service_modules()))
    assert missing == [], "ALLOWED_ORPHANS names a module that does not exist: " + ", ".join(missing)


def test_allowed_orphans_are_documented():
    undocumented = []
    for name in sorted(ALLOWED_ORPHANS):
        source = (SERVICES_DIR / f"{name}.py").read_text(encoding="utf-8")
        docstring = ast.get_docstring(ast.parse(source)) or ""
        if _STAGED_MARKER not in docstring:
            undocumented.append(name)
    assert undocumented == [], (
        f"allowlisted modules whose docstring lacks '{_STAGED_MARKER}': "
        + ", ".join(undocumented)
    )
