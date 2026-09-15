import asyncio

from sqlalchemy import delete, select

from src.db.database import AsyncSessionLocal
from src.db.deduplication import normalize_url
from src.db.models import News
from src.db.repository import NewsRepository


TEST_SOURCE = "phase7-url-diagnose"

URL_1 = (
    "https://example.com/"
    "phase7-dedup-test-001"
)

URL_2 = (
    "https://example.com/"
    "phase7-dedup-test-001"
    "?utm_source=facebook"
    "&fbclid=test123"
)


async def main():
    print("=" * 60)
    print("PHASE 7 — SECTION 7.9.2A")
    print("URL DEDUPLICATION DIAGNOSTIC")
    print("=" * 60)

    normalized_url_1 = normalize_url(URL_1)
    normalized_url_2 = normalize_url(URL_2)

    print()
    print("Original URL 1:")
    print(URL_1)

    print()
    print("Original URL 2:")
    print(URL_2)

    print()
    print("Normalized URL 1:")
    print(normalized_url_1)

    print()
    print("Normalized URL 2:")
    print(normalized_url_2)

    print()

    assert normalized_url_1 == normalized_url_2

    print("PASS: URL normalization produces identical URLs")

    async with AsyncSessionLocal() as session:

        repository = NewsRepository(session)

        # Cleanup
        await session.execute(
            delete(News).where(
                News.source == TEST_SOURCE
            )
        )
        await session.commit()

        # Insert directly through repository
        article = await repository.create_news(
            url=normalized_url_1,
            content_hash="a" * 64,
            title="Diagnostic article",
            content="Diagnostic content",
            source=TEST_SOURCE,
            category="Khoa học",
            decision_score=1.0,
        )

        print()
        print(
            "Inserted database ID:",
            article.id,
        )

        print()
        print("Stored URL:")
        print(article.url)

        # Direct DB query
        result = await session.execute(
            select(News).where(
                News.url == normalized_url_1
            )
        )

        db_article = result.scalar_one_or_none()

        assert db_article is not None

        print()
        print(
            "PASS: PostgreSQL contains normalized URL"
        )

        # Repository existence check
        exists = await repository.exists_by_url(
            normalized_url_2
        )

        print()
        print(
            "exists_by_url(normalized_url_2):",
            exists,
        )

        assert exists is True

        print()
        print(
            "PASS: exists_by_url detects duplicate URL"
        )

        # Cleanup
        await session.execute(
            delete(News).where(
                News.source == TEST_SOURCE
            )
        )

        await session.commit()

        print()
        print("PASS: Diagnostic records cleaned up")

    print()
    print("=" * 60)
    print("SECTION 7.9.2A DIAGNOSTIC: PASS")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())