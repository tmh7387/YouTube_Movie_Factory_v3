"""Record which image-generation path each scene took.

Before this, nothing distinguished a scene generated from bible reference images
(GPT-Image-2 /images/edits, character-consistent) from one generated from prompt
text alone (CometAPI SeeDream). reference_inputs makes the choice auditable:

    {"mode": "reference"|"text", "refs": [url, ...], "service": "gpt_image_2"|"cometapi"}

Revision ID: e5f6a7b8c9d0
Revises: d1e2f3a4b5c6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'production_scenes',
        sa.Column('reference_inputs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('production_scenes', 'reference_inputs')
