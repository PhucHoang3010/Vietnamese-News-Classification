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

    # ---------------------------------------------------------
    # Load current DB rows
    # ---------------------------------------------------------
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
                    content_hash,
                    LENGTH(content) AS old_content_len
                FROM news
                ORDER BY id
                """
            )
        )

        rows = result.mappings().all()

    print("=" * 90)
    print("PHASE 8 BACKFILL COMMIT")
    print("=" * 90)
    print(f"TOTAL ARTICLES: {len(rows)}")
    print("FULLTEXT CONCURRENCY: 1")
    print()

    # ---------------------------------------------------------
    # Fetch full articles sequentially
    # ---------------------------------------------------------
    successful_articles = []
    failed_fetches = []

    async with AsyncArticleFetcher(
        timeout_seconds=15.0,
        max_concurrency=1,
        max_content_chars=40_000,
    ) as fetcher:

        for current, row in enumerate(
            rows,
            start=1,
        ):
            print(
                f"[{current}/{len(rows)}] "
                f"ID {row['id']}...",
                end=" ",
                flush=True,
            )

            try:
                article = await fetcher.fetch(
                    row["url"]
                )

                if not article.content:
                    print("FETCH_FAILED")
                    failed_fetches.append(
                        row["id"]
                    )
                    continue

                print(
                    f"OK "
                    f"({len(article.content)} chars)"
                )

                successful_articles.append(
                    {
                        "row": row,
                        "article": article,
                    }
                )

            except Exception as exc:
                print(
                    f"FETCH_FAILED "
                    f"({type(exc).__name__})"
                )

                failed_fetches.append(
                    row["id"]
                )

            await asyncio.sleep(0.5)

    print()
    print(
        f"FULLTEXT SUCCESS: "
        f"{len(successful_articles)}"
    )

    print(
        f"FULLTEXT FAILED: "
        f"{len(failed_fetches)}"
    )

    if not successful_articles:
        print("Nothing to update.")
        await engine.dispose()
        return

    # ---------------------------------------------------------
    # Prediction through real FastAPI
    # ---------------------------------------------------------
    prediction_inputs = []

    for item in successful_articles:
        row = item["row"]
        article = item["article"]

        prediction_inputs.append(
            {
                "text": (
                    f"{row['title']}\n"
                    f"{article.content}"
                )
            }
        )

    async with httpx.AsyncClient() as http_client:

        prediction_client = NewsPredictionClient(
            http_client,
            base_url="http://fastapi:8000",
            timeout_seconds=30.0,
        )

        predictions = (
            await prediction_client.predict_batch(
                prediction_inputs
            )
        )

    # ---------------------------------------------------------
    # Prepare updates
    # ---------------------------------------------------------
    updates = []
    prediction_failed = 0

    for item, prediction in zip(
        successful_articles,
        predictions,
        strict=True,
    ):
        row = item["row"]
        article = item["article"]

        if (
            prediction.get("status") != "OK"
            or prediction.get("label") is None
            or prediction.get("score") is None
        ):
            prediction_failed += 1
            continue

        new_hash = generate_content_hash(
            row["title"],
            article.content,
        )["content_hash"]

        updates.append(
            {
                "id": row["id"],
                "content": article.content,
                "content_hash": new_hash,
                "category": prediction["label"],
                "decision_score": float(
                    prediction["score"]
                ),
                "old_category": row["category"],
                "new_category": prediction["label"],
                "old_content_len": row[
                    "old_content_len"
                ],
                "new_content_len": len(
                    article.content
                ),
            }
        )

    print(
        f"PREDICTION FAILED: "
        f"{prediction_failed}"
    )

    # ---------------------------------------------------------
    # Update inside one transaction
    # ---------------------------------------------------------
    changed_categories = 0
    same_categories = 0
    updated_count = 0
    hash_conflicts = 0

    async with engine.begin() as conn:

        # Existing hashes belonging to other rows.
        existing_hashes_result = await conn.execute(
            text(
                """
                SELECT id, content_hash
                FROM news
                """
            )
        )

        existing_hashes = {
            row.id: row.content_hash
            for row in existing_hashes_result
        }

        hash_to_id = {
            content_hash: row_id
            for row_id, content_hash
            in existing_hashes.items()
        }

        for item in updates:

            conflicting_id = hash_to_id.get(
                item["content_hash"]
            )

            if (
                conflicting_id is not None
                and conflicting_id != item["id"]
            ):
                print(
                    f"SKIP ID {item['id']}: "
                    f"content_hash conflict "
                    f"with ID {conflicting_id}"
                )

                hash_conflicts += 1
                continue

            await conn.execute(
                text(
                    """
                    UPDATE news
                    SET
                        content = :content,
                        content_hash = :content_hash,
                        category = :category,
                        decision_score = :decision_score
                    WHERE id = :id
                    """
                ),
                item,
            )

            updated_count += 1

            if (
                item["old_category"]
                != item["new_category"]
            ):
                changed_categories += 1
            else:
                same_categories += 1

    print()
    print("=" * 90)
    print("COMMIT SUMMARY")
    print("=" * 90)

    print(
        f"TOTAL DB ARTICLES     : "
        f"{len(rows)}"
    )

    print(
        f"FULLTEXT SUCCESS      : "
        f"{len(successful_articles)}"
    )

    print(
        f"FULLTEXT FAILED       : "
        f"{len(failed_fetches)}"
    )

    print(
        f"PREDICTION FAILED     : "
        f"{prediction_failed}"
    )

    print(
        f"UPDATED               : "
        f"{updated_count}"
    )

    print(
        f"CATEGORY CHANGED      : "
        f"{changed_categories}"
    )

    print(
        f"CATEGORY SAME         : "
        f"{same_categories}"
    )

    print(
        f"HASH CONFLICTS        : "
        f"{hash_conflicts}"
    )

    print()
    print(
        "8-ish failed articles remain unchanged."
    )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())