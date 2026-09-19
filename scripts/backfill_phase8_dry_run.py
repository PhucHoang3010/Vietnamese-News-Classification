from __future__ import annotations

import asyncio
import os

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from src.crawler.article_fetcher import AsyncArticleFetcher
from src.crawler.prediction_client import NewsPredictionClient
from src.db.deduplication import generate_content_hash


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured."
    )

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1,
    )


async def main() -> None:
    engine = create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

    SessionLocal = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async with SessionLocal() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    id,
                    url,
                    title,
                    category,
                    decision_score,
                    LENGTH(content) AS old_content_len
                FROM news
                ORDER BY id
                """
            )
        )

        rows = result.mappings().all()

    print("=" * 90)
    print("PHASE 8 BACKFILL DRY RUN")
    print("=" * 90)
    print(f"TOTAL ARTICLES: {len(rows)}")
    print("Concurrency: 1")
    print("DATABASE UPDATE: NO")
    print()

    # ---------------------------------------------------------
    # Sequential full-text fetch
    # ---------------------------------------------------------
    full_articles = []

    async with AsyncArticleFetcher(
        timeout_seconds=15.0,
        max_concurrency=1,
        max_content_chars=40_000,
    ) as fetcher:
        for row in rows:
            print(
                f"Fetching ID {row['id']}...",
                end=" ",
                flush=True,
            )

            try:
                article = await fetcher.fetch(
                    row["url"]
                )

                if not article.content:
                    print("FAILED")
                    full_articles.append(None)
                else:
                    print(
                        f"OK ({len(article.content)} chars)"
                    )
                    full_articles.append(article)

            except Exception as exc:
                print(
                    f"FAILED "
                    f"({type(exc).__name__})"
                )
                full_articles.append(None)

            await asyncio.sleep(0.5)

    # ---------------------------------------------------------
    # Prepare predictions
    # ---------------------------------------------------------
    prediction_inputs = []
    prediction_indexes = []

    for index, (row, article) in enumerate(
        zip(rows, full_articles, strict=True)
    ):
        if article is None:
            continue

        prediction_inputs.append(
            {
                "text": (
                    f"{row['title']}\n"
                    f"{article.content}"
                )
            }
        )

        prediction_indexes.append(index)

    predictions = {}

    async with httpx.AsyncClient() as http_client:
        client = NewsPredictionClient(
            http_client,
            base_url="http://fastapi:8000",
            timeout_seconds=30.0,
        )

        if prediction_inputs:
            results = await client.predict_batch(
                prediction_inputs
            )

            for index, prediction in zip(
                prediction_indexes,
                results,
                strict=True,
            ):
                predictions[index] = prediction

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------
    fulltext_success = 0
    fulltext_failed = 0
    changed = 0
    same = 0

    print()
    print("=" * 90)
    print("RESULTS")
    print("=" * 90)

    for index, row in enumerate(rows):
        article = full_articles[index]

        if article is None:
            fulltext_failed += 1
            continue

        fulltext_success += 1

        prediction = predictions.get(index)

        if not prediction:
            print(
                f"ID {row['id']} | "
                "PREDICTION FAILED"
            )
            continue

        new_label = prediction["label"]
        score = prediction["score"]

        marker = (
            "CHANGED"
            if new_label != row["category"]
            else "SAME"
        )

        if marker == "CHANGED":
            changed += 1
        else:
            same += 1

        print(
            f"ID {row['id']:>3} | "
            f"{row['category']} -> {new_label} | "
            f"{row['old_content_len']} -> "
            f"{len(article.content)} chars | "
            f"score={score:.6f} | {marker}"
        )

        new_hash = generate_content_hash(
            row["title"],
            article.content,
        )["content_hash"]

        # Only calculate/print hash.
        # DO NOT update database.
        _ = new_hash

    print()
    print("=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(
        f"TOTAL              : {len(rows)}"
    )
    print(
        f"FULLTEXT SUCCESS   : {fulltext_success}"
    )
    print(
        f"FULLTEXT FAILED    : {fulltext_failed}"
    )
    print(
        f"CATEGORY CHANGED   : {changed}"
    )
    print(
        f"CATEGORY SAME      : {same}"
    )
    print()
    print(
        "NO DATABASE UPDATE WAS PERFORMED."
    )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())