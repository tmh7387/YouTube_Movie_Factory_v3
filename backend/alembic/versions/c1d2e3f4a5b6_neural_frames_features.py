"""neural_frames_features

Adds all fields for:
  Phase 1 — SeeDance 2.0 video engine per-scene
  Phase 2 — GPT-Image-2 + ProductionCharacter table
  Phase 4 — stem analysis on production_jobs + stem_energy_hint per scene
  Phase 5 — lyrics on production_jobs
  Phase 6 — upscale_enabled on production_jobs + upscaled_video_path per scene

Revision ID: c1d2e3f4a5b6
Revises: 7f4bf2748828
Create Date: 2026-04-25 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "7f4bf2748828"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── production_jobs ────────────────────────────────────────────────────
    op.add_column(
        "production_jobs",
        sa.Column("stem_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "production_jobs",
        sa.Column("lyrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "production_jobs",
        sa.Column("upscale_enabled", sa.Boolean(), nullable=True, server_default="false"),
    )

    # ── production_scenes ──────────────────────────────────────────────────
    op.add_column(
        "production_scenes",
        sa.Column("video_engine", sa.String(length=20), nullable=True, server_default="kling"),
    )
    op.add_column(
        "production_scenes",
        sa.Column("seedance_task_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "production_scenes",
        sa.Column("seedance_status", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "production_scenes",
        sa.Column("character_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "production_scenes",
        sa.Column("stem_energy_hint", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "production_scenes",
        sa.Column("upscaled_video_path", sa.Text(), nullable=True),
    )

    # ── production_characters (new table) ─────────────────────────────────
    op.create_table(
        "production_characters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production_jobs.id"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "reference_image_paths",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("production_characters")
    for col in [
        "upscaled_video_path",
        "stem_energy_hint",
        "character_name",
        "seedance_status",
        "seedance_task_id",
        "video_engine",
    ]:
        op.drop_column("production_scenes", col)
    for col in ["upscale_enabled", "lyrics", "stem_analysis"]:
        op.drop_column("production_jobs", col)
