import asyncio

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from src.db.database import AsyncSessionLocal
from src.db.models import News


TEST_URL = "https://example.com/p2-phase7-15-integrity"
TEST_HASH = "a" * 64


async def cleanup():
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(News).where(
                News.url.in_(
                    [
                        TEST_URL,
                        "https://example.com/p2-phase7-15-other-url",
                        "https://example.com/p2-phase7-15-invalid",
                    ]
                )
            )
        )
        await session.commit()


async def main():
    print("=" * 70)
    print("SECTION 7.15 DATA INTEGRITY / TRANSACTION VALIDATION")
    print("=" * 70)

    await cleanup()

    # ---------------------------------------------------------
    # TEST 1: Valid insert
    # ---------------------------------------------------------
    async with AsyncSessionLocal() as session:
        news = News(
            url=TEST_URL,
            content_hash=TEST_HASH,
            title="Integrity Test",
            content="Integrity test content",
            source="phase7-test",
            category="Khoa học",
            decision_score=1.0,
        )

        session.add(news)
        await session.commit()

        assert news.id is not None

        print("PASS valid insert")

    # ---------------------------------------------------------
    # TEST 2: UNIQUE URL
    # ---------------------------------------------------------
    duplicate_url_failed = False

    async with AsyncSessionLocal() as session:
        duplicate = News(
            url=TEST_URL,
            content_hash="b" * 64,
            title="Duplicate URL",
            content="Duplicate URL test",
            source="phase7-test",
            category="Khoa học",
            decision_score=0.5,
        )

        session.add(duplicate)

        try:
            await session.commit()
        except IntegrityError:
            duplicate_url_failed = True
            await session.rollback()

    assert duplicate_url_failed

    print("PASS UNIQUE URL constraint")

    # ---------------------------------------------------------
    # TEST 3: UNIQUE content_hash
    # ---------------------------------------------------------
    duplicate_hash_failed = False

    async with AsyncSessionLocal() as session:
        duplicate = News(
            url="https://example.com/p2-phase7-15-other-url",
            content_hash=TEST_HASH,
            title="Duplicate Hash",
            content="Duplicate hash test",
            source="phase7-test",
            category="Khoa học",
            decision_score=0.5,
        )

        session.add(duplicate)

        try:
            await session.commit()
        except IntegrityError:
            duplicate_hash_failed = True
            await session.rollback()

    assert duplicate_hash_failed

    print("PASS UNIQUE content_hash constraint")

    # ---------------------------------------------------------
    # TEST 4: NOT NULL
    # ---------------------------------------------------------
    not_null_failed = False

    async with AsyncSessionLocal() as session:
        invalid = News(
            url="https://example.com/p2-phase7-15-invalid",
            content_hash="c" * 64,
            title=None,
            content="Invalid NOT NULL test",
            source="phase7-test",
            category="Khoa học",
            decision_score=0.5,
        )

        session.add(invalid)

        try:
            await session.commit()
        except IntegrityError:
            not_null_failed = True
            await session.rollback()

    assert not_null_failed

    print("PASS NOT NULL constraint")

    # ---------------------------------------------------------
    # TEST 5: Rollback preserves valid record
    # ---------------------------------------------------------
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(News).where(News.url == TEST_URL)
        )

        rows = list(result.scalars().all())

        assert len(rows) == 1
        assert rows[0].title == "Integrity Test"

    print("PASS rollback preserved valid record")

    # ---------------------------------------------------------
    # CLEANUP
    # ---------------------------------------------------------
    await cleanup()

    print("=" * 70)
    print("SECTION 7.15 DATA INTEGRITY / TRANSACTION: PASS")
    print("=" * 70)
    print("PASS test data cleanup")


if __name__ == "__main__":
    asyncio.run(main())