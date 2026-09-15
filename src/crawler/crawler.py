from __future__ import annotations

from dataclasses import dataclass

from src.crawler.config import RSSFeedConfig
from src.crawler.fetcher import AsyncRSSFetcher, FetchError
from src.crawler.prediction_client import NewsPredictionClient
from src.crawler.rss_parser import parse_rss
from src.db.deduplication import generate_content_hash, normalize_url
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


class RSSCrawler:
    """
    RSS crawler orchestration layer.

    Responsibilities:
    1. Fetch RSS feeds.
    2. Parse RSS/Atom.
    3. Normalize URL/content.
    4. Deduplicate before ML inference.
    5. Call FastAPI /predict/batch.
    6. Persist classified articles to PostgreSQL.

    The crawler never imports VietnameseNewsPredictor.
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

    async def crawl_feed(
        self,
        feed: RSSFeedConfig,
        stats: CrawlStats,
    ) -> None:
        try:
            xml_content = await self.fetcher.fetch(feed.url)

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
            normalized_url = normalize_url(article.url)

            hashes = generate_content_hash(
                article.title,
                article.content,
            )

            content_hash = hashes["content_hash"]

            # ---------------------------------------------------------
            # Dedup BEFORE ML inference
            # ---------------------------------------------------------
            if await self.repository.exists_by_url(normalized_url):
                stats.articles_duplicate += 1
                continue

            if await self.repository.exists_by_content_hash(content_hash):
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

        # -------------------------------------------------------------
        # Batch inference through FastAPI
        # -------------------------------------------------------------
        prediction_inputs = [
            {
                "text": (
                    f"{candidate['article'].title}\n"
                    f"{candidate['article'].content}"
                )
            }
            for candidate in candidates
        ]

        predictions = await self.prediction_client.predict_batch(
            prediction_inputs
        )

        stats.articles_predicted += len(predictions)

        # -------------------------------------------------------------
        # Persist results
        # -------------------------------------------------------------
        for candidate, prediction in zip(
            candidates,
            predictions,
            strict=True,
        ):
            article = candidate["article"]

            label = prediction.get("label")
            score = prediction.get("score")
            status = prediction.get("status")

            # UNKNOWN hoặc prediction thiếu dữ liệu hợp lệ
            # không được ghi vào database như một category bình thường.
            if (
                status != "OK"
                or label is None
                or score is None
            ):
                stats.articles_skipped += 1
                continue

            news, status = await self.repository.create_news_deduplicated(
                url=candidate["normalized_url"],
                title=article.title,
                content=article.content,
                source=article.source,
                category=label,
                decision_score=float(score),
                published_at=article.published_at,
            )

            if status == "CREATED":
                stats.articles_created += 1
            elif status.startswith("DUPLICATE"):
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

        stats.feeds_total = len(enabled_feeds)

        # -------------------------------------------------------------
        # Feed isolation:
        # one failed feed must not stop other feeds.
        # -------------------------------------------------------------
        for feed in enabled_feeds:
            await self.crawl_feed(
                feed,
                stats,
            )

        return stats