import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete

from src.db.database import AsyncSessionLocal
from src.db.models import News
from src.db.repository import NewsRepository


TEST_PREFIX = "https://example.com/p2-phase7-14-test-"


async def cleanup():
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(News).where(News.url.like(f"{TEST_PREFIX}%"))
        )
        await session.commit()


async def main():
    print("=" * 70)
    print("SECTION 7.14 NULL / PAGINATION BOUNDARY VALIDATION")
    print("=" * 70)

    await cleanup()

    try:
        async with AsyncSessionLocal() as session:
            repo = NewsRepository(session)

            records = [
                {
                    "url": f"{TEST_PREFIX}1",
                    "title": "Published Article",
                    "content": "Published article test",
                    "source": "phase7-test",
                    "category": "Khoa học",
                    "decision_score": 1.0,
                    "published_at": datetime(
                        2026, 1, 10, tzinfo=timezone.utc
                    ),
                },
                {
                    "url": f"{TEST_PREFIX}2",
                    "title": "No Published Date",
                    "content": "Null published date test",
                    "source": "phase7-test",
                    "category": "Khoa học",
                    "decision_score": 0.9,
                    "published_at": None,
                },
                {
                    "url": f"{TEST_PREFIX}3",
                    "title": "Earlier Article",
                    "content": "Earlier article test",
                    "source": "phase7-test",
                    "category": "Khoa học",
                    "decision_score": 0.8,
                    "published_at": datetime(
                        2026, 1, 5, tzinfo=timezone.utc
                    ),
                },
            ]

            for record in records:
                news, status = await repo.create_news_deduplicated(**record)

                assert news is not None
                assert status == "CREATED"

            print("PASS test data inserted")

            # -----------------------------------------------------
            # 1. NULL published_at must not break latest query
            # -----------------------------------------------------
            latest = await repo.list_latest_news(limit=100)

            test_rows = [
                item
                for item in latest
                if item.url.startswith(TEST_PREFIX)
            ]

            assert len(test_rows) == 3

            published_rows = [
                item for item in test_rows
                if item.published_at is not None
            ]

            null_rows = [
                item for item in test_rows
                if item.published_at is None
            ]

            assert len(published_rows) == 2
            assert len(null_rows) == 1

            assert published_rows[0].published_at > published_rows[1].published_at

            print("PASS NULL published_at handling")

            # -----------------------------------------------------
            # 2. Pagination boundary
            # -----------------------------------------------------
            page_1 = await repo.list_latest_news(
                limit=1,
                offset=0,
            )

            page_2 = await repo.list_latest_news(
                limit=1,
                offset=1,
            )

            page_3 = await repo.list_latest_news(
                limit=1,
                offset=2,
            )

            test_page_ids = {
                page_1[0].id,
                page_2[0].id,
                page_3[0].id,
            }

            assert len(page_1) == 1
            assert len(page_2) == 1
            assert len(page_3) == 1
            assert len(test_page_ids) == 3

            print("PASS pagination boundary")

            # -----------------------------------------------------
            # 3. Offset beyond available rows
            # -----------------------------------------------------
            empty_page = await repo.list_latest_news(
                limit=10,
                offset=100000,
            )

            assert empty_page == []

            print("PASS offset beyond dataset")

        print("=" * 70)
        print("SECTION 7.14 NULL / PAGINATION BOUNDARY: PASS")
        print("=" * 70)

    finally:
        await cleanup()
        print("PASS test data cleanup")


if __name__ == "__main__":
    asyncio.run(main())