from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Date, cast, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.db.models import News


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


def build_filters(
    from_date: date | None,
    to_date: date | None,
    category: str | None,
    source: str | None,
    content_source: str | None,
):

    trend_date = cast(
        func.coalesce(
            News.published_at,
            News.crawled_at,
        ),
        Date,
    )

    conditions = []

    if from_date:
        conditions.append(trend_date >= from_date)

    if to_date:
        conditions.append(trend_date <= to_date)

    if category:
        conditions.append(News.category == category)

    if source:
        conditions.append(News.source == source)

    if content_source:
        conditions.append(News.content_source == content_source)

    return trend_date, conditions


@router.get("/summary")
async def analytics_summary(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    content_source: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    _, conditions = build_filters(
        from_date,
        to_date,
        category,
        source,
        content_source,
    )

    total_articles = (
        await db.scalar(
            select(func.count(News.id)).where(*conditions)
        )
    ) or 0

    total_categories = (
        await db.scalar(
            select(func.count(distinct(News.category)))
            .where(*conditions)
        )
    ) or 0

    total_sources = (
        await db.scalar(
            select(func.count(distinct(News.source)))
            .where(*conditions)
        )
    ) or 0

    fulltext_articles = (
        await db.scalar(
            select(func.count(News.id))
            .where(*conditions)
            .where(News.content_source == "fulltext")
        )
    ) or 0

    fallback_articles = (
        await db.scalar(
            select(func.count(News.id))
            .where(*conditions)
            .where(News.content_source == "rss_fallback")
        )
    ) or 0

    latest_crawled_at = await db.scalar(
        select(func.max(News.crawled_at)).where(*conditions)
    )

    return {
        "total_articles": int(total_articles),
        "total_categories": int(total_categories),
        "total_sources": int(total_sources),
        "fulltext_articles": int(fulltext_articles),
        "rss_fallback_articles": int(fallback_articles),
        "latest_crawled_at": latest_crawled_at,
    }


@router.get("/categories")
async def analytics_categories(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    content_source: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    _, conditions = build_filters(
        from_date,
        to_date,
        category,
        source,
        content_source,
    )

    total_articles = (
        await db.scalar(
            select(func.count(News.id)).where(*conditions)
        )
    ) or 0

    result = await db.execute(
        select(
            News.category,
            func.count(News.id).label("total"),
        )
        .where(*conditions)
        .group_by(News.category)
        .order_by(func.count(News.id).desc())
    )

    rows = result.all()

    items = []

    for row in rows:
        total = int(row.total)

        percentage = (
            round((total / total_articles) * 100, 2)
            if total_articles
            else 0.0
        )

        items.append(
            {
                "category": row.category,
                "total": total,
                "percentage": percentage,
            }
        )

    return {
        "total_articles": int(total_articles),
        "items": items,
    }


@router.get("/daily")
async def analytics_daily(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    content_source: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    trend_date, conditions = build_filters(
        from_date,
        to_date,
        category,
        source,
        content_source,
    )

    result = await db.execute(
        select(
            trend_date.label("day"),
            func.count(News.id).label("total"),
        )
        .where(*conditions)
        .group_by(trend_date)
        .order_by(trend_date.asc())
    )

    rows = result.all()

    return {
        "items": [
            {
                "day": row.day.isoformat(),
                "total": int(row.total),
            }
            for row in rows
        ]
    }


@router.get("/sources")
async def analytics_sources(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    content_source: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    _, conditions = build_filters(
        from_date,
        to_date,
        category,
        source,
        content_source,
    )

    result = await db.execute(
        select(
            News.source,
            func.count(News.id).label("total"),
        )
        .where(*conditions)
        .group_by(News.source)
        .order_by(func.count(News.id).desc())
    )

    rows = result.all()

    return {
        "items": [
            {
                "source": row.source,
                "total": int(row.total),
            }
            for row in rows
        ]
    }


@router.get("/content-sources")
async def analytics_content_sources(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    content_source: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    _, conditions = build_filters(
        from_date,
        to_date,
        category,
        source,
        content_source,
    )

    result = await db.execute(
        select(
            News.content_source,
            func.count(News.id).label("total"),
        )
        .where(*conditions)
        .group_by(News.content_source)
        .order_by(func.count(News.id).desc())
    )

    rows = result.all()

    return {
        "items": [
            {
                "content_source": row.content_source,
                "total": int(row.total),
            }
            for row in rows
        ]
    }


@router.get("/trend-by-category")
async def analytics_trend_by_category(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    content_source: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    trend_date, conditions = build_filters(
        from_date,
        to_date,
        category,
        source,
        content_source,
    )

    result = await db.execute(
        select(
            trend_date.label("day"),
            News.category,
            func.count(News.id).label("total"),
        )
        .where(*conditions)
        .group_by(trend_date, News.category)
        .order_by(
            trend_date.asc(),
            func.count(News.id).desc(),
        )
    )

    rows = result.all()

    grouped = {}

    for row in rows:
        day = row.day.isoformat()

        if day not in grouped:
            grouped[day] = {
                "day": day,
                "categories": {},
                "total": 0,
            }

        total = int(row.total)

        grouped[day]["categories"][row.category] = total
        grouped[day]["total"] += total

    return {
        "items": list(grouped.values())
    }


@router.get("/recent")
async def analytics_recent(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    content_source: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    sort_date = func.coalesce(
        News.published_at,
        News.crawled_at,
    )

    filter_date = cast(sort_date, Date)

    conditions = []

    if from_date:
        conditions.append(filter_date >= from_date)

    if to_date:
        conditions.append(filter_date <= to_date)

    if category:
        conditions.append(News.category == category)

    if source:
        conditions.append(News.source == source)

    if content_source:
        conditions.append(News.content_source == content_source)

    result = await db.execute(
        select(
            News.id,
            News.title,
            News.category,
            News.source,
            News.content_source,
            News.decision_score,
            News.published_at,
            News.crawled_at,
            News.url,
        )
        .where(*conditions)
        .order_by(sort_date.desc())
        .limit(limit)
    )

    rows = result.mappings().all()

    return {
        "count": len(rows),
        "items": [
            {
                "id": row["id"],
                "title": row["title"],
                "category": row["category"],
                "source": row["source"],
                "content_source": row["content_source"],
                "decision_score": row["decision_score"],
                "published_at": (
                    row["published_at"].isoformat()
                    if row["published_at"]
                    else None
                ),
                "crawled_at": (
                    row["crawled_at"].isoformat()
                    if row["crawled_at"]
                    else None
                ),
                "url": row["url"],
            }
            for row in rows
        ],
    }
