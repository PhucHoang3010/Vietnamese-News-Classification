import asyncio
from datetime import datetime, timezone

import httpx

from src.crawler.config import RSSFeedConfig
from src.crawler.crawler import RSSCrawler
from src.crawler.fetcher import AsyncRSSFetcher
from src.crawler.prediction_client import NewsPredictionClient


RSS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Vietnamese News</title>

        <item>
            <title>Việt Nam phát triển công nghệ mới</title>
            <link>https://example.com/article-1</link>
            <description>
                Nội dung bài viết về công nghệ Việt Nam.
            </description>
            <pubDate>Mon, 15 Sep 2026 08:00:00 GMT</pubDate>
        </item>

        <item>
            <title>Giáo dục Việt Nam thay đổi</title>
            <link>https://example.com/article-2</link>
            <description>
                Nội dung bài viết về giáo dục.
            </description>
            <pubDate>Mon, 15 Sep 2026 09:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>
"""


class FakeRepository:
    def __init__(self) -> None:
        self.rows = []

    async def exists_by_url(self, url: str) -> bool:
        return any(row["url"] == url for row in self.rows)

    async def exists_by_content_hash(self, content_hash: str) -> bool:
        return any(
            row["content_hash"] == content_hash
            for row in self.rows
        )

    async def create_news_deduplicated(
        self,
        *,
        url,
        content_hash,
        title,
        content,
        source,
        category,
        decision_score,
        published_at,
    ):

        if await self.exists_by_url(url):
            return None, "DUPLICATE_URL"

        if await self.exists_by_content_hash(content_hash):
            return None, "DUPLICATE_CONTENT"

        row = {
            "url": url,
            "content_hash": content_hash,
            "title": title,
            "content": content,
            "source": source,
            "category": category,
            "decision_score": decision_score,
            "published_at": published_at,
        }

        self.rows.append(row)

        return row, "CREATED"


async def main() -> None:
    print("=" * 70)
    print("SECTION 8.3 RSS CRAWLER VALIDATION")
    print("=" * 70)

    request_log = []

    async def handler(request: httpx.Request) -> httpx.Response:
        request_log.append(
            {
                "url": str(request.url),
                "method": request.method,
            }
        )

        # -------------------------------------------------------------
        # RSS feed
        # -------------------------------------------------------------
        if request.url.host == "feed.test":
            return httpx.Response(
                200,
                headers={
                    "Content-Type": "application/rss+xml; charset=utf-8"
                },
                content=RSS_XML.encode("utf-8"),
            )

        # -------------------------------------------------------------
        # Prediction API
        # -------------------------------------------------------------
        if request.url.host == "api.test":
            assert request.method == "POST"
            assert request.url.path == "/predict/batch"

            payload = request.read().decode("utf-8")

            assert '"items"' in payload
            assert "Việt Nam" in payload

            return httpx.Response(
                200,
                json={
                    "predictions": [
                        {
                            "category": "Khoa học",
                            "decision_score": 2.41,
                        },
                        {
                            "category": "Giáo dục",
                            "decision_score": 1.87,
                        },
                    ]
                },
            )

        # -------------------------------------------------------------
        # Broken feed
        # -------------------------------------------------------------
        if request.url.host == "broken.test":
            return httpx.Response(
                500,
                content=b"broken",
            )

        raise AssertionError(
            f"Unexpected request: {request.method} {request.url}"
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport
    ) as http_client:

        fetcher = AsyncRSSFetcher(
            http_client,
            max_retries=0,
        )

        prediction_client = NewsPredictionClient(
            http_client,
            base_url="https://api.test",
        )

        repository = FakeRepository()

        crawler = RSSCrawler(
            fetcher=fetcher,
            prediction_client=prediction_client,
            repository=repository,
        )

        # -------------------------------------------------------------
        # 1. Successful crawl
        # -------------------------------------------------------------
        feed = RSSFeedConfig(
            name="test-feed",
            url="https://feed.test/news.xml",
            source="Test Source",
        )

        stats = await crawler.crawl_feeds([feed])

        assert stats.feeds_total == 1
        assert stats.feeds_success == 1
        assert stats.feeds_failed == 0
        assert stats.articles_parsed == 2
        assert stats.articles_predicted == 2
        assert stats.articles_created == 2

        print("PASS successful RSS → parse → predict → storage")

        # -------------------------------------------------------------
        # 2. Dedup before prediction
        # -------------------------------------------------------------
        stats = await crawler.crawl_feeds([feed])

        assert stats.articles_duplicate == 2
        assert stats.articles_predicted == 0
        assert stats.articles_created == 0

        print("PASS dedup before ML inference")

        # -------------------------------------------------------------
        # 3. Prediction API was actually called via HTTP
        # -------------------------------------------------------------
        prediction_calls = [
            item
            for item in request_log
            if item["url"] == "https://api.test/predict/batch"
        ]

        assert len(prediction_calls) == 1
        assert prediction_calls[0]["method"] == "POST"

        print("PASS crawler uses FastAPI HTTP /predict/batch")

        # -------------------------------------------------------------
        # 4. Feed isolation
        # -------------------------------------------------------------
        broken_feed = RSSFeedConfig(
            name="broken-feed",
            url="https://broken.test/news.xml",
            source="Broken Source",
        )

        stats = await crawler.crawl_feeds(
            [broken_feed, feed]
        )

        assert stats.feeds_total == 2
        assert stats.feeds_failed == 1
        assert stats.feeds_success == 1

        print("PASS failed feed does not stop other feeds")

        # -------------------------------------------------------------
        # 5. Stored rows
        # -------------------------------------------------------------
        assert len(repository.rows) == 2

        categories = {
            row["category"]
            for row in repository.rows
        }

        assert categories == {
            "Khoa học",
            "Giáo dục",
        }

        print("PASS predicted categories stored")

    print("=" * 70)
    print("SECTION 8.3 RSS CRAWLER: PASS")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())