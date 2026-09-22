from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Awaitable, Callable


logger = logging.getLogger("crawler.control")


class CrawlerControl:
    def __init__(
        self,
        crawl_func: Callable[
            [dict],
            Awaitable[object],
        ],
    ) -> None:
        self.crawl_func = crawl_func

        self.token = os.getenv(
            "CRAWLER_CONTROL_TOKEN",
            "local-dev-crawler-token",
        )

        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None

        self.status = "idle"
        self.last_run_status = "never"
        self.last_run_source = None
        self.last_started_at = None
        self.last_finished_at = None
        self.last_error = None
        self.last_stats = None
        self.last_options = {}

    def is_running(self) -> bool:
        return (
            self._lock.locked()
            or (
                self._task is not None
                and not self._task.done()
            )
        )

    def status_payload(self) -> dict:
        return {
            "status": self.status,
            "last_run_status": self.last_run_status,
            "last_run_source": self.last_run_source,
            "last_started_at": self.last_started_at,
            "last_finished_at": self.last_finished_at,
            "last_error": self.last_error,
            "last_options": self.last_options,
            "last_stats": self.last_stats,
        }

    async def trigger(
        self,
        options: dict | None = None,
    ) -> bool:
        if self.is_running():
            return False

        normalized_options = options or {}

        self._task = asyncio.create_task(
            self._run(
                "manual",
                normalized_options,
            )
        )

        return True

    async def _run(
        self,
        source: str,
        options: dict | None = None,
    ) -> None:
        options = options or {}

        async with self._lock:
            self.status = "running"
            self.last_run_status = "running"
            self.last_run_source = source
            self.last_started_at = datetime.now(
                timezone.utc
            ).isoformat()
            self.last_finished_at = None
            self.last_error = None
            self.last_stats = None
            self.last_options = options

            logger.info(
                (
                    "Crawl started from control | "
                    "source=%s | options=%s"
                ),
                source,
                options,
            )

            try:
                stats = await self.crawl_func(
                    options
                )

                self.last_stats = {
                    key: value
                    for key, value in vars(stats).items()
                }

                self.last_run_status = "success"

                logger.info(
                    (
                        "Controlled crawl completed | "
                        "source=%s | options=%s"
                    ),
                    source,
                    options,
                )

            except Exception as exc:
                self.last_run_status = "error"
                self.last_error = str(exc)

                logger.exception(
                    (
                        "Controlled crawl failed | "
                        "source=%s | options=%s"
                    ),
                    source,
                    options,
                )

            finally:
                self.status = "idle"
                self.last_finished_at = datetime.now(
                    timezone.utc
                ).isoformat()

    def _authorized(
        self,
        headers: dict[str, str],
    ) -> bool:
        return (
            headers.get("x-crawler-token", "")
            == self.token
        )

    @staticmethod
    async def _write_response(
        writer: asyncio.StreamWriter,
        status_code: int,
        payload: dict,
    ) -> None:
        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        status_text = {
            200: "OK",
            202: "Accepted",
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found",
            405: "Method Not Allowed",
            409: "Conflict",
        }.get(
            status_code,
            "Error",
        )

        response = (
            f"HTTP/1.1 {status_code} {status_text}\r\n"
            "Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode("utf-8")

        writer.write(response + body)
        await writer.drain()

        writer.close()

        try:
            await writer.wait_closed()
        except Exception:
            pass

    @staticmethod
    async def _read_body(
        reader: asyncio.StreamReader,
        headers: dict[str, str],
    ) -> bytes:
        raw_length = headers.get(
            "content-length",
            "0",
        )

        try:
            content_length = int(raw_length)
        except ValueError:
            content_length = 0

        if content_length <= 0:
            return b""

        if content_length > 100_000:
            raise ValueError(
                "Request body is too large."
            )

        return await asyncio.wait_for(
            reader.readexactly(content_length),
            timeout=5,
        )

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            request_line = await asyncio.wait_for(
                reader.readline(),
                timeout=5,
            )

            if not request_line:
                writer.close()
                return

            parts = (
                request_line.decode(
                    "utf-8",
                    errors="replace",
                )
                .strip()
                .split()
            )

            if len(parts) < 2:
                await self._write_response(
                    writer,
                    400,
                    {"detail": "Invalid request"},
                )
                return

            method = parts[0].upper()
            path = parts[1]

            headers: dict[str, str] = {}

            while True:
                line = await asyncio.wait_for(
                    reader.readline(),
                    timeout=5,
                )

                if line in (
                    b"\r\n",
                    b"\n",
                    b"",
                ):
                    break

                decoded = line.decode(
                    "utf-8",
                    errors="replace",
                ).strip()

                if ":" in decoded:
                    key, value = decoded.split(
                        ":",
                        1,
                    )

                    headers[
                        key.strip().lower()
                    ] = value.strip()

            if not self._authorized(headers):
                await self._write_response(
                    writer,
                    401,
                    {"detail": "Unauthorized"},
                )
                return

            if method == "GET" and path == "/status":
                await self._write_response(
                    writer,
                    200,
                    self.status_payload(),
                )
                return

            if method == "POST" and path == "/run":
                body = await self._read_body(
                    reader,
                    headers,
                )

                options = {}

                if body:
                    try:
                        options = json.loads(
                            body.decode("utf-8")
                        )

                        if not isinstance(
                            options,
                            dict,
                        ):
                            raise ValueError(
                                "Request body must be a JSON object."
                            )

                    except (
                        json.JSONDecodeError,
                        UnicodeDecodeError,
                        ValueError,
                    ) as exc:
                        await self._write_response(
                            writer,
                            400,
                            {
                                "detail": str(exc),
                            },
                        )
                        return

                accepted = await self.trigger(
                    options
                )

                if not accepted:
                    await self._write_response(
                        writer,
                        409,
                        {
                            "status": "busy",
                            "detail": (
                                "Crawler is already running."
                            ),
                        },
                    )
                    return

                await self._write_response(
                    writer,
                    202,
                    {
                        "status": "accepted",
                        "detail": (
                            "Crawler run started."
                        ),
                        "options": options,
                    },
                )
                return

            await self._write_response(
                writer,
                404,
                {"detail": "Not Found"},
            )

        except Exception:
            logger.exception(
                "Crawler control request failed."
            )