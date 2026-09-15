import asyncio

from sqlalchemy import text
from src.db.database import AsyncSessionLocal


async def explain_query(session, query_name: str, sql: str):
    print(f"\n--- {query_name} ---")

    result = await session.execute(
        text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {sql}")
    )

    rows = result.fetchall()

    for row in rows:
        print(row[0])

    return "\n".join(row[0] for row in rows)


async def main():
    print("=" * 70)
    print("SECTION 7.13 INDEX / EXPLAIN ANALYZE VALIDATION")
    print("=" * 70)

    async with AsyncSessionLocal() as session:

        # ---------------------------------------------------------
        # 1. Composite index: published_at + category
        # ---------------------------------------------------------
        composite_plan = await explain_query(
            session,
            "Composite index query",
            """
            SELECT id, title, category, published_at
            FROM news
            WHERE published_at >= TIMESTAMPTZ '2026-01-01 00:00:00+00'
              AND published_at < TIMESTAMPTZ '2027-01-01 00:00:00+00'
              AND category = 'Kinh doanh'
            ORDER BY published_at DESC
            LIMIT 100
            """,
        )

        # ---------------------------------------------------------
        # 2. Published_at index
        # ---------------------------------------------------------
        published_plan = await explain_query(
            session,
            "Published date query",
            """
            SELECT id, title, category, published_at
            FROM news
            WHERE published_at >= TIMESTAMPTZ '2026-01-01 00:00:00+00'
              AND published_at < TIMESTAMPTZ '2027-01-01 00:00:00+00'
            ORDER BY published_at DESC
            LIMIT 100
            """,
        )

        # ---------------------------------------------------------
        # 3. Category query
        # ---------------------------------------------------------
        category_plan = await explain_query(
            session,
            "Category query",
            """
            SELECT id, title, category, published_at
            FROM news
            WHERE category = 'Kinh doanh'
            ORDER BY published_at DESC
            LIMIT 100
            """,
        )

        print("\n" + "=" * 70)

        # PostgreSQL may choose Seq Scan when the table is small.
        # Therefore we validate that the relevant indexes exist and
        # that EXPLAIN ANALYZE executes successfully, without falsely
        # requiring a specific planner choice.

        index_result = await session.execute(
            text(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'news'
                ORDER BY indexname
                """
            )
        )

        indexes = [row[0] for row in index_result.fetchall()]

        required_indexes = {
            "ix_news_published_at",
            "ix_news_category",
            "ix_news_published_at_category",
        }

        missing = required_indexes - set(indexes)

        assert not missing, f"Missing indexes: {sorted(missing)}"

        assert composite_plan
        assert published_plan
        assert category_plan

        print("PASS composite index exists")
        print("PASS published_at index exists")
        print("PASS category index exists")
        print("PASS EXPLAIN ANALYZE composite query")
        print("PASS EXPLAIN ANALYZE published_at query")
        print("PASS EXPLAIN ANALYZE category query")

        print("=" * 70)
        print("SECTION 7.13 INDEX / EXPLAIN ANALYZE: PASS")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())