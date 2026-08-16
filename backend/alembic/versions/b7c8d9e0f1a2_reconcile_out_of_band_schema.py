"""Fold the out-of-band schema changes back into the migration chain.

Five columns the application reads and writes every run exist in no migration at all.
They were applied straight to Supabase — production_jobs' music columns by
backend/alter.py, the rest by hand — so `alembic upgrade head` produced a schema the
code could not run against. The end-to-end smoke gate is what surfaced this: it is the
first time the chain has ever been run against an empty database.

  production_jobs.music_url        written by POST /api/production/upload/audio
  production_jobs.music_filename   read every pipeline run to decide the Seedance ref
  production_jobs.beat_sync_enabled  set at job creation
  production_jobs.progress_log     appended on every _log() call
  research_jobs.research_summary   dropped by 521d1b9ef974 and never re-added, yet
                                   written by every research job since

Written with ADD COLUMN IF NOT EXISTS so it is a no-op on the live database where the
columns already exist, and does the real work on a fresh one. This appends to the head;
it does not touch the existing chain.

Revision ID: b7c8d9e0f1a2
Revises: f6a7b8c9d0e1
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE production_jobs
            ADD COLUMN IF NOT EXISTS music_url TEXT,
            ADD COLUMN IF NOT EXISTS music_filename TEXT,
            ADD COLUMN IF NOT EXISTS beat_sync_enabled BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS progress_log JSONB
    """)
    op.execute("""
        ALTER TABLE research_jobs
            ADD COLUMN IF NOT EXISTS research_summary TEXT
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE production_jobs
            DROP COLUMN IF EXISTS progress_log,
            DROP COLUMN IF EXISTS beat_sync_enabled,
            DROP COLUMN IF EXISTS music_filename,
            DROP COLUMN IF EXISTS music_url
    """)
    op.execute("""
        ALTER TABLE research_jobs
            DROP COLUMN IF EXISTS research_summary
    """)
