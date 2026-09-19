from __future__ import annotations

import asyncio
import logging

import httpx

from src.crawler.article_parser import (
    ParsedArticle,
    parse_article_html,
)


logger = logging.getLogger("crawler.article_fetcher")


class ArticleFetchError(Exception):
    """Article page fetch or parsing failed."""


class AsyncArticleFetcher:
    """
    Fetch full article HTML and extract article body.

    RSS is used only to discover article URLs.
    This class retrieves the actual article page.

    Retry policy:
    - Retry timeout/network errors.
    - Retry HTTP 429.
    - Retry HTTP 5xx.
    - Do NOT retry normal 4xx errors such as 403/404.
    - Do NOT retry parser errors.
    """

    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        max_concurrency: int = 1,
        max_content_chars: int = 40_000,
        max_retries: int = 3,
        initial_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 8.0,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_concurrency = max_concurrency
        self.max_content_chars = max_content_chars

        self.max_retries = max(0, max_retries)
        self.initial_backoff_seconds = max(
            0.0,
            initial_backoff_seconds,
        )
        self.max_backoff_seconds = max(
            self.initial_backoff_seconds,
            max_backoff_seconds,
        )

        self._client: httpx.AsyncClient | None = None

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.5",
        }

    async def __aenter__(self) -> "AsyncArticleFetcher":
        self._client = httpx.AsyncClient(
            headers=self.headers,
            follow_redirects=True,
        )
        return self

    async def __aexit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ---------------------------------------------------------
    # Retry helpers
    # ---------------------------------------------------------

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        return (
            status_code == 429
            or 500 <= status_code <= 599
        )

    def _get_backoff_seconds(
        self,
        attempt: int,
        response: httpx.Response | None = None,
    ) -> float:
        """
        Exponential backoff:
            attempt 0 -> 1s
            attempt 1 -> 2s
            attempt 2 -> 4s
            ...

        For HTTP 429, respect Retry-After when available.
        """

        if response is not None:
            retry_after = response.headers.get(
                "Retry-After"
            )

            if retry_after:
                try:
                    retry_after_seconds = float(
                        retry_after
                    )

                    if retry_after_seconds >= 0:
                        return min(
                            retry_after_seconds,
                            self.max_backoff_seconds,
                        )
                except ValueError:
                    pass

        delay = (
            self.initial_backoff_seconds
            * (2 ** attempt)
        )

        return min(
            delay,
            self.max_backoff_seconds,
        )

    async def _sleep_before_retry(
        self,
        *,
        attempt: int,
        url: str,
        response: httpx.Response | None = None,
    ) -> None:
        delay = self._get_backoff_seconds(
            attempt,
            response,
        )

        logger.warning(
            "Retrying article fetch | "
            "attempt=%d/%d "
            "delay=%.1fs "
            "url=%s",
            attempt + 1,
            self.max_retries,
            delay,
            url,
        )

        if delay > 0:
            await asyncio.sleep(delay)

    # ---------------------------------------------------------
    # Fetch one article
    # ---------------------------------------------------------

    async def fetch(
        self,
        url: str,
    ) -> ParsedArticle:
        if self._client is None:
            raise ArticleFetchError(
                "AsyncArticleFetcher must be used "
                "inside 'async with'."
            )

        if not url or not url.strip():
            raise ArticleFetchError(
                "Article URL is empty."
            )

        last_error: Exception | None = None

        for attempt in range(
            self.max_retries + 1
        ):
            try:
                response = await self._client.get(
                    url,
                    timeout=self.timeout_seconds,
                )

                # -------------------------------------------------
                # Retryable HTTP status
                # -------------------------------------------------
                if self._is_retryable_status(
                    response.status_code
                ):
                    last_error = httpx.HTTPStatusError(
                        f"Retryable HTTP status "
                        f"{response.status_code}",
                        request=response.request,
                        response=response,
                    )

                    if attempt < self.max_retries:
                        await self._sleep_before_retry(
                            attempt=attempt,
                            url=url,
                            response=response,
                        )
                        continue

                    raise last_error

                # -------------------------------------------------
                # Non-retryable HTTP status
                # -------------------------------------------------
                response.raise_for_status()

                # -------------------------------------------------
                # Parse article
                # -------------------------------------------------
                parsed = parse_article_html(
                    response.text
                )

                content = parsed.content

                if len(content) > self.max_content_chars:
                    content = content[
                        : self.max_content_chars
                    ]

                return ParsedArticle(
                    title=parsed.title,
                    content=content,
                )

            except httpx.TimeoutException as exc:
                last_error = exc

                if attempt < self.max_retries:
                    await self._sleep_before_retry(
                        attempt=attempt,
                        url=url,
                    )
                    continue

                raise ArticleFetchError(
                    f"Timeout fetching article: {url}"
                ) from exc

            except httpx.NetworkError as exc:
                last_error = exc

                if attempt < self.max_retries:
                    await self._sleep_before_retry(
                        attempt=attempt,
                        url=url,
                    )
                    continue

                raise ArticleFetchError(
                    f"Network error fetching article: {url}"
                ) from exc

            except httpx.HTTPStatusError as exc:
                # 429 / 5xx exhausted retries
                if (
                    exc.response is not None
                    and self._is_retryable_status(
                        exc.response.status_code
                    )
                ):
                    raise ArticleFetchError(
                        "Retryable HTTP error exhausted "
                        f"for article: {url} "
                        f"(HTTP "
                        f"{exc.response.status_code})"
                    ) from exc

                # 4xx and other non-retryable HTTP errors
                raise ArticleFetchError(
                    f"HTTP error fetching article: {url} "
                    f"(HTTP "
                    f"{exc.response.status_code})"
                ) from exc

            except ValueError as exc:
                # Parsing/extraction failure:
                # retrying usually produces the same result.
                raise ArticleFetchError(
                    f"Article parsing failed: {url}"
                ) from exc

            except httpx.HTTPError as exc:
                last_error = exc

                if attempt < self.max_retries:
                    await self._sleep_before_retry(
                        attempt=attempt,
                        url=url,
                    )
                    continue

                raise ArticleFetchError(
                    f"HTTP error fetching article: {url}"
                ) from exc

        raise ArticleFetchError(
            f"Failed to fetch article: {url}"
        ) from last_error

    # ---------------------------------------------------------
    # Fetch many articles
    # ---------------------------------------------------------

    async def fetch_many(
        self,
        urls: list[str],
    ) -> list[ParsedArticle | None]:
        semaphore = asyncio.Semaphore(
            self.max_concurrency
        )

        async def fetch_one(
            url: str,
        ) -> ParsedArticle | None:
            async with semaphore:
                try:
                    return await self.fetch(url)

                except ArticleFetchError as exc:
                    logger.warning(
                        "Article fetch failed | "
                        "url=%s | error=%s",
                        url,
                        exc,
                    )
                    return None

        return await asyncio.gather(
            *(
                fetch_one(url)
                for url in urls
            )
        )