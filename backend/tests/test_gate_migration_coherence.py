"""
Gate 8.3 — migration/usage coherence.

Every column an Alembic migration creates must be read or written somewhere in
backend/app or backend/tasks, outside the SQLAlchemy model definition and outside
the migrations themselves. A column that exists only on paper is a promise the
schema makes and the code never keeps.

This is the check that would have caught the eight dead `beat_*` columns and the
two dead `qa_*` columns.

PRE_EXISTING_UNUSED is the debt this pass inherited from the initial migration. It
is a fixed, closed list: nothing may be added to it. New dead columns fail the gate.
"""
import ast
import re
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = BACKEND_ROOT / "alembic" / "versions"
MODELS_FILE = BACKEND_ROOT / "app" / "models" / "__init__.py"
USAGE_DIRS = (BACKEND_ROOT / "app", BACKEND_ROOT / "tasks")

# Debt this pass inherited: schema columns that no application code reads or writes.
# Frozen — do not extend. Either wire a column or drop it in a migration.
#
# Notable: the youtube_* and final_video_path columns belong to a publish phase that
# was never built; production_tracks.* belongs to generated music, which is unreachable
# today (num_tracks is hardcoded 0 and this pass removed the unreachable Suno caller).
PRE_EXISTING_UNUSED = {
    ("production_jobs", "celery_task_id"),
    ("production_jobs", "concatenated_audio_path"),
    ("production_jobs", "final_video_path"),
    ("production_jobs", "youtube_description"),
    ("production_jobs", "youtube_hashtags"),
    ("production_jobs", "youtube_title"),
    ("production_jobs", "youtube_video_id"),
    ("production_scenes", "animation_decision"),
    ("production_scenes", "image_b64_path"),
    ("production_scenes", "image_tail_scene_id"),
    ("production_scenes", "kling_request_dur"),
    ("production_scenes", "raw_video_path"),
    ("production_scenes", "raw_video_url"),
    ("production_tracks", "local_audio_path"),
    ("production_tracks", "suno_task_id"),
    ("research_jobs", "expanded_queries"),
    ("research_jobs", "gemini_model"),
    ("research_jobs", "top_n"),
    ("research_videos", "selected_for_curation"),
    ("system_config", "is_secret"),
}

# Columns present on every table and never referenced by name in application code.
UNIVERSAL_IGNORES = {"id", "created_at"}


def _module_level_string(tree: ast.Module, name: str) -> str | None:
    for node in tree.body:
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target.id
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
        if target == name and isinstance(node.value, ast.Constant):
            return node.value.value if isinstance(node.value.value, str) else None
    return None


def _ordered_migrations() -> list[ast.Module]:
    """Parse every migration and return them in revision-chain order (base first)."""
    by_revision: dict[str, ast.Module] = {}
    down: dict[str, str | None] = {}

    for path in sorted(MIGRATIONS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        revision = _module_level_string(tree, "revision")
        if revision is None:
            continue
        by_revision[revision] = tree
        down[revision] = _module_level_string(tree, "down_revision")

    children = {parent: rev for rev, parent in down.items()}
    heads = [rev for rev, parent in down.items() if parent is None]
    assert len(heads) == 1, f"expected a single base revision, found {heads}"

    ordered: list[ast.Module] = []
    current: str | None = heads[0]
    while current is not None:
        ordered.append(by_revision[current])
        current = children.get(current)

    assert len(ordered) == len(by_revision), (
        "migration chain is not linear — some revisions are unreachable from the base"
    )
    return ordered


def _upgrade_body(tree: ast.Module) -> list[ast.stmt]:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "upgrade":
            return node.body
    return []


def _iter_migration_columns() -> set[tuple[str, str]]:
    """
    Replay the upgrade() path of the whole migration chain and return the columns
    that survive to the head. Columns added and later dropped, or belonging to a
    dropped table, are not part of the current schema and are not the gate's business.
    Only upgrade() is read — downgrade() re-adds columns that no longer exist.
    """
    columns: set[tuple[str, str]] = set()

    for tree in _ordered_migrations():
        for statement in _upgrade_body(tree):
            for node in ast.walk(statement):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                op_name = node.func.attr
                if op_name not in (
                    "create_table", "add_column", "drop_column",
                    "drop_table", "rename_table", "alter_column",
                ):
                    continue
                if not node.args or not isinstance(node.args[0], ast.Constant):
                    continue
                table = node.args[0].value
                if not isinstance(table, str):
                    continue

                if op_name in ("create_table", "add_column"):
                    for arg in node.args[1:]:
                        for column in _column_names(arg):
                            columns.add((table, column))
                elif op_name == "drop_column":
                    if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                        columns.discard((table, node.args[1].value))
                elif op_name == "drop_table":
                    columns = {(t, c) for t, c in columns if t != table}
                elif op_name == "alter_column":
                    # op.alter_column('t', 'old', new_column_name='new')
                    new_name = next(
                        (
                            kw.value.value
                            for kw in node.keywords
                            if kw.arg == "new_column_name" and isinstance(kw.value, ast.Constant)
                        ),
                        None,
                    )
                    if new_name and len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                        columns.discard((table, node.args[1].value))
                        columns.add((table, new_name))
                elif op_name == "rename_table":
                    if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                        new_table = node.args[1].value
                        columns = {
                            (new_table if t == table else t, c) for t, c in columns
                        }

    return columns


def _column_names(node: ast.AST) -> list[str]:
    """Extract the literal name from sa.Column('name', ...) calls inside a node."""
    names = []
    for sub in ast.walk(node):
        if (
            isinstance(sub, ast.Call)
            and isinstance(sub.func, ast.Attribute)
            and sub.func.attr == "Column"
            and sub.args
            and isinstance(sub.args[0], ast.Constant)
            and isinstance(sub.args[0].value, str)
        ):
            names.append(sub.args[0].value)
    return names


def _usage_corpus() -> str:
    """All application source except the model definitions themselves."""
    chunks = []
    for directory in USAGE_DIRS:
        for path in sorted(directory.rglob("*.py")):
            if path == MODELS_FILE:
                continue
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _frontend_corpus() -> str:
    """
    Frontend sources count as usage: a column serialised straight through an API
    handler is read by the UI, and the handler mentions it by name anyway.
    """
    frontend = BACKEND_ROOT.parent / "frontend" / "src"
    if not frontend.is_dir():
        return ""
    return "\n".join(
        path.read_text(encoding="utf-8")
        for pattern in ("*.ts", "*.tsx")
        for path in sorted(frontend.rglob(pattern))
    )


def unused_columns() -> set[tuple[str, str]]:
    corpus = _usage_corpus() + "\n" + _frontend_corpus()
    unused = set()
    for table, column in _iter_migration_columns():
        if column in UNIVERSAL_IGNORES:
            continue
        if re.search(rf"\b{re.escape(column)}\b", corpus):
            continue
        unused.add((table, column))
    return unused


def test_no_new_paper_only_columns():
    offenders = sorted(unused_columns() - PRE_EXISTING_UNUSED)
    assert offenders == [], (
        "columns exist in the schema but are neither read nor written:\n  "
        + "\n  ".join(f"{t}.{c}" for t, c in offenders)
    )


def test_pre_existing_debt_list_only_shrinks():
    """Once a legacy dead column is wired or dropped, it must leave the list."""
    resolved = sorted(PRE_EXISTING_UNUSED - unused_columns())
    assert resolved == [], (
        "these columns are now used (or gone) and must be removed from "
        "PRE_EXISTING_UNUSED:\n  " + "\n  ".join(f"{t}.{c}" for t, c in resolved)
    )


def test_beat_and_qa_columns_are_not_dead():
    """
    The specific regression this gate exists for: the eight beat_* columns and the
    two qa_* columns shipped with zero assignments anywhere.
    """
    dead = {c for _, c in unused_columns() if c.startswith(("beat_", "qa_"))}
    assert dead == set(), f"beat/qa columns still unused: {sorted(dead)}"
