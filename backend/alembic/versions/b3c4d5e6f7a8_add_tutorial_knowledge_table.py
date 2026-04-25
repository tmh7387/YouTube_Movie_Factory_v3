"""add tutorial_knowledge table

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-04-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b3c4d5e6f7a8'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tutorial_knowledge',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('youtube_url', sa.Text(), nullable=False),
        sa.Column('video_id', sa.String(50)),
        sa.Column('category', sa.String(30), server_default='general'),
        sa.Column('status', sa.String(20), server_default='pending'),

        # Gemini analysis
        sa.Column('gemini_analysis', postgresql.JSONB()),
        sa.Column('standout_tip', sa.Text()),
        sa.Column('exact_prompts', postgresql.JSONB()),
        sa.Column('tool_names', postgresql.JSONB()),
        sa.Column('workflow_steps', postgresql.JSONB()),
        sa.Column('key_settings', postgresql.JSONB()),
        sa.Column('category_specific', postgresql.JSONB()),
        sa.Column('full_technique_summary', sa.Text()),

        # Resource mining
        sa.Column('description_resources', postgresql.JSONB()),
        sa.Column('comment_resources', postgresql.JSONB()),
        sa.Column('aggregated_resources', postgresql.JSONB()),

        # External resource content
        sa.Column('external_resources', postgresql.JSONB()),

        sa.Column('error_message', sa.Text()),
        sa.Column('gemini_model_used', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_tutorial_knowledge_category', 'tutorial_knowledge', ['category'])
    op.create_index('ix_tutorial_knowledge_status', 'tutorial_knowledge', ['status'])


def downgrade() -> None:
    op.drop_index('ix_tutorial_knowledge_status', 'tutorial_knowledge')
    op.drop_index('ix_tutorial_knowledge_category', 'tutorial_knowledge')
    op.drop_table('tutorial_knowledge')
