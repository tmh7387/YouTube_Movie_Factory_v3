"""v4_bible_intake_ripple_model_router

Revision ID: 8425016f02a6
Revises: c4d5e6f7a8b9
Create Date: 2026-05-01 16:58:14.905170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8425016f02a6'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — v4 additions only. No destructive changes."""
    # 1. Create pre_production_bibles table
    op.create_table('pre_production_bibles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('curation_job_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('characters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('environments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('style_lock', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('surreal_motifs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('camera_specs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('character_sheet_urls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('environment_sheet_urls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('process_log', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['curation_job_id'], ['curation_jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Add bible_id FK to curation_jobs
    op.add_column('curation_jobs', sa.Column('bible_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_curation_bible', 'curation_jobs', 'pre_production_bibles', ['bible_id'], ['id'])

    # 3. Add bible/QA columns to production_scenes
    op.add_column('production_scenes', sa.Column('bible_character', sa.String(length=200), nullable=True))
    op.add_column('production_scenes', sa.Column('bible_environment', sa.String(length=200), nullable=True))
    op.add_column('production_scenes', sa.Column('qa_status', sa.String(length=20), nullable=True))
    op.add_column('production_scenes', sa.Column('qa_notes', sa.Text(), nullable=True))

    # 4. Add source_type and source_data to research_jobs
    op.add_column('research_jobs', sa.Column('source_type', sa.String(length=30), nullable=True))
    op.add_column('research_jobs', sa.Column('source_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema — remove v4 additions."""
    op.drop_column('research_jobs', 'source_data')
    op.drop_column('research_jobs', 'source_type')

    op.drop_column('production_scenes', 'qa_notes')
    op.drop_column('production_scenes', 'qa_status')
    op.drop_column('production_scenes', 'bible_environment')
    op.drop_column('production_scenes', 'bible_character')

    op.drop_constraint('fk_curation_bible', 'curation_jobs', type_='foreignkey')
    op.drop_column('curation_jobs', 'bible_id')

    op.drop_table('pre_production_bibles')
