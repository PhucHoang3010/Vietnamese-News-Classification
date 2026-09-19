from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from src.crawler.article_fetcher import AsyncArticleFetcher
from src.crawler.prediction_client import NewsPredictionClient


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured.")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1,
    )


OUTPUT = Path(
    "/app/backfill_phase8_review.json"
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

    report = {
        "total": len(rows),
        "fulltext_success": [],
        "fulltext_failed": [],
        "category_changed": [],
        "category_same": [],
    }

    async with AsyncArticleFetcher(
        timeout_seconds=15.0,
        max_concurrency=1,
        max_content_chars=40_000,
    ) as fetcher:

        async with httpx.AsyncClient() as http_client:

            prediction_client = NewsPredictionClient(
                http_client,
                base_url="http://fastapi:8000",
                timeout_seconds=30.0,
            )

            for row in rows:

                try:
                    article = await fetcher.fetch(
                        row["url"]
                    )

                    if not article.content:
                        report[
                            "fulltext_failed"
                        ].append(
                            {
                                "id": row["id"],
                                "url": row["url"],
                                "reason": "empty_content",
                            }
                        )
                        continue

                    report[
                        "fulltext_success"
                    ].append(
                        {
                            "id": row["id"],
                            "url": row["url"],
                            "old_content_len": row[
                                "old_content_len"
                            ],
                            "new_content_len": len(
                                article.content
                            ),
                        }
                    )

                    prediction = (
                        await prediction_client.predict_batch(
                            [
                                {
                                    "text": (
                                        f"{row['title']}\n"
                                        f"{article.content}"
                                    )
                                }
                            ]
                        )
                    )[0]

                    new_category = prediction[
                        "label"
                    ]

                    item = {
                        "id": row["id"],
                        "title": row["title"],
                        "url": row["url"],
                        "old_category": row[
                            "category"
                        ],
                        "new_category": new_category,
                        "old_content_len": row[
                            "old_content_len"
                        ],
                        "new_content_len": len(
                            article.content
                        ),
                        "new_score": prediction[
                            "score"
                        ],
                    }

                    if (
                        new_category
                        != row["category"]
                    ):
                        report[
                            "category_changed"
                        ].append(item)
                    else:
                        report[
                            "category_same"
                        ].append(item)

                except Exception as exc:
                    report[
                        "fulltext_failed"
                    ].append(
                        {
                            "id": row["id"],
                            "url": row["url"],
                            "reason": (
                                f"{type(exc).__name__}: "
                                f"{exc}"
                            ),
                        }
                    )

                await asyncio.sleep(0.5)

    OUTPUT.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 90)
    print("PHASE 8 BACKFILL REVIEW")
    print("=" * 90)

    print(
        f"TOTAL            : "
        f"{report['total']}"
    )

    print(
        f"FULLTEXT SUCCESS : "
        f"{len(report['fulltext_success'])}"
    )

    print(
        f"FULLTEXT FAILED  : "
        f"{len(report['fulltext_failed'])}"
    )

    print(
        f"CATEGORY CHANGED : "
        f"{len(report['category_changed'])}"
    )

    print(
        f"CATEGORY SAME    : "
        f"{len(report['category_same'])}"
    )

    print()
    print("=" * 90)
    print("CATEGORY CHANGES")
    print("=" * 90)

    for item in report[
        "category_changed"
    ]:
        print(
            f"ID {item['id']:>3} | "
            f"{item['old_category']} "
            f"-> "
            f"{item['new_category']} | "
            f"len "
            f"{item['old_content_len']} "
            f"-> "
            f"{item['new_content_len']} | "
            f"score="
            f"{item['new_score']:.6f}"
        )

    print()
    print("=" * 90)
    print("FULLTEXT FAILURES")
    print("=" * 90)

    for item in report[
        "fulltext_failed"
    ]:
        print(
            f"ID {item['id']:>3} | "
            f"{item['reason']} | "
            f"{item['url']}"
        )

    print()
    print(
        f"REPORT: {OUTPUT}"
    )

    print()
    print(
        "NO DATABASE UPDATE WAS PERFORMED."
    )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())