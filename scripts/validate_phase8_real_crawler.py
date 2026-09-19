from __future__ import annotations

import asyncio

import httpx

from src.crawler.config import DEFAULT_RSS_FEEDS
from src.crawler.crawler import RSSCrawler
from src.crawler.fetcher import AsyncRSSFetcher
from src.crawler.prediction_client import NewsPredictionClient
from src.db.database import AsyncSessionLocal
from src.db.repository import NewsRepository


API_BASE_URL = "http://fastapi:8000"


async def main() -> None:
    print("=" * 70)
    print("SECTION 8.5 REAL RSS -> FASTAPI -> POSTGRESQL VALIDATION")
    print("=" * 70)

    enabled_feeds = [
        feed
        for feed in DEFAULT_RSS_FEEDS
        if feed.enabled
    ]

    assert enabled_feeds, "No enabled RSS feeds configured."

    print()
    print("Configured RSS feeds:")

    for feed in enabled_feeds:
        print(
            f"  - {feed.name}: "
            f"{feed.url} "
            f"({feed.source})"
        )

    async with httpx.AsyncClient() as http_client:
        # -------------------------------------------------------------
        # 1. Verify FastAPI is available
        # -------------------------------------------------------------
        health_response = await http_client.get(
            f"{API_BASE_URL}/health",
            timeout=10.0,
        )

        assert health_response.status_code == 200, (
            f"FastAPI health check failed: "
            f"{health_response.status_code} "
            f"{health_response.text}"
        )

        print()
        print("PASS FastAPI health")

        # -------------------------------------------------------------
        # 2. Create real HTTP prediction client
        # -------------------------------------------------------------
        prediction_client = NewsPredictionClient(
            http_client,
            base_url=API_BASE_URL,
        )

        print("PASS real FastAPI prediction client")

        # -------------------------------------------------------------
        # 3. Create real RSS fetcher
        # -------------------------------------------------------------
        fetcher = AsyncRSSFetcher(
            http_client,
        )

        print("PASS real RSS fetcher")

        # -------------------------------------------------------------
        # 4. Use real PostgreSQL repository
        # -------------------------------------------------------------
        async with AsyncSessionLocal() as session:
            repository = NewsRepository(session)

            crawler = RSSCrawler(
                fetcher=fetcher,
                prediction_client=prediction_client,
                repository=repository,
            )

            # ---------------------------------------------------------
            # 5. Crawl real RSS feeds
            # ---------------------------------------------------------
            stats = await crawler.crawl_feeds(
                enabled_feeds,
            )

            print()
            print("REAL CRAWL RESULT")
            print("-" * 70)
            print(f"feeds_total       : {stats.feeds_total}")
            print(f"feeds_success     : {stats.feeds_success}")
            print(f"feeds_failed      : {stats.feeds_failed}")
            print(f"articles_parsed   : {stats.articles_parsed}")
            print(f"articles_skipped  : {stats.articles_skipped}")
            print(f"articles_duplicate: {stats.articles_duplicate}")
            print(f"articles_predicted: {stats.articles_predicted}")
            print(f"articles_created  : {stats.articles_created}")

            # ---------------------------------------------------------
            # 6. Basic assertions
            # ---------------------------------------------------------
            assert stats.feeds_total == len(enabled_feeds), (
                "Unexpected feed count."
            )

            assert stats.feeds_success + stats.feeds_failed == (
                stats.feeds_total
            ), "Feed success/failure accounting is inconsistent."

            assert stats.articles_predicted <= stats.articles_parsed, (
                "Predicted article count cannot exceed parsed article count."
            )

            assert stats.articles_created <= stats.articles_predicted, (
                "Created article count cannot exceed predicted article count."
            )

            print()
            print("PASS crawler statistics consistency")

    print()
    print("=" * 70)
    print("SECTION 8.5 REAL RSS CRAWLER: PASS")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())