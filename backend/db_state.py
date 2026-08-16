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
# (revision, description, table, column or None for "the table itself")
CHAIN: List[Tuple[str, str, str, Optional[str]]] = [
    ("521d1b9ef974", "initial migration",              "production_jobs",   "job_dir"),
    ("a2b3c4d5e6f7", "research brief",                 "research_jobs",     "research_brief"),
    ("7f4bf2748828", "stage 2 schema alignment",       "production_jobs",   "tempo_bpm"),
    ("b3c4d5e6f7a8", "tutorial knowledge table",       "tutorial_knowledge", None),
    ("c4d5e6f7a8b9", "video production skills table",  "video_production_skills", None),
    ("8425016f02a6", "bible intake + model router",    "pre_production_bibles", None),
    ("d1e2f3a4b5c6", "model-agnostic animation",       "production_scenes", "animation_decision"),
    ("e5f6a7b8c9d0", "reference inputs on scenes",     "production_scenes", "reference_inputs"),
    ("f6a7b8c9d0e1", "approvals + generation outcome", "generation_outcome", None),
    ("b7c8d9e0f1a2", "reconcile out-of-band schema",   "production_jobs",   "progress_log"),
    ("c8d9e0f1a2b3", "job ownership and liveness",     "production_jobs",   "worker_id"),
]

GREEN, RED, DIM, BOLD, OFF = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"


async def report() -> int:
    from sqlalchemy import text

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
    for rev, label, table, column in CHAIN:
        present = (table in tables) if column is None else ((table, column) in columns)
        thing = table if column is None else f"{table}.{column}"
        mark = f"{GREEN}present{OFF}" if present else f"{RED}absent {OFF}"
        print(f"  {mark}  {rev}  {label:<32} {DIM}{thing}{OFF}")
        (applied if present else missing).append(rev)

    print()

    # The safe stamp target is the last revision whose fingerprint is present AND that
    # has nothing missing before it. A gap means the schema was built out of order, by
    # hand, and no single stamp describes it.
    order = [rev for rev, *_ in CHAIN]
    first_missing = min((order.index(rev) for rev in missing), default=len(order))
    contiguous = order[:first_missing]
    gap = [rev for rev in applied if rev not in contiguous]

    if not missing:
        print(f"{BOLD}Every migration is already applied.{OFF}")
        print("The schema is complete. Only the version row is wrong. Fix it with:\n")
        print(f"  alembic stamp {CHAIN[-1][0]}\n")
        print("Then check it took:\n\n  alembic current\n")
        return 0

    if gap:
        print(f"{RED}{BOLD}The schema has a gap.{OFF}")
        print("Some later changes are applied while earlier ones are not:")
        print(f"  applied out of order: {', '.join(gap)}")
        print("\nDo NOT stamp. Send this whole report to Claude first.\n")
        return 2

    target = contiguous[-1] if contiguous else None
    print(f"{BOLD}The schema stops cleanly after {target or '(nothing)'}.{OFF}")
    print(f"Still to apply: {', '.join(missing)}\n")
    print("Safe recovery, in order:\n")
    if target:
        print(f"  alembic stamp {target}")
    else:
        print("  alembic stamp base")
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
