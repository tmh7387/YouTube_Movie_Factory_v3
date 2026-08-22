"""Add shot_plan to production_scenes.

Clip length was never carried through the pipeline. The creative brief already
returned a per-scene `duration`, `target_duration_sec` already existed on the
row, and neither was read — tasks/production.py asked every model for a literal
5 seconds on every scene regardless of what the scene needed or what the model
could do.

Removing that constant needs somewhere to put the structure that replaces it.
`target_duration_sec` covers total clip length; `shot_plan` covers what happens
inside the clip — how many cuts, and the timestamped beat for each one, which is
what Seedance 2.5 honours and what a director actually specifies.

Shape:

    {
      "shots": [
        {"index": 1, "start": 0,  "end": 4,  "beat": "..."},
        {"index": 2, "start": 4,  "end": 11, "beat": "..."}
      ],
      "source": "brief" | "user"
    }

NULL means no explicit plan: the clip runs as a single take for
`target_duration_sec`. There is no default length — a scene with neither is a
planning gap and is reported rather than silently filled.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, Sequence[str], None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'production_scenes',
        sa.Column('shot_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('production_scenes', 'shot_plan')
