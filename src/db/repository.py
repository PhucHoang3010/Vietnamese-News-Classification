from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import News
from src.db.deduplication import (
    generate_content_hash,
    normalize_url,
)


class NewsRepository:
    """Repository for CRUD operations on the news table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def exists_by_url(self, url: str) -> bool:
        """Return True if a news article with the given URL exists."""

        stmt = (
            select(News.id)
            .where(News.url == url)
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def exists_by_content_hash(self, content_hash: str) -> bool:
        """Return True if a news article with the given content hash exists."""

        stmt = (
            select(News.id)
            .where(News.content_hash == content_hash)
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def create_news(
        self,
        *,
        url: str,
        content_hash: str,
        title: str,
        content: str,
        source: str,
        category: str,
        decision_score: float,
        published_at: datetime | None = None,
    ) -> News:
        """Create and persist a new news article."""

        news = News(
            url=url,
            content_hash=content_hash,
            title=title,
            content=content,
            source=source,
            category=category,
            decision_score=decision_score,
            published_at=published_at,
        )

        self.session.add(news)

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise

        await self.session.refresh(news)

        return news

    async def get_news_by_id(
        self,
        news_id: int,
    ) -> News | None:
        """Return one news article by primary key."""

        stmt = (
            select(News)
            .where(News.id == news_id)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def list_news(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[News]:
        """Return news articles ordered by newest crawled time."""

        stmt = (
            select(News)
            .order_by(News.crawled_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def create_news_deduplicated(
        self,
        *,
        url: str,
        title: str,
        content: str,
        source: str,
        category: str,
        decision_score: float,
        published_at: datetime | None = None,
    ) -> tuple[News | None, str]:
        """
        Normalize and insert a news article with deduplication.

        Returns:
            (news, status)

        Status:
            CREATED
            DUPLICATE_URL
            DUPLICATE_CONTENT
        """

        normalized_url = normalize_url(url)

        hashes = generate_content_hash(
            title,
            content,
        )

        content_hash = hashes["content_hash"]

        if await self.exists_by_url(normalized_url):
            return None, "DUPLICATE_URL"

        if await self.exists_by_content_hash(content_hash):
            return None, "DUPLICATE_CONTENT"

        try:
            news = await self.create_news(
                url=normalized_url,
                content_hash=content_hash,
                title=title,
                content=content,
                source=source,
                category=category,
                decision_score=decision_score,
                published_at=published_at,
            )

            return news, "CREATED"

        except IntegrityError:
            # A concurrent transaction may have inserted
            # the same URL/content hash after our existence check.
            return None, "DUPLICATE_CONSTRAINT"