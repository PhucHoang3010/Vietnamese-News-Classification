import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env", override=True)

from src.db.database import engine
from src.db.models import News
from src.db.repository import NewsRepository


TEST_URL = "https://example.com/concurrent-dedup-test"
TEST_TITLE = "Concurrent dedup test"
TEST_CONTENT = (
    "This is a temporary article used to validate concurrent "
    "deduplication in PostgreSQL."
)
TEST_SOURCE = "phase7-test"
TEST_CATEGORY = "Khoa học"
TEST_SCORE = 1.0


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def cleanup_test_data() -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(News).where(
                News.url == TEST_URL
            )
        )
        await session.commit()


async def create_test_article(worker_id: int):
    async with AsyncSessionLocal() as session:
        repository = NewsRepository(session)

        news, status = await repository.create_news_deduplicated(
            url=TEST_URL,
            title=TEST_TITLE,
            content=TEST_CONTENT,
            source=TEST_SOURCE,
            category=TEST_CATEGORY,
            decision_score=TEST_SCORE,
            published_at=datetime.now(timezone.utc),
        )

        return worker_id, news, status


async def main():
    print("PHASE 7.11 — CONCURRENT DEDUP TEST")
    print("=" * 80)

    # -----------------------------------------------------
    # Cleanup
    # -----------------------------------------------------

    await cleanup_test_data()

    print("PASS: Old concurrent test data cleaned")


    # -----------------------------------------------------
    # Run concurrent inserts
    # -----------------------------------------------------

    print()
    print("Running 10 concurrent insert attempts...")

    results = await asyncio.gather(
        *[
            create_test_article(worker_id)
            for worker_id in range(1, 11)
        ],
        return_exceptions=True,
    )


    # -----------------------------------------------------
    # Validate task execution
    # -----------------------------------------------------

    exceptions = [
        result
        for result in results
        if isinstance(result, Exception)
    ]

    if exceptions:
        print()
        print("ERROR: Unexpected exceptions detected")

        for exception in exceptions:
            print(type(exception).__name__, exception)

        raise AssertionError(
            "Concurrent dedup test produced unexpected exceptions."
        )

    print("PASS: All concurrent tasks completed")


    # -----------------------------------------------------
    # Inspect statuses
    # -----------------------------------------------------

    successful_results = [
        result
        for result in results
        if not isinstance(result, Exception)
    ]

    statuses = [
        result[2]
        for result in successful_results
    ]

    print()
    print("Worker results:")
    for worker_id, news, status in successful_results:
        news_id = news.id if news is not None else None

        print(
            f"  Worker {worker_id:02d}: "
            f"status={status}, "
            f"news_id={news_id}"
        )


    # -----------------------------------------------------
    # Exactly one CREATED
    # -----------------------------------------------------

    created_count = statuses.count("CREATED")

    assert created_count == 1, (
        f"Expected exactly 1 CREATED result, "
        f"got {created_count}"
    )

    print()
    print("PASS: Exactly one article was CREATED")


    # -----------------------------------------------------
    # Remaining attempts must be duplicates
    # -----------------------------------------------------

    duplicate_statuses = {
        "DUPLICATE_URL",
        "DUPLICATE_CONTENT",
        "DUPLICATE_CONSTRAINT",
    }

    duplicate_count = sum(
        status in duplicate_statuses
        for status in statuses
    )

    assert duplicate_count == 9, (
        f"Expected 9 duplicate results, "
        f"got {duplicate_count}"
    )

    print("PASS: Remaining 9 attempts were rejected as duplicates")


    # -----------------------------------------------------
    # Validate actual database state
    # -----------------------------------------------------

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(News).where(
                News.url == TEST_URL
            )
        )

        rows = list(result.scalars().all())

    print()
    print(f"Database rows for test URL: {len(rows)}")

    assert len(rows) == 1

    print("PASS: PostgreSQL contains exactly one record")


    # -----------------------------------------------------
    # Cleanup
    # -----------------------------------------------------

    await cleanup_test_data()

    print()
    print("PASS: Concurrent test data cleaned")


    # -----------------------------------------------------
    # Final result
    # -----------------------------------------------------

    print()
    print("=" * 80)
    print("SECTION 7.11 CONCURRENT DEDUP: PASS")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())