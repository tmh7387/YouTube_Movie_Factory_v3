"""Add video_model to production_jobs.

curation_jobs already carried a video_model column, but it was only read when
generating the creative brief — the production pipeline ignored it and let the
ModelRouter pick per scene. Now that models are user-selectable (Seedance 2.0 /
2.5, Kling, Wan, MiniMax H3), a production run needs to record which model the
user asked for so retries and the UI agree with what was generated.

NULL keeps the previous behaviour: fall back to the curation job's choice, then
to auto-routing.

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'production_jobs',
        sa.Column('video_model', sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('production_jobs', 'video_model')
