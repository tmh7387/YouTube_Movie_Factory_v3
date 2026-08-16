"""Give production jobs an owner and a pulse.

Jobs used to run inside the web request with nothing recording who was running them.
A server restart mid-run left the job stuck in 'animating' forever, indistinguishable
from one still working, and with no way to pick it back up.

worker_id + heartbeat_at make ownership explicit and staleness detectable: a worker
claims a job atomically, refreshes the heartbeat as it progresses, and any job whose
heartbeat has gone stale is free for another worker to take over. attempt_count is
there so a job that keeps dying can be spotted rather than retried forever.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c8d9e0f1a2b3'
down_revision: Union[str, Sequence[str], None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('production_jobs', sa.Column('worker_id', sa.String(length=64), nullable=True))
    op.add_column('production_jobs', sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('production_jobs', sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('production_jobs', sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=True))
    # The worker's poll is "queued, or running with a stale heartbeat".
    op.create_index(
        'ix_production_jobs_status_heartbeat',
        'production_jobs',
        ['status', 'heartbeat_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_production_jobs_status_heartbeat', table_name='production_jobs')
    op.drop_column('production_jobs', 'attempt_count')
    op.drop_column('production_jobs', 'heartbeat_at')
    op.drop_column('production_jobs', 'claimed_at')
    op.drop_column('production_jobs', 'worker_id')
