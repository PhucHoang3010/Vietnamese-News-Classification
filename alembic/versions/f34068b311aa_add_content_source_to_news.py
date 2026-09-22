"""add content source to news

Revision ID: f34068b311aa
Revises: 9deb7db9ed0b
"""

from alembic import op
import sqlalchemy as sa


revision = "f34068b311aa"
down_revision = "9deb7db9ed0b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "news",
        sa.Column(
            "content_source",
            sa.String(length=20),
            nullable=False,
            server_default="rss_fallback",
        ),
    )


def downgrade() -> None:
    op.drop_column("news", "content_source")
