"""
Gate 8.1 — import resolution.

Every `from app.X import Y` and `from tasks.X import Y` in the backend must name
something that module actually defines. This is a pure AST walk: no third-party
package is imported, so the gate runs anywhere Python does.

This is the check that would have caught `run_briefing_pipeline` — an import of a
name that had been deleted from tasks/curation.py, which only blew up at request
time on the one endpoint that used it.
"""
import ast
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parent.parent
FIRST_PARTY_ROOTS = ("app", "tasks")
SCAN_DIRS = ("app", "tasks", "tests")


def _python_files() -> list[Path]:
    files: list[Path] = []
    for directory in SCAN_DIRS:
        files.extend(sorted((BACKEND_ROOT / directory).rglob("*.py")))
    return files


def _module_to_path(module: str) -> Path | None:
    """
    Map a dotted first-party module name to its file on disk.

    `app.api`, `app.services` and friends have no __init__.py — they are implicit
    namespace packages — so a bare directory counts as resolved.
    """
    rel = Path(*module.split("."))
    for candidate in (BACKEND_ROOT / rel.with_suffix(".py"), BACKEND_ROOT / rel / "__init__.py"):
        if candidate.is_file():
            return candidate
    directory = BACKEND_ROOT / rel
    if directory.is_dir():
        return directory
    return None


def _defined_names(path: Path) -> set[str]:
    """Top-level names a module exposes: defs, classes, assignments and its own imports."""
    if path.is_dir():
        # Namespace package — exports nothing directly; only submodules resolve.
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == "*":
                    # A star import can supply anything; treat the module as open.
                    names.add("*")
                else:
                    names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.Try):
            # Guarded imports / definitions — walk one level deeper.
            for sub in node.body:
                if isinstance(sub, (ast.Import, ast.ImportFrom)):
                    for alias in sub.names:
                        names.add(alias.asname or alias.name.split(".")[0])
    return names


def _is_first_party(module: str | None) -> bool:
    return bool(module) and module.split(".")[0] in FIRST_PARTY_ROOTS


def collect_unresolved() -> list[str]:
    problems: list[str] = []

    for path in _python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:  # pragma: no cover - a syntax error is its own failure
            problems.append(f"{path}: syntax error: {exc}")
            continue

        rel = path.relative_to(BACKEND_ROOT)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_first_party(alias.name) and _module_to_path(alias.name) is None:
                        problems.append(f"{rel}:{node.lineno}: no module '{alias.name}'")
                continue

            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level:  # relative import — not used in this codebase
                continue
            if not _is_first_party(node.module):
                continue

            target = _module_to_path(node.module)
            if target is None:
                problems.append(f"{rel}:{node.lineno}: no module '{node.module}'")
                continue

            exported = _defined_names(target)
            if "*" in exported:
                continue

            for alias in node.names:
                if alias.name in exported:
                    continue
                # `from app.api import health` — a submodule, not a name in __init__.py
                if _module_to_path(f"{node.module}.{alias.name}") is not None:
                    continue
                problems.append(
                    f"{rel}:{node.lineno}: '{node.module}' does not define '{alias.name}'"
                )

    return problems


def test_every_first_party_import_resolves():
    problems = collect_unresolved()
    assert problems == [], "unresolved first-party imports:\n  " + "\n  ".join(problems)


@pytest.mark.parametrize(
    "snippet, expect_problem",
    [
        ("from app.services.claude_service import claude_service\n", False),
        ("from tasks.curation import _orchestrate_curation\n", False),
        ("from tasks.curation import run_briefing_pipeline\n", True),
        ("from app.services.no_such_module import thing\n", True),
    ],
)
def test_gate_detects_what_it_claims_to(snippet, expect_problem, tmp_path):
    """The gate is only worth having if it fails on the case that motivated it."""
    probe = BACKEND_ROOT / "tests" / "_import_gate_probe.py"
    probe.write_text(snippet, encoding="utf-8")
    try:
        problems = [p for p in collect_unresolved() if "_import_gate_probe" in p]
        assert bool(problems) is expect_problem, problems
    finally:
        probe.unlink()
