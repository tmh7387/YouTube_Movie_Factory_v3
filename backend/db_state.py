"""
Read-only report on what the database really contains, and which Alembic revision
matches it.

Why this exists
---------------
`alembic current` reads one row — the version number the database claims — and stops
dead if that number names no file:

    ERROR  Can't locate revision identified by 'e7f8a9b0c1d2'
    FAILED: Can't locate revision identified by 'e7f8a9b0c1d2'

That message says nothing about the tables and columns, which is the thing that
actually matters. A stamp guessed from it can skip a real change, after which the
schema and the version row disagree in silence.

So this asks the database directly. Every migration in the chain carries a fingerprint
— one table or column it is the only migration to create. Present means applied.

    python -m db_state

It writes nothing. Ever. It ends by printing the exact commands to run.
"""
from __future__ import annotations

import asyncio
import sys
from typing import List, Optional, Tuple

if sys.platform == "win32":
    # Same reason as live_check and app/main.py: psycopg refuses the Proactor loop.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


# The chain, oldest first, each with one thing it alone creates.
# (revision, description, table, column or None for "the table itself", detectable)
#
# `detectable` is False for a migration whose objects can exist WITHOUT it having run.
# b7c8d9e0f1a2 is the only one: its whole job is to adopt columns that something else
# already made, so it uses ADD COLUMN IF NOT EXISTS. Finding progress_log therefore says
# nothing about whether it ran, and treating it as evidence invents a gap that is not
# there. It is skipped, and re-running it is harmless by construction.
CHAIN: List[Tuple[str, str, str, Optional[str], bool]] = [
    ("521d1b9ef974", "initial migration",              "production_jobs",   "job_dir", True),
    ("a2b3c4d5e6f7", "research brief",                 "research_jobs",     "research_brief", True),
    ("7f4bf2748828", "stage 2 schema alignment",       "production_jobs",   "tempo_bpm", True),
    ("b3c4d5e6f7a8", "tutorial knowledge table",       "tutorial_knowledge", None, True),
    ("c4d5e6f7a8b9", "video production skills table",  "video_production_skills", None, True),
    ("8425016f02a6", "bible intake + model router",    "pre_production_bibles", None, True),
    ("d1e2f3a4b5c6", "model-agnostic animation",       "production_scenes", "animation_decision", True),
    ("e5f6a7b8c9d0", "reference inputs on scenes",     "production_scenes", "reference_inputs", True),
    ("f6a7b8c9d0e1", "approvals + generation outcome", "generation_outcome", None, True),
    ("b7c8d9e0f1a2", "reconcile out-of-band schema",   "production_jobs",   "progress_log", False),
    ("c8d9e0f1a2b3", "job ownership and liveness",     "production_jobs",   "worker_id", True),
]

GREEN, RED, DIM, BOLD, OFF = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"

COMPLETE, PARTIAL, GAP = "complete", "partial", "gap"


def decide(applied: List[str], missing: List[str]) -> Tuple[str, str, List[str], List[str]]:
    """
    Turn present/absent into one instruction. Pure, so it can be tested without a database.

    Returns (verdict, stamp target, still to apply, out-of-order revisions).

    The safe target is the last revision that is present AND has nothing absent before
    it. Anything present after the first absent one is a gap: the schema was built out
    of order, no single stamp describes it, and stamping would tell Alembic to skip a
    change the database never got.
    """
    order = [rev for rev, _label, _table, _column, detectable in CHAIN if detectable]
    first_missing = min((order.index(rev) for rev in missing), default=len(order))
    contiguous = order[:first_missing]
    gap = [rev for rev in applied if rev not in contiguous]

    if gap:
        return GAP, "", missing, gap
    if not missing:
        return COMPLETE, CHAIN[-1][0], [], []
    return PARTIAL, contiguous[-1] if contiguous else "base", missing, []


async def report() -> int:
    import logging

    from sqlalchemy import text

    # The engine is built with echo on. Its SQL log buries the report this script exists
    # to print, and none of it is the answer to the question being asked.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        stamped = await session.scalar(
            text(
                "SELECT version_num FROM alembic_version"
                " WHERE EXISTS (SELECT 1 FROM information_schema.tables"
                "               WHERE table_name = 'alembic_version')"
            )
        )

        tables = {
            row[0]
            for row in (
                await session.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables"
                        " WHERE table_schema = 'public'"
                    )
                )
            ).all()
        }
        columns = {
            (row[0], row[1])
            for row in (
                await session.execute(
                    text(
                        "SELECT table_name, column_name FROM information_schema.columns"
                        " WHERE table_schema = 'public'"
                    )
                )
            ).all()
        }

    print(f"\n{BOLD}db_state — what the database really contains{OFF}\n")
    print(f"  version row says: {stamped or '(no alembic_version row)'}")
    known = {rev for rev, *_ in CHAIN}
    if stamped and stamped not in known:
        print(f"  {RED}that revision is in no migration file in this repo{OFF}")
    print()

    applied: List[str] = []
    missing: List[str] = []
    for rev, label, table, column, detectable in CHAIN:
        present = (table in tables) if column is None else ((table, column) in columns)
        thing = table if column is None else f"{table}.{column}"
        if not detectable:
            print(f"  {DIM}n/a    {OFF}  {rev}  {label:<32} {DIM}{thing} — adopts what exists{OFF}")
            continue
        mark = f"{GREEN}present{OFF}" if present else f"{RED}absent {OFF}"
        print(f"  {mark}  {rev}  {label:<32} {DIM}{thing}{OFF}")
        (applied if present else missing).append(rev)

    print()

    verdict, target, missing, gap = decide(applied, missing)

    # --purge, not a plain stamp. A plain stamp reads the version row first, and when
    # that row names a revision with no file, it dies with the same "Can't locate
    # revision" as `alembic current`. --purge empties the row before writing, so it
    # works no matter what the row said.
    if verdict == COMPLETE:
        print(f"{BOLD}Every migration is already applied.{OFF}")
        print("The schema is complete. Only the version row is wrong. Fix it with:\n")
        print(f"  alembic stamp --purge {target}")
        print("\nThen check it took:\n\n  alembic current\n")
        return 0

    if verdict == GAP:
        print(f"{RED}{BOLD}The schema has a gap.{OFF}")
        print("Some later changes are applied while earlier ones are not:")
        print(f"  applied out of order: {', '.join(gap)}")
        print("\nDo NOT stamp. Send this whole report to Claude first.\n")
        return 2

    print(f"{BOLD}The schema stops cleanly after {target}.{OFF}")
    print(f"Still to apply: {', '.join(missing)}\n")
    print("Safe recovery, in order:\n")
    print(f"  alembic stamp --purge {target}")
    print("  alembic upgrade head")
    print("  python -m db_state          # run this again; everything should say present\n")
    return 0


def main() -> int:
    try:
        return asyncio.run(report())
    except Exception as exc:                      # noqa: BLE001 - a report, not a service
        print(f"\n{RED}could not read the database: {type(exc).__name__}: {exc}{OFF}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
