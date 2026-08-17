"""Persist scene approvals and record one outcome row per generated scene.

Scene approvals lived in a React useState Set and were never sent to the server, so
the approval gate was decorative and nothing survived a page reload. generation_outcome
is the signal the platform had no way of collecting: what was asked for, what came
back, and what the QA gate and the human each thought of it.

user_approved is nullable on purpose — null means "not reviewed", which is a different
thing from False ("a human looked and rejected it").

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('production_scenes', sa.Column('user_approved', sa.Boolean(), nullable=True))
    op.add_column('production_scenes', sa.Column('user_feedback', sa.Text(), nullable=True))

    op.create_table(
        'generation_outcome',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scene_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('reference_mode', sa.String(length=20), nullable=True),
        sa.Column('beat_aligned', sa.Boolean(), nullable=True),
        sa.Column('qa_pass', sa.Boolean(), nullable=True),
        sa.Column('qa_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_approved', sa.Boolean(), nullable=True),
        sa.Column('skill_slugs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['scene_id'], ['production_scenes.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['production_jobs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scene_id'),
    )
    op.create_index('ix_generation_outcome_job_id', 'generation_outcome', ['job_id'])


def downgrade() -> None:
    op.drop_index('ix_generation_outcome_job_id', table_name='generation_outcome')
    op.drop_table('generation_outcome')
    op.drop_column('production_scenes', 'user_feedback')
    op.drop_column('production_scenes', 'user_approved')
