import asyncio
import os

import asyncpg

from src.intelligence.trend_service import (
    build_trend_record,
    sort_trends,
)


async def main():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set."
        )

    dsn = database_url.replace(
        "postgresql+asyncpg://",
        "postgresql://",
        1,
    )

    conn = await asyncpg.connect(dsn)

    try:
        print("=" * 100)
        print("KEYWORD AGGREGATION + TREND TEST v1.0")
        print("=" * 100)

        bounds = await conn.fetchrow(
            """
            SELECT
                MIN(DATE(n.published_at)) AS min_day,
                MAX(DATE(n.published_at)) AS max_day
            FROM keyword_occurrences k
            JOIN news n
                ON n.id = k.news_id
            WHERE n.published_at IS NOT NULL
            """
        )

        min_day = bounds["min_day"]
        max_day = bounds["max_day"]

        print(f"Corpus start: {min_day}")
        print(f"Corpus end:   {max_day}")

        rows = await conn.fetch(
            """
            WITH bounds AS (
                SELECT
                    MAX(DATE(n.published_at)) AS max_day
                FROM keyword_occurrences k
                JOIN news n
                    ON n.id = k.news_id
                WHERE n.published_at IS NOT NULL
            ),

            aggregated AS (
                SELECT
                    k.keyword,

                    (
                        ARRAY_AGG(
                            k.display_keyword
                            ORDER BY
                                k.frequency DESC,
                                k.final_score DESC
                        )
                    )[1] AS display_keyword,

                    COUNT(DISTINCT k.news_id)
                        AS total_articles,

                    SUM(k.frequency)
                        AS total_frequency,

                    SUM(k.final_score)
                        AS keyword_strength,

                    COUNT(DISTINCT k.news_id)
                        FILTER (
                            WHERE DATE(n.published_at)
                                BETWEEN
                                    b.max_day - INTERVAL '2 days'
                                    AND
                                    b.max_day
                        )
                        AS recent_articles,

                    COUNT(DISTINCT k.news_id)
                        FILTER (
                            WHERE DATE(n.published_at)
                                BETWEEN
                                    b.max_day - INTERVAL '5 days'
                                    AND
                                    b.max_day - INTERVAL '3 days'
                        )
                        AS previous_articles,

                    MAX(DATE(n.published_at))
                        AS last_seen,

                    b.max_day

                FROM keyword_occurrences k
                JOIN news n
                    ON n.id = k.news_id
                CROSS JOIN bounds b

                WHERE n.published_at IS NOT NULL

                GROUP BY
                    k.keyword,
                    b.max_day

                HAVING COUNT(DISTINCT k.news_id) >= 2
            )

            SELECT
                keyword,
                display_keyword,
                total_articles,
                total_frequency,
                keyword_strength,
                COALESCE(
                    recent_articles,
                    0
                ) AS recent_articles,
                COALESCE(
                    previous_articles,
                    0
                ) AS previous_articles,
                (
                    max_day - last_seen
                )::integer AS age_days

            FROM aggregated

            ORDER BY
                recent_articles DESC,
                total_articles DESC,
                keyword_strength DESC
            """
        )

        print(
            f"Trend candidates: {len(rows)}"
        )

        if not rows:
            print("No trend candidates.")
            return

        max_strength = max(
            float(row["keyword_strength"])
            for row in rows
        )

        records = [
            build_trend_record(
                dict(row),
                max_strength,
            )
            for row in rows
        ]

        records = sort_trends(records)

        print()
        print("-" * 115)
        print(
            f"{'Keyword':<32}"
            f"{'Recent':>8}"
            f"{'Prev':>8}"
            f"{'Total':>8}"
            f"{'Growth':>12}"
            f"{'Strength':>10}"
            f"{'Momentum':>10}"
            f"{'Trend':>10}"
        )
        print("-" * 115)

        for record in records[:30]:
            print(
                f"{record['display_keyword'][:31]:<32}"
                f"{record['recent_articles']:>8}"
                f"{record['previous_articles']:>8}"
                f"{record['total_articles']:>8}"
                f"{record['growth_label']:>12}"
                f"{record['strength_score']:>10.4f}"
                f"{record['momentum_score']:>10.4f}"
                f"{record['trend_score']:>10.4f}"
            )

        print("-" * 115)

        print()
        print("=" * 100)
        print("TREND TEST COMPLETED")
        print("=" * 100)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
