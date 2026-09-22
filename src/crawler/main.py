from __future__ import annotations

import asyncio
import logging
import os
from datetime import date

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


def parse_iso_date(
    value: str | None,
) -> date | None:
    if value is None or value == "":
        return None

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid date format: {value}. "
            "Expected YYYY-MM-DD."
        ) from exc


def resolve_feeds(
    sources: list[str] | None,
):
    enabled_feeds = [
        feed
        for feed in DEFAULT_RSS_FEEDS
        if feed.enabled
    ]

    if not sources:
        return enabled_feeds

    requested = {
        source.strip().lower()
        for source in sources
        if source and source.strip()
    }

    if not requested:
        return enabled_feeds

    available = {
        feed.name.lower(): feed
        for feed in enabled_feeds
    }

    unknown = sorted(
        requested - available.keys()
    )

    if unknown:
        raise ValueError(
            "Unknown crawler source(s): "
            + ", ".join(unknown)
        )

    return [
        available[name]
        for name in sorted(requested)
    ]


async def run_crawl_once(
    options: dict | None = None,
):
    options = options or {}

    sources = options.get("sources")

    from_date = parse_iso_date(
        options.get("from_date")
    )
    to_date = parse_iso_date(
        options.get("to_date")
    )

    if (
        from_date is not None
        and to_date is not None
        and from_date > to_date
    ):
        raise ValueError(
            "from_date must be <= to_date."
        )

    feeds = resolve_feeds(sources)

    prediction_api_url = get_prediction_api_url()

    logger.info(
        (
            "Starting crawl cycle | "
            "prediction_api=%s | "
            "sources=%s | "
            "from_date=%s | "
            "to_date=%s"
        ),
        prediction_api_url,
        [feed.name for feed in feeds],
        from_date,
        to_date,
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
                    feeds,
                    from_date=from_date,
                    to_date=to_date,
                )

                logger.info(
                    (
                        "Crawl cycle completed | "
                        "feeds_total=%d "
                        "feeds_success=%d "
                        "feeds_failed=%d "
                        "articles_parsed=%d "
                        "articles_date_filtered=%d "
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
                    stats.articles_date_filtered,
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
                await control._run(
                    "scheduled",
                    {},
                )

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