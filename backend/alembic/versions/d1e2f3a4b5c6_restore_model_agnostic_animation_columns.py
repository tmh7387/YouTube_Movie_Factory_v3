"""Restore model-agnostic animation columns on production_scenes.

Stage-2 alignment (7f4bf2748828) renamed animation_* -> kling_*, which predates
the ModelRouter. The router selects among Kling v2 Master, Kling v1.6,
Seedance 2.0 and Wan Pro, so Kling-specific column names are wrong. This
migration restores the neutral names and re-adds animation_decision.

kling_mode and kling_request_dur are intentionally left as-is: they carry
Kling-specific request semantics with no model-neutral equivalent.

Revision ID: d1e2f3a4b5c6
Revises: 8425016f02a6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = '8425016f02a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('production_scenes', 'kling_model',
                    new_column_name='animation_model',
                    existing_type=sa.String(length=30),
                    type_=sa.String(length=50))
    op.alter_column('production_scenes', 'kling_task_id',
                    new_column_name='cometapi_task_id',
                    existing_type=sa.String(length=255))
    op.alter_column('production_scenes', 'kling_status',
                    new_column_name='animation_status',
                    existing_type=sa.String(length=20))
    op.add_column('production_scenes',
                  sa.Column('animation_decision', postgresql.JSONB(astext_type=sa.Text()),
                            nullable=True))


def downgrade() -> None:
    op.drop_column('production_scenes', 'animation_decision')
    op.alter_column('production_scenes', 'animation_status',
                    new_column_name='kling_status',
                    existing_type=sa.String(length=20))
    op.alter_column('production_scenes', 'cometapi_task_id',
                    new_column_name='kling_task_id',
                    existing_type=sa.String(length=255))
    op.alter_column('production_scenes', 'animation_model',
                    new_column_name='kling_model',
                    existing_type=sa.String(length=50),
                    type_=sa.String(length=30))
