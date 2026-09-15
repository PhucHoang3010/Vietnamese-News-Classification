import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete, select

from src.db.database import AsyncSessionLocal
from src.db.models import News
from src.db.repository import NewsRepository


TEST_SOURCE = "phase7-test"

TEST_URL = (
    "https://example.com/"
    "phase7-dedup-test-001"
)


async def main():
    print("=" * 60)
    print("PHASE 7 — SECTION 7.9.2")
    print("REAL POSTGRESQL DEDUPLICATION TEST")
    print("=" * 60)

    async with AsyncSessionLocal() as session:

        repository = NewsRepository(session)

        # --------------------------------------------------
        # Cleanup before test
        # --------------------------------------------------

        await session.execute(
            delete(News).where(
                News.source == TEST_SOURCE
            )
        )

        await session.commit()

        # --------------------------------------------------
        # 1. First insert
        # --------------------------------------------------

        article, status = (
            await repository.create_news_deduplicated(
                url=TEST_URL,
                title="Tin tức kiểm thử PostgreSQL",
                content=(
                    "Nội dung kiểm thử deduplication "
                    "cho PostgreSQL."
                ),
                source=TEST_SOURCE,
                category="Khoa học",
                decision_score=1.0,
                published_at=datetime.now(timezone.utc),
            )
        )

        assert status == "CREATED"
        assert article is not None

        print("PASS: First article CREATED")

        # --------------------------------------------------
        # 2. Same URL with tracking parameters
        # --------------------------------------------------

        duplicate_url, duplicate_status = (
            await repository.create_news_deduplicated(
                url=(
                    TEST_URL
                    + "?utm_source=facebook"
                    + "&fbclid=test123"
                ),
                title="Một tiêu đề khác",
                content="Một nội dung khác.",
                source=TEST_SOURCE,
                category="Khoa học",
                decision_score=1.0,
            )
        )

        assert duplicate_url is None
        assert duplicate_status == "DUPLICATE_URL"

        print(
            "PASS: Tracking URL detected as DUPLICATE_URL"
        )

        # --------------------------------------------------
        # 3. Different URL, same content
        # --------------------------------------------------

        duplicate_content, content_status = (
            await repository.create_news_deduplicated(
                url=(
                    "https://example.com/"
                    "phase7-dedup-test-002"
                ),
                title="Tin tức kiểm thử PostgreSQL",
                content=(
                    "Nội dung kiểm thử deduplication "
                    "cho PostgreSQL."
                ),
                source=TEST_SOURCE,
                category="Khoa học",
                decision_score=1.0,
            )
        )

        assert duplicate_content is None
        assert content_status == "DUPLICATE_CONTENT"

        print(
            "PASS: Same content detected as DUPLICATE_CONTENT"
        )

        # --------------------------------------------------
        # 4. Completely different article
        # --------------------------------------------------

        new_article, new_status = (
            await repository.create_news_deduplicated(
                url=(
                    "https://example.com/"
                    "phase7-dedup-test-003"
                ),
                title="Một bài báo hoàn toàn khác",
                content=(
                    "Nội dung hoàn toàn khác "
                    "với bài kiểm thử đầu tiên."
                ),
                source=TEST_SOURCE,
                category="Khoa học",
                decision_score=2.0,
            )
        )

        assert new_status == "CREATED"
        assert new_article is not None

        print(
            "PASS: Different article CREATED"
        )

        # --------------------------------------------------
        # 5. Verify database count
        # --------------------------------------------------

        result = await session.execute(
            select(News).where(
                News.source == TEST_SOURCE
            )
        )

        rows = list(result.scalars().all())

        assert len(rows) == 2

        print(
            "PASS: Database contains exactly "
            "2 unique test articles"
        )

        # --------------------------------------------------
        # Cleanup
        # --------------------------------------------------

        await session.execute(
            delete(News).where(
                News.source == TEST_SOURCE
            )
        )

        await session.commit()

        print(
            "PASS: Test records cleaned up"
        )

    print("=" * 60)
    print("SECTION 7.9.2 VALIDATION: PASS")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())