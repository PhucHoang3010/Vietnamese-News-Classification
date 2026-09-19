from __future__ import annotations

import asyncio
import logging
import os

import httpx

from src.crawler.config import DEFAULT_RSS_FEEDS
from src.crawler.control import CrawlerControl
from src.crawler.crawler import RSSCrawler
from src.crawler.fetcher import create_fetcher
from src.crawler.prediction_client import NewsPredictionClient
from src.db.database import AsyncSessionLocal, engine
from src.db.repository import NewsRepository


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("crawler")


def get_prediction_api_url() -> str:
    return os.getenv(
        "PREDICTION_API_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")


def get_crawl_interval_seconds() -> int:
    value = os.getenv(
        "CRAWL_INTERVAL_SECONDS",
        "900",
    )

    try:
        interval = int(value)
    except ValueError as exc:
        raise ValueError(
            "CRAWL_INTERVAL_SECONDS must be an integer."
        ) from exc

    if interval < 10:
        raise ValueError(
            "CRAWL_INTERVAL_SECONDS must be >= 10."
        )

    return interval


async def run_crawl_once():
    prediction_api_url = get_prediction_api_url()

    logger.info(
        "Starting crawl cycle | prediction_api=%s",
        prediction_api_url,
    )

    async with create_fetcher() as fetcher:
        async with httpx.AsyncClient() as prediction_http_client:
            prediction_client = NewsPredictionClient(
                prediction_http_client,
                base_url=prediction_api_url,
            )

            async with AsyncSessionLocal() as session:
                repository = NewsRepository(session)

                crawler = RSSCrawler(
                    fetcher=fetcher,
                    prediction_client=prediction_client,
                    repository=repository,
                )

                stats = await crawler.crawl_feeds(
                    DEFAULT_RSS_FEEDS
                )

                logger.info(
                    (
                        "Crawl cycle completed | "
                        "feeds_total=%d "
                        "feeds_success=%d "
                        "feeds_failed=%d "
                        "articles_parsed=%d "
                        "articles_duplicate=%d "
                        "articles_predicted=%d "
                        "articles_created=%d "
                        "articles_skipped=%d "
                        "articles_fulltext_fetched=%d "
                        "articles_fulltext_fallback=%d"
                    ),
                    stats.feeds_total,
                    stats.feeds_success,
                    stats.feeds_failed,
                    stats.articles_parsed,
                    stats.articles_duplicate,
                    stats.articles_predicted,
                    stats.articles_created,
                    stats.articles_skipped,
                    stats.articles_fulltext_fetched,
                    stats.articles_fulltext_fallback,
                )

                return stats


async def scheduled_worker(
    control: CrawlerControl,
) -> None:
    interval_seconds = get_crawl_interval_seconds()

    logger.info(
        "Crawler worker started | interval=%d seconds",
        interval_seconds,
    )

    while True:
        try:
            if control.is_running():
                logger.info(
                    "Skipping scheduled crawl because "
                    "another crawl is running."
                )
            else:
                await control._run("scheduled")

        except Exception:
            logger.exception(
                "Scheduled crawl cycle failed unexpectedly."
            )

        logger.info(
            "Next crawl cycle in %d seconds.",
            interval_seconds,
        )

        await asyncio.sleep(interval_seconds)


async def main() -> None:
    control = CrawlerControl(
        crawl_func=run_crawl_once,
    )

    server = await asyncio.start_server(
        control.handle_client,
        host="0.0.0.0",
        port=9000,
    )

    logger.info(
        "Crawler control server started | port=9000"
    )

    worker_task = asyncio.create_task(
        scheduled_worker(control)
    )

    try:
        async with server:
            await server.serve_forever()

    except asyncio.CancelledError:
        logger.info("Crawler worker cancelled.")
        raise

    finally:
        worker_task.cancel()

        try:
            await worker_task
        except asyncio.CancelledError:
            pass

        if control._task and not control._task.done():
            control._task.cancel()

            try:
                await control._task
            except asyncio.CancelledError:
                pass

        await engine.dispose()

        logger.info(
            "Database engine disposed."
        )


if __name__ == "__main__":
    asyncio.run(main())
