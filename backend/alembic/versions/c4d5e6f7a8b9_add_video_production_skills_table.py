"""add video_production_skills table

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-04-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'c4d5e6f7a8b9'
down_revision = 'b3c4d5e6f7a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'video_production_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('slug', sa.String(200), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),

        # SKILL.md content
        sa.Column('description', sa.Text()),
        sa.Column('skill_body', sa.Text()),

        # Categorisation
        sa.Column('category', sa.String(30)),
        sa.Column('applicable_video_types', postgresql.JSONB()),
        sa.Column('tags', postgresql.JSONB()),

        # Core reusable content
        sa.Column('prompt_template', sa.Text()),
        sa.Column('example_prompts', postgresql.JSONB()),
        sa.Column('workflow_steps', postgresql.JSONB()),

        # Tool info (separate from body to keep skills tool-agnostic)
        sa.Column('tools_tested_with', postgresql.JSONB()),

        sa.Column('difficulty', sa.String(20)),

        # Provenance
        sa.Column('source_video_url', sa.Text()),
        sa.Column('source_knowledge_entry_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tutorial_knowledge.id')),

        # Quality
        sa.Column('confidence_score', sa.Numeric()),
        sa.Column('usage_count', sa.Integer(), server_default='0'),

        sa.Column('skill_file_path', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_skills_slug', 'video_production_skills', ['slug'], unique=True)
    op.create_index('ix_skills_category', 'video_production_skills', ['category'])


def downgrade() -> None:
    op.drop_index('ix_skills_category', 'video_production_skills')
    op.drop_index('ix_skills_slug', 'video_production_skills')
    op.drop_table('video_production_skills')
