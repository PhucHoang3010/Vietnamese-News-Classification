from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="rss_fallback",
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    decision_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_news_published_at", "published_at"),
        Index("ix_news_category", "category"),
        Index(
            "ix_news_published_at_category",
            "published_at",
            "category",
        ),
    )