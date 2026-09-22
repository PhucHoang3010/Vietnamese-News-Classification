"""add keyword occurrences

Revision ID: 58183fc56f68
Revises: f34068b311aa
"""

from alembic import op
import sqlalchemy as sa


revision = "58183fc56f68"
down_revision = "f34068b311aa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "keyword_occurrences",

        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "news_id",
            sa.BigInteger(),
            nullable=False,
        ),

        sa.Column(
            "keyword",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "display_keyword",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "ngram",
            sa.SmallInteger(),
            nullable=False,
        ),

        sa.Column(
            "frequency",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "tfidf",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "association",
            sa.Float(),
            nullable=False,
            server_default="1",
        ),

        sa.Column(
            "phrase_quality",
            sa.Float(),
            nullable=False,
            server_default="1",
        ),

        sa.Column(
            "boundary_quality",
            sa.Float(),
            nullable=False,
            server_default="1",
        ),

        sa.Column(
            "final_score",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.ForeignKeyConstraint(
            ["news_id"],
            ["news.id"],
            ondelete="CASCADE",
        ),

        sa.UniqueConstraint(
            "news_id",
            "keyword",
            name="uq_keyword_occurrences_news_keyword",
        ),
    )

    op.create_index(
        "ix_keyword_occurrences_news_id",
        "keyword_occurrences",
        ["news_id"],
    )

    op.create_index(
        "ix_keyword_occurrences_keyword",
        "keyword_occurrences",
        ["keyword"],
    )

    op.create_index(
        "ix_keyword_occurrences_keyword_created",
        "keyword_occurrences",
        ["keyword", "created_at"],
    )

    op.create_index(
        "ix_keyword_occurrences_news_score",
        "keyword_occurrences",
        ["news_id", "final_score"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_keyword_occurrences_news_score",
        table_name="keyword_occurrences",
    )

    op.drop_index(
        "ix_keyword_occurrences_keyword_created",
        table_name="keyword_occurrences",
    )

    op.drop_index(
        "ix_keyword_occurrences_keyword",
        table_name="keyword_occurrences",
    )

    op.drop_index(
        "ix_keyword_occurrences_news_id",
        table_name="keyword_occurrences",
    )

    op.drop_table("keyword_occurrences")
