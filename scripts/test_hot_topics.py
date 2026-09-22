import asyncio
import os

import asyncpg

from src.intelligence.hot_topic_service import (
    build_cooccurrence_graph,
    build_hot_topic,
    find_topic_clusters,
    rank_hot_topics,
)
from src.intelligence.trend_service import (
    build_trend_record,
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
        print("HOT TOPIC TEST v1.0")
        print("=" * 100)

        # ---------------------------------------------------------
        # 1. Load keyword/article relations
        # ---------------------------------------------------------
        rows = await conn.fetch(
            """
            SELECT
                k.keyword,
                k.display_keyword,
                k.news_id
            FROM keyword_occurrences k
            ORDER BY k.keyword, k.news_id
            """
        )

        graph_rows = [
            {
                "keyword": row["keyword"],
                "display_keyword": row["display_keyword"],
                "news_id": row["news_id"],
            }
            for row in rows
        ]

        # ---------------------------------------------------------
        # 2. Build co-occurrence graph
        # ---------------------------------------------------------
        graph = build_cooccurrence_graph(
            graph_rows,
            min_overlap=2,
            min_jaccard=0.20,
        )

        clusters = find_topic_clusters(
            graph,
            min_cluster_size=2,
        )

        print(
            f"Keyword nodes: {len(graph)}"
        )

        print(
            f"Topic clusters: {len(clusters)}"
        )

        # ---------------------------------------------------------
        # 3. Load trend data
        # ---------------------------------------------------------
        trend_rows = await conn.fetch(
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
                                    AND b.max_day
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

                    (
                        b.max_day - MAX(
                            DATE(n.published_at)
                        )
                    )::integer AS age_days

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

            SELECT *
            FROM aggregated
            """
        )

        if not trend_rows:
            print("No trend data.")
            return

        max_strength = max(
            float(row["keyword_strength"])
            for row in trend_rows
        )

        trend_records = {}

        for row in trend_rows:
            record = build_trend_record(
                dict(row),
                max_strength,
            )

            trend_records[
                record["keyword"]
            ] = record

        # ---------------------------------------------------------
        # 4. Build topic objects
        # ---------------------------------------------------------
        topics = []

        for cluster in clusters:
            usable_keywords = [
                keyword
                for keyword in cluster
                if keyword in trend_records
            ]

            if len(usable_keywords) < 2:
                continue

            topic = build_hot_topic(
                usable_keywords,
                trend_records,
            )

            topics.append(topic)

        topics = rank_hot_topics(topics)

        # ---------------------------------------------------------
        # 5. Display
        # ---------------------------------------------------------
        print()

        for index, topic in enumerate(
            topics[:20],
            start=1,
        ):
            print(
                f"[{index}] {topic['label']}"
            )

            print(
                f"    Topic strength: "
                f"{topic['topic_strength']:.4f}"
            )

            print(
                f"    Trend max: "
                f"{topic['max_trend_score']:.4f}"
            )

            print(
                f"    Article volume: "
                f"{topic['article_volume']}"
            )

            print(
                "    Keywords:"
            )

            for keyword in topic["keywords"][:10]:
                display = trend_records[
                    keyword
                ]["display_keyword"]

                print(
                    f"      - {display}"
                )

            print()

        print("=" * 100)
        print("HOT TOPIC TEST COMPLETED")
        print("=" * 100)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
