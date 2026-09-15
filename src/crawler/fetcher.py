from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Optional

import httpx


DEFAULT_USER_AGENT = "VietnameseNewsCrawler/1.0"
DEFAULT_MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_BACKOFF_SECONDS = 0.2


class FetchError(Exception):
    """Base exception for RSS fetching errors."""


class FetchHTTPError(FetchError):
    """HTTP response error."""


class FetchTimeoutError(FetchError):
    """Request timeout error."""


class FetchResponseTooLargeError(FetchError):
    """Response body exceeds configured maximum size."""


class AsyncRSSFetcher:
    """
    Reliable asynchronous RSS/Atom feed fetcher.

    The HTTP client can be injected so one AsyncClient can be reused
    across the entire crawler pipeline.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.client = client
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.user_agent = user_agent

    @staticmethod
    def _extract_charset_from_content_type(content_type: str | None) -> str | None:
        if not content_type:
            return None

        match = re.search(
            r"charset\s*=\s*[\"']?\s*([^;\"'\s]+)",
            content_type,
            flags=re.IGNORECASE,
        )

        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_xml_encoding(raw: bytes) -> str | None:
        """
        Extract encoding from an XML declaration.

        Example:
        <?xml version="1.0" encoding="UTF-8"?>
        """

        sample = raw[:1024]

        match = re.search(
            rb"<\?xml[^>]+encoding\s*=\s*[\"']([^\"']+)[\"']",
            sample,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        try:
            return match.group(1).decode("ascii").strip()
        except UnicodeDecodeError:
            return None

    @classmethod
    def _decode_response(cls, raw: bytes, content_type: str | None) -> str:
        """
        Decode XML safely.

        Priority:
        1. XML declaration
        2. HTTP Content-Type charset
        3. UTF-8 fallback with replacement

        XML declaration is preferred because RSS/Atom feeds sometimes
        contain an incorrect HTTP charset header.
        """

        xml_encoding = cls._extract_xml_encoding(raw)
        header_encoding = cls._extract_charset_from_content_type(content_type)

        encodings: list[str] = []

        if xml_encoding:
            encodings.append(xml_encoding)

        if header_encoding and header_encoding.lower() not in {
            e.lower() for e in encodings
        }:
            encodings.append(header_encoding)

        if "utf-8" not in {e.lower() for e in encodings}:
            encodings.append("utf-8")

        for encoding in encodings:
            try:
                return raw.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                continue

        return raw.decode("utf-8", errors="replace")

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        return status_code == 429 or 500 <= status_code <= 599

    async def _sleep_before_retry(self, attempt: int) -> None:
        delay = self.retry_backoff_seconds * (2**attempt)

        if delay > 0:
            await asyncio.sleep(delay)

    async def _read_limited_body(self, response: httpx.Response) -> bytes:
        """
        Read response body incrementally and enforce the size limit.
        """

        content_length = response.headers.get("Content-Length")

        if content_length:
            try:
                declared_size = int(content_length)

                if declared_size > self.max_response_bytes:
                    raise FetchResponseTooLargeError(
                        f"RSS response declares {declared_size} bytes, "
                        f"limit is {self.max_response_bytes} bytes."
                    )
            except ValueError:
                # Invalid Content-Length: fall back to streaming validation.
                pass

        chunks: list[bytes] = []
        total_size = 0

        async for chunk in response.aiter_bytes():
            total_size += len(chunk)

            if total_size > self.max_response_bytes:
                raise FetchResponseTooLargeError(
                    f"RSS response exceeded {self.max_response_bytes} bytes."
                )

            chunks.append(chunk)

        return b"".join(chunks)

    async def fetch(self, url: str) -> str:
        """
        Fetch one RSS/Atom feed.

        Retry policy:
        - Timeout / network errors: retry.
        - HTTP 429: retry.
        - HTTP 5xx: retry.
        - Other 4xx: fail immediately.
        """

        headers = {
            "User-Agent": self.user_agent,
            "Accept": (
                "application/rss+xml, "
                "application/atom+xml, "
                "application/xml, "
                "text/xml, "
                "*/*;q=0.1"
            ),
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.get(
                    url,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )

                if self._is_retryable_status(response.status_code):
                    if attempt < self.max_retries:
                        await self._sleep_before_retry(attempt)
                        continue

                    raise FetchHTTPError(
                        f"RSS fetch failed after retries: "
                        f"HTTP {response.status_code} for {url}"
                    )

                if response.status_code >= 400:
                    raise FetchHTTPError(
                        f"RSS fetch failed: "
                        f"HTTP {response.status_code} for {url}"
                    )

                raw_body = await self._read_limited_body(response)

                return self._decode_response(
                    raw_body,
                    response.headers.get("Content-Type"),
                )

            except FetchResponseTooLargeError:
                raise

            except FetchHTTPError:
                raise

            except httpx.TimeoutException as exc:
                if attempt >= self.max_retries:
                    raise FetchTimeoutError(
                        f"RSS fetch timed out after retries: {url}"
                    ) from exc

                await self._sleep_before_retry(attempt)

            except httpx.RequestError as exc:
                if attempt >= self.max_retries:
                    raise FetchError(
                        f"RSS fetch request failed after retries: {url}"
                    ) from exc

                await self._sleep_before_retry(attempt)

        raise FetchError(f"RSS fetch failed unexpectedly: {url}")


@asynccontextmanager
async def create_fetcher(
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
    user_agent: str = DEFAULT_USER_AGENT,
) -> AsyncIterator[AsyncRSSFetcher]:
    """
    Production convenience context manager.

    One AsyncClient is created and reused for all fetches inside the
    context, then closed exactly once.
    """

    async with httpx.AsyncClient() as client:
        yield AsyncRSSFetcher(
            client,
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
            user_agent=user_agent,
        )