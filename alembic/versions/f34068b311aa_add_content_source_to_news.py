"""add content_source to news

Revision ID: f34068b311aa
Revises: 9deb7db9ed0b
Create Date: 2026-09-19 06:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f34068b311aa'
down_revision: Union[str, Sequence[str], None] = '9deb7db9ed0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "news",
        sa.Column(
            "content_source",
            sa.String(length=20),
            server_default="rss_fallback",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("news", "content_source")