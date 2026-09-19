from __future__ import annotations

from dataclasses import dataclass

from src.crawler.article_fetcher import (
    AsyncArticleFetcher,
)
from src.crawler.config import RSSFeedConfig
from src.crawler.fetcher import (
    AsyncRSSFetcher,
    FetchError,
)
from src.crawler.prediction_client import (
    NewsPredictionClient,
)
from src.crawler.rss_parser import parse_rss
from src.db.deduplication import (
    generate_content_hash,
    normalize_url,
)
from src.db.repository import NewsRepository


@dataclass
class CrawlStats:
    feeds_total: int = 0
    feeds_success: int = 0
    feeds_failed: int = 0

    articles_parsed: int = 0
    articles_skipped: int = 0
    articles_duplicate: int = 0
    articles_predicted: int = 0
    articles_created: int = 0

    articles_fulltext_fetched: int = 0
    articles_fulltext_fallback: int = 0


class RSSCrawler:
    """
    RSS crawler orchestration layer.

    Flow:

        RSS
          ↓
        Parse
          ↓
        URL deduplication
          ↓
        Fetch full article HTML
          ↓
        Extract full content
          ↓
        FastAPI /predict/batch
          ↓
        PostgreSQL

    RSS is used for article discovery.
    The actual article page is used for ML content.
    """

    def __init__(
        self,
        *,
        fetcher: AsyncRSSFetcher,
        prediction_client: NewsPredictionClient,
        repository: NewsRepository,
    ) -> None:
        self.fetcher = fetcher
        self.prediction_client = prediction_client
        self.repository = repository

        self.article_fetcher = AsyncArticleFetcher(
            timeout_seconds=15.0,
            max_concurrency=1,
            max_content_chars=40_000,
        )

    async def crawl_feed(
        self,
        feed: RSSFeedConfig,
        stats: CrawlStats,
    ) -> None:

        try:
            xml_content = await self.fetcher.fetch(
                feed.url
            )

            articles = parse_rss(
                xml_content,
                source=feed.source,
            )

            stats.feeds_success += 1
            stats.articles_parsed += len(articles)

        except FetchError:
            stats.feeds_failed += 1
            return

        candidates = []

        for article in articles:
            normalized_url = normalize_url(
                article.url
            )

            hashes = generate_content_hash(
                article.title,
                article.content,
            )

            content_hash = hashes[
                "content_hash"
            ]

            # -----------------------------------------------------
            # Dedup BEFORE article fetch / ML inference
            # -----------------------------------------------------
            if await self.repository.exists_by_url(
                normalized_url
            ):
                stats.articles_duplicate += 1
                continue

            if await self.repository.exists_by_content_hash(
                content_hash
            ):
                stats.articles_duplicate += 1
                continue

            candidates.append(
                {
                    "article": article,
                    "normalized_url": normalized_url,
                    "content_hash": content_hash,
                }
            )

        if not candidates:
            return

        # ---------------------------------------------------------
        # Fetch full article content
        # ---------------------------------------------------------
        article_urls = [
            candidate["article"].url
            for candidate in candidates
        ]

        full_articles = (
            await self.article_fetcher.fetch_many(
                article_urls
            )
        )

        resolved_contents: list[str] = []
        content_sources: list[str] = []

        for candidate, full_article in zip(
            candidates,
            full_articles,
            strict=True,
        ):
            rss_content = (
                candidate["article"].content
            )

            if (
                full_article is not None
                and full_article.content
            ):
                resolved_contents.append(
                    full_article.content
                )

                content_sources.append("fulltext")

                stats.articles_fulltext_fetched += 1

            else:
                # -------------------------------------------------
                # Safe fallback:
                # use RSS snippet when full article cannot be fetched.
                # -------------------------------------------------
                resolved_contents.append(
                    rss_content
                )

                content_sources.append("rss_fallback")

                stats.articles_fulltext_fallback += 1

        # ---------------------------------------------------------
        # Batch inference through FastAPI
        # ---------------------------------------------------------
        prediction_inputs = [
            {
                "text": (
                    f"{candidate['article'].title}\n"
                    f"{content}"
                )
            }
            for candidate, content in zip(
                candidates,
                resolved_contents,
                strict=True,
            )
        ]

        predictions = (
            await self.prediction_client.predict_batch(
                prediction_inputs
            )
        )

        stats.articles_predicted += (
            len(predictions)
        )

        # ---------------------------------------------------------
        # Persist results
        # ---------------------------------------------------------
        for index, (
            candidate,
            prediction,
        ) in enumerate(
            zip(
                candidates,
                predictions,
                strict=True,
            )
        ):
            article = candidate["article"]

            label = prediction.get(
                "label"
            )

            score = prediction.get(
                "score"
            )

            status = prediction.get(
                "status"
            )

            # UNKNOWN / invalid prediction
            # should never become a normal category.
            if (
                status != "OK"
                or label is None
                or score is None
            ):
                stats.articles_skipped += 1
                continue

            news, create_status = (
                await self.repository
                .create_news_deduplicated(
                    url=candidate[
                        "normalized_url"
                    ],
                    title=article.title,
                    content=resolved_contents[
                        index
                    ],
                    content_source=content_sources[
                        index
                    ],
                    source=article.source,
                    category=label,
                    decision_score=float(
                        score
                    ),
                    published_at=(
                        article.published_at
                    ),
                )
            )

            if create_status == "CREATED":
                stats.articles_created += 1

            elif create_status.startswith(
                "DUPLICATE"
            ):
                stats.articles_duplicate += 1

    async def crawl_feeds(
        self,
        feeds: list[RSSFeedConfig],
    ) -> CrawlStats:

        stats = CrawlStats()

        enabled_feeds = [
            feed
            for feed in feeds
            if feed.enabled
        ]

        stats.feeds_total = len(
            enabled_feeds
        )

        # Keep one HTTP client alive for all feeds.
        async with self.article_fetcher:

            # -----------------------------------------------------
            # Feed isolation:
            # one failed feed must not stop other feeds.
            # -----------------------------------------------------
            for feed in enabled_feeds:
                await self.crawl_feed(
                    feed,
                    stats,
                )

        return stats