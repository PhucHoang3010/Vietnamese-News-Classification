from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.intelligence.hot_topic_service import (
    build_cooccurrence_graph,
    build_hot_topic,
    find_topic_clusters,
    rank_hot_topics,
)
from src.intelligence.trend_service import (
    build_trend_record,
    sort_trends,
)


router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
)


def build_common_filters(
    from_date: date | None,
    to_date: date | None,
    category: str | None,
    source: str | None,
    content_source: str | None,
):
    conditions = [
        "n.published_at IS NOT NULL"
    ]

    params: dict[str, Any] = {}

    date_expr = (
        "CAST(COALESCE(n.published_at, n.crawled_at) AS DATE)"
    )

    if from_date:
        conditions.append(
            f"{date_expr} >= :from_date"
        )
        params["from_date"] = from_date

    if to_date:
        conditions.append(
            f"{date_expr} <= :to_date"
        )
        params["to_date"] = to_date

    if category:
        conditions.append(
            "n.category = :category"
        )
        params["category"] = category

    if source:
        conditions.append(
            "n.source = :source"
        )
        params["source"] = source

    if content_source:
        conditions.append(
            "n.content_source = :content_source"
        )
        params["content_source"] = content_source

    return conditions, params, date_expr


async def get_trend_rows(
    db: AsyncSession,
    keyword: str | None,
    from_date: date | None,
    to_date: date | None,
    category: str | None,
    source: str | None,
    content_source: str | None,
    recent_days: int,
    previous_days: int,
    min_articles: int,
):
    date_expr = """
        CAST(
            COALESCE(n.published_at, n.crawled_at)
            AS DATE
        )
    """

    where_clauses = [
        "1 = 1"
    ]

    params = {
        "min_articles": min_articles,
        "recent_days": recent_days,
        "previous_days": previous_days,
    }

    if keyword:
        where_clauses.append(
            "LOWER(k.keyword) LIKE LOWER(:keyword)"
        )
        params["keyword"] = f"%{keyword}%"

    if from_date:
        where_clauses.append(
            f"{date_expr} >= :from_date"
        )
        params["from_date"] = from_date

    if to_date:
        where_clauses.append(
            f"{date_expr} <= :to_date"
        )
        params["to_date"] = to_date

    if category:
        where_clauses.append(
            "n.category = :category"
        )
        params["category"] = category

    if source:
        where_clauses.append(
            "n.source = :source"
        )
        params["source"] = source

    if content_source:
        where_clauses.append(
            "n.content_source = :content_source"
        )
        params["content_source"] = content_source

    where_sql = " AND ".join(where_clauses)

    sql = text(
        f"""
        WITH base AS (
            SELECT
                k.keyword,
                MAX(k.display_keyword) AS display_keyword,
                k.news_id,
                k.frequency,
                k.final_score,
                {date_expr} AS article_day
            FROM keyword_occurrences k
            JOIN news n
                ON n.id = k.news_id
            WHERE {where_sql}
            GROUP BY
                k.keyword,
                k.news_id,
                k.frequency,
                k.final_score,
                article_day
        ),

        bounds AS (
            SELECT
                MAX(article_day) AS anchor_day
            FROM base
        ),

        aggregated AS (
            SELECT
                b.keyword,
                MAX(b.display_keyword) AS display_keyword,

                COUNT(DISTINCT b.news_id)
                    AS total_articles,

                SUM(b.frequency)
                    AS total_frequency,

                SUM(b.final_score)
                    AS keyword_strength,

                COUNT(
                    DISTINCT CASE
                        WHEN b.article_day >= (
                            bounds.anchor_day
                            - (:recent_days - 1)
                        )
                        THEN b.news_id
                    END
                ) AS recent_articles,

                COUNT(
                    DISTINCT CASE
                        WHEN b.article_day < (
                            bounds.anchor_day
                            - (:recent_days - 1)
                        )
                        AND b.article_day >= (
                            bounds.anchor_day
                            - (
                                :recent_days
                                + :previous_days
                                - 1
                            )
                        )
                        THEN b.news_id
                    END
                ) AS previous_articles,

                MAX(
                    bounds.anchor_day - b.article_day
                ) AS age_days

            FROM base b
            CROSS JOIN bounds

            GROUP BY
                b.keyword

            HAVING
                COUNT(DISTINCT b.news_id) >= :min_articles
        )

        SELECT
            keyword,
            display_keyword,
            total_articles,
            total_frequency,
            keyword_strength,
            recent_articles,
            previous_articles,
            age_days,
            (SELECT anchor_day FROM bounds) AS anchor_day

        FROM aggregated

        ORDER BY
            keyword_strength DESC,
            total_articles DESC,
            recent_articles DESC
        """
    )

    result = await db.execute(sql, params)

    return result.mappings().all()


@router.get(
    "/keywords",
    summary="Get aggregated keywords",
)
async def intelligence_keywords(
    keyword: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    content_source: str | None = Query(default=None),
    min_articles: int = Query(default=1, ge=1, le=100),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    conditions, params, _ = build_common_filters(
        from_date,
        to_date,
        category,
        source,
        content_source,
    )

    if keyword:
        conditions.append(
            "k.keyword ILIKE :keyword"
        )
        params["keyword"] = f"%{keyword}%"

    where_sql = " AND ".join(
        conditions
    )

    params["min_articles"] = min_articles
    params["limit"] = limit

    result = await db.execute(
        text(
            f"""
            SELECT
                k.keyword,
                MAX(k.display_keyword)
                    AS display_keyword,
                COUNT(DISTINCT k.news_id)
                    AS article_count,
                SUM(k.frequency)
                    AS total_frequency,
                SUM(k.final_score)
                    AS strength

            FROM keyword_occurrences k

            JOIN news n
                ON n.id = k.news_id

            WHERE {where_sql}

            GROUP BY k.keyword

            HAVING COUNT(DISTINCT k.news_id)
                >= :min_articles

            ORDER BY
                article_count DESC,
                total_frequency DESC,
                strength DESC

            LIMIT :limit
            """
        ),
        params,
    )

    rows = result.mappings().all()

    return {
        "count": len(rows),
        "items": [
            {
                "keyword": row["keyword"],
                "display_keyword": row["display_keyword"],
                "article_count": int(
                    row["article_count"]
                ),
                "total_frequency": int(
                    row["total_frequency"]
                ),
                "strength": float(
                    row["strength"] or 0
                ),
            }
            for row in rows
        ],
    }


@router.get(
    "/trends",
    summary="Get keyword trends",
)
async def intelligence_trends(
    keyword: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    content_source: str | None = Query(default=None),
    recent_days: int = Query(
        default=3,
        ge=2,
        le=14,
    ),
    previous_days: int = Query(
        default=3,
        ge=2,
        le=14,
    ),
    min_articles: int = Query(
        default=2,
        ge=1,
        le=100,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: AsyncSession = Depends(get_db),
):
    rows = await get_trend_rows(
        db=db,
        keyword=keyword,
        from_date=from_date,
        to_date=to_date,
        category=category,
        source=source,
        content_source=content_source,
        recent_days=recent_days,
        previous_days=previous_days,
        min_articles=min_articles,
    )

    if not rows:
        return {
            "count": 0,
            "recent_days": recent_days,
            "previous_days": previous_days,
            "anchor_date": None,
            "items": [],
        }

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

    records = sort_trends(
        records
    )[:limit]

    return {
        "count": len(records),
        "recent_days": recent_days,
        "previous_days": previous_days,
        "anchor_date": rows[0]["anchor_day"].isoformat() if rows and rows[0]["anchor_day"] else None,
        "items": records,
    }


@router.get(
    "/hot-topics",
    summary="Get hot topic candidates",
)
async def intelligence_hot_topics(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    content_source: str | None = Query(default=None),
    recent_days: int = Query(
        default=3,
        ge=2,
        le=14,
    ),
    previous_days: int = Query(
        default=3,
        ge=2,
        le=14,
    ),
    min_articles: int = Query(
        default=2,
        ge=1,
        le=100,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
    db: AsyncSession = Depends(get_db),
):
    trend_rows = await get_trend_rows(
        db=db,
        keyword=None,
        from_date=from_date,
        to_date=to_date,
        category=category,
        source=source,
        content_source=content_source,
        recent_days=recent_days,
        previous_days=previous_days,
        min_articles=min_articles,
    )

    if not trend_rows:
        return {
            "count": 0,
            "anchor_date": None,
            "recent_days": recent_days,
            "items": [],
        }

    max_strength = max(
        float(row["keyword_strength"])
        for row in trend_rows
    )

    trend_records_list = [
        build_trend_record(
            dict(row),
            max_strength,
        )
        for row in trend_rows
    ]

    trend_records = {
        record["keyword"]: record
        for record in trend_records_list
    }

    trend_keywords = list(
        trend_records.keys()
    )

    placeholders = []

    keyword_params: dict[str, Any] = {}

    for index, value in enumerate(
        trend_keywords
    ):
        key = f"kw_{index}"
        placeholders.append(
            f":{key}"
        )
        keyword_params[key] = value

    conditions, base_params, _ = build_common_filters(
        from_date,
        to_date,
        category,
        source,
        content_source,
    )

    where_sql = " AND ".join(
        conditions
    )

    relation_result = await db.execute(
        text(
            f"""
            SELECT
                k.keyword,
                MAX(k.display_keyword)
                    AS display_keyword,
                k.news_id

            FROM keyword_occurrences k

            JOIN news n
                ON n.id = k.news_id

            WHERE {where_sql}
              AND k.keyword IN (
                  {", ".join(placeholders)}
              )

            GROUP BY
                k.keyword,
                k.news_id
            """
        ),
        {
            **base_params,
            **keyword_params,
        },
    )

    relation_rows = [
        {
            "keyword": row["keyword"],
            "display_keyword": row["display_keyword"],
            "news_id": row["news_id"],
        }
        for row in relation_result.mappings().all()
    ]

    graph = build_cooccurrence_graph(
        relation_rows,
        min_overlap=2,
        min_jaccard=0.20,
    )

    clusters = find_topic_clusters(
        graph,
        min_cluster_size=2,
    )

    topics = []

    for cluster in clusters:
        usable = [
            keyword
            for keyword in cluster
            if keyword in trend_records
        ]

        if len(usable) < 2:
            continue

        topics.append(
            build_hot_topic(
                usable,
                trend_records,
            )
        )

    topics = rank_hot_topics(
        topics
    )[:limit]

    return {
        "count": len(topics),
        "anchor_date": (
            trend_rows[0]["anchor_day"].isoformat()
            if trend_rows and trend_rows[0]["anchor_day"]
            else None
        ),
        "recent_days": recent_days,
        "items": topics,
    }



