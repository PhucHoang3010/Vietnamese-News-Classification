import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from src.db.database import AsyncSessionLocal
from src.db.models import News
from src.db.repository import NewsRepository


TEST_PREFIX = "https://example.com/p2-phase7-12-test-"


async def cleanup_test_data():
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(News).where(News.url.like(f"{TEST_PREFIX}%"))
        )
        await session.commit()


async def insert_test_data():
    base_time = datetime(2026, 1, 10, 8, 0, tzinfo=timezone.utc)

    records = [
        {
            "url": f"{TEST_PREFIX}1",
            "title": "Phase 7.12 Test Business",
            "content": "Test content business one",
            "source": "phase7-test",
            "category": "Kinh doanh",
            "decision_score": 1.1,
            "published_at": base_time + timedelta(days=2),
        },
        {
            "url": f"{TEST_PREFIX}2",
            "title": "Phase 7.12 Test Education",
            "content": "Test content education one",
            "source": "phase7-test",
            "category": "Giáo dục",
            "decision_score": 0.8,
            "published_at": base_time + timedelta(days=1),
        },
        {
            "url": f"{TEST_PREFIX}3",
            "title": "Phase 7.12 Test Business Two",
            "content": "Test content business two",
            "source": "phase7-test",
            "category": "Kinh doanh",
            "decision_score": 1.5,
            "published_at": base_time,
        },
    ]

    async with AsyncSessionLocal() as session:
        repo = NewsRepository(session)

        for record in records:
            news, status = await repo.create_news_deduplicated(**record)

            assert news is not None, (
                f"Failed to insert {record['url']}: {status}"
            )
            assert status == "CREATED"

    return base_time


async def test_queries(base_time: datetime):
    async with AsyncSessionLocal() as session:
        repo = NewsRepository(session)

        # ---------------------------------------------------------
        # 1. Latest news
        # ---------------------------------------------------------
        latest = await repo.list_latest_news(limit=3)

        test_latest = [
            item for item in latest
            if item.url.startswith(TEST_PREFIX)
        ]

        assert len(test_latest) == 3
        assert test_latest[0].category == "Kinh doanh"
        assert test_latest[0].published_at > test_latest[1].published_at

        print("PASS latest news query")

        # ---------------------------------------------------------
        # 2. Category filter
        # ---------------------------------------------------------
        business_news = await repo.list_news_by_category(
            category="Kinh doanh",
            limit=100,
        )

        test_business = [
            item
            for item in business_news
            if item.url.startswith(TEST_PREFIX)
        ]

        assert len(test_business) == 2
        assert all(
            item.category == "Kinh doanh"
            for item in test_business
        )

        print("PASS category filter")

        # ---------------------------------------------------------
        # 3. Published date range
        # ---------------------------------------------------------
        start_at = base_time
        end_at = base_time + timedelta(days=2)

        range_news = await repo.list_news_by_published_range(
            start_at=start_at,
            end_at=end_at,
            limit=100,
        )

        test_range = [
            item
            for item in range_news
            if item.url.startswith(TEST_PREFIX)
        ]

        assert len(test_range) == 2

        print("PASS published date range")

        # ---------------------------------------------------------
        # 4. Category trend count
        # ---------------------------------------------------------
        trend = await repo.count_news_by_category(
            start_at=base_time,
            end_at=base_time + timedelta(days=3),
        )

        trend_dict = dict(trend)

        assert trend_dict.get("Kinh doanh") == 2
        assert trend_dict.get("Giáo dục") == 1

        print("PASS category trend count")

        # ---------------------------------------------------------
        # 5. Pagination
        # ---------------------------------------------------------
        page_1 = await repo.list_latest_news(limit=1, offset=0)
        page_2 = await repo.list_latest_news(limit=1, offset=1)

        assert len(page_1) == 1
        assert len(page_2) == 1
        assert page_1[0].id != page_2[0].id

        print("PASS pagination")


async def main():
    print("=" * 60)
    print("SECTION 7.12 NEWS QUERY VALIDATION")
    print("=" * 60)

    await cleanup_test_data()

    try:
        base_time = await insert_test_data()

        print("PASS test data inserted")

        await test_queries(base_time)

        print("=" * 60)
        print("SECTION 7.12 NEWS QUERY REPOSITORY: PASS")
        print("=" * 60)

    finally:
        await cleanup_test_data()
        print("PASS test data cleanup")


if __name__ == "__main__":
    asyncio.run(main())