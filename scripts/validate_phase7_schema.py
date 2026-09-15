import asyncio

from sqlalchemy import text

from src.db.database import engine


async def main():
    async with engine.connect() as conn:
        print("=" * 60)
        print("PHASE 7 — SECTION 7.6")
        print("POSTGRESQL SCHEMA VALIDATION")
        print("=" * 60)

        table_result = await conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'news'
                """
            )
        )

        table = table_result.scalar_one_or_none()

        if table != "news":
            raise RuntimeError("news table not found.")

        print("Table news       : PASS")

        columns_result = await conn.execute(
            text(
                """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'news'
                ORDER BY ordinal_position
                """
            )
        )

        columns = columns_result.fetchall()

        print(f"Column count     : {len(columns)}")

        for row in columns:
            print(
                f"  {row.column_name:18}"
                f" type={row.data_type:25}"
                f" nullable={row.is_nullable}"
                f" default={row.column_default}"
            )

        expected_columns = {
            "id",
            "url",
            "content_hash",
            "title",
            "content",
            "source",
            "category",
            "decision_score",
            "published_at",
            "crawled_at",
        }

        actual_columns = {row.column_name for row in columns}

        if actual_columns != expected_columns:
            raise RuntimeError(
                f"Column mismatch.\n"
                f"Expected: {expected_columns}\n"
                f"Actual: {actual_columns}"
            )

        print("Columns          : PASS")

        index_result = await conn.execute(
            text(
                """
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename = 'news'
                ORDER BY indexname
                """
            )
        )

        indexes = index_result.fetchall()

        print("Indexes:")

        for row in indexes:
            print(f"  {row.indexname}")
            print(f"    {row.indexdef}")

        required_indexes = {
            "ix_news_category",
            "ix_news_published_at",
            "ix_news_published_at_category",
        }

        actual_indexes = {row.indexname for row in indexes}

        missing_indexes = required_indexes - actual_indexes

        if missing_indexes:
            raise RuntimeError(
                f"Missing indexes: {missing_indexes}"
            )

        print("Required indexes : PASS")

        constraint_result = await conn.execute(
            text(
                """
                SELECT
                    tc.constraint_name,
                    tc.constraint_type
                FROM information_schema.table_constraints tc
                WHERE tc.table_schema = 'public'
                  AND tc.table_name = 'news'
                ORDER BY tc.constraint_name
                """
            )
        )

        constraints = constraint_result.fetchall()

        print("Constraints:")

        for row in constraints:
            print(
                f"  {row.constraint_name}"
                f" -> {row.constraint_type}"
            )

        print("Constraints      : PASS")

        print("=" * 60)
        print("SECTION 7.6 SCHEMA VALIDATION: PASS")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())