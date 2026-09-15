import asyncio

import httpx

from src.crawler.fetcher import (
    AsyncRSSFetcher,
    FetchError,
    FetchHTTPError,
    FetchResponseTooLargeError,
    FetchTimeoutError,
)


async def main() -> None:
    print("=" * 70)
    print("SECTION 8.2 RSS FETCHER VALIDATION")
    print("=" * 70)

    state = {
        "retry_count": 0,
        "timeout_count": 0,
        "last_user_agent": None,
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        state["last_user_agent"] = request.headers.get("User-Agent")

        if request.url.path == "/success":
            return httpx.Response(
                200,
                headers={"Content-Type": "application/rss+xml"},
                content=b"<rss><channel><title>Vietnamese News</title></channel></rss>",
            )

        if request.url.path == "/retry":
            state["retry_count"] += 1

            if state["retry_count"] < 3:
                return httpx.Response(503, content=b"temporary failure")

            return httpx.Response(
                200,
                headers={"Content-Type": "application/rss+xml"},
                content=b"<rss><channel><title>Retry OK</title></channel></rss>",
            )

        if request.url.path == "/timeout":
            state["timeout_count"] += 1
            raise httpx.ReadTimeout(
                "simulated timeout",
                request=request,
            )

        if request.url.path == "/404":
            return httpx.Response(404, content=b"not found")

        if request.url.path == "/500":
            return httpx.Response(500, content=b"server error")

        if request.url.path == "/vietnamese":
            xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                "<rss><channel><title>"
                "Tin tức Việt Nam"
                "</title></channel></rss>"
            )

            raw = xml.encode("utf-8")

            # Deliberately provide a wrong HTTP charset.
            return httpx.Response(
                200,
                headers={
                    "Content-Type": "application/rss+xml; charset=iso-8859-1"
                },
                content=raw,
            )

        if request.url.path == "/large":
            return httpx.Response(
                200,
                headers={"Content-Type": "application/rss+xml"},
                content=b"x" * (10 * 1024 * 1024 + 1),
            )

        raise AssertionError(f"Unexpected path: {request.url.path}")

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        fetcher = AsyncRSSFetcher(
            client,
            max_retries=2,
            retry_backoff_seconds=0,
            max_response_bytes=10 * 1024 * 1024,
        )

        # ---------------------------------------------------------------
        # 1. Basic successful fetch
        # ---------------------------------------------------------------
        result = await fetcher.fetch("https://example.test/success")

        assert "Vietnamese News" in result
        print("PASS basic RSS fetch")

        # ---------------------------------------------------------------
        # 2. User-Agent
        # ---------------------------------------------------------------
        assert state["last_user_agent"] == "VietnameseNewsCrawler/1.0"
        print("PASS User-Agent")

        # ---------------------------------------------------------------
        # 3. Retry on HTTP 503
        # ---------------------------------------------------------------
        result = await fetcher.fetch("https://example.test/retry")

        assert "Retry OK" in result
        assert state["retry_count"] == 3

        print("PASS retry on HTTP 5xx")

        # ---------------------------------------------------------------
        # 4. Timeout retry
        # ---------------------------------------------------------------
        try:
            await fetcher.fetch("https://example.test/timeout")
            raise AssertionError("Expected FetchTimeoutError")
        except FetchTimeoutError:
            pass

        assert state["timeout_count"] == 3
        print("PASS timeout retry")

        # ---------------------------------------------------------------
        # 5. HTTP 404
        # ---------------------------------------------------------------
        try:
            await fetcher.fetch("https://example.test/404")
            raise AssertionError("Expected FetchHTTPError")
        except FetchHTTPError as exc:
            assert "404" in str(exc)

        print("PASS HTTP 404 handling")

        # ---------------------------------------------------------------
        # 6. HTTP 500 after retries
        # ---------------------------------------------------------------
        try:
            await fetcher.fetch("https://example.test/500")
            raise AssertionError("Expected FetchHTTPError")
        except FetchHTTPError as exc:
            assert "500" in str(exc)

        print("PASS HTTP 500 handling")

        # ---------------------------------------------------------------
        # 7. Vietnamese encoding
        # ---------------------------------------------------------------
        result = await fetcher.fetch("https://example.test/vietnamese")

        assert "Tin tức Việt Nam" in result
        print("PASS Vietnamese UTF-8/XML encoding")

        # ---------------------------------------------------------------
        # 8. Response body limit
        # ---------------------------------------------------------------
        try:
            await fetcher.fetch("https://example.test/large")
            raise AssertionError("Expected FetchResponseTooLargeError")
        except FetchResponseTooLargeError:
            pass

        print("PASS 10 MB response limit")

        # ---------------------------------------------------------------
        # 9. Reusable AsyncClient
        # ---------------------------------------------------------------
        first = await fetcher.fetch("https://example.test/success")
        second = await fetcher.fetch("https://example.test/success")

        assert "Vietnamese News" in first
        assert "Vietnamese News" in second

        print("PASS reusable AsyncClient")

        # ---------------------------------------------------------------
        # 10. Feed failure isolation
        # ---------------------------------------------------------------
        try:
            await fetcher.fetch("https://example.test/404")
        except FetchError:
            pass

        # The same client/fetcher must remain usable.
        result = await fetcher.fetch("https://example.test/success")

        assert "Vietnamese News" in result

        print("PASS failed feed does not poison fetcher")

    print("=" * 70)
    print("SECTION 8.2 RSS FETCHER: PASS")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())