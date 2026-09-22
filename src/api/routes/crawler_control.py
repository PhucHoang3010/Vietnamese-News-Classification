from __future__ import annotations

import os
from datetime import date

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.crawler.config import DEFAULT_RSS_FEEDS


router = APIRouter(
    prefix="/crawler",
    tags=["Crawler"],
)


class CrawlerRunRequest(BaseModel):
    sources: list[str] | None = Field(
        default=None,
        description="Crawler feed names. Empty/null = all enabled feeds.",
    )

    from_date: date | None = Field(
        default=None,
        description="Inclusive published date filter.",
    )

    to_date: date | None = Field(
        default=None,
        description="Inclusive published date filter.",
    )


def get_crawler_url() -> str:
    return os.getenv(
        "CRAWLER_CONTROL_URL",
        "http://crawler:9000",
    ).rstrip("/")


def get_crawler_token() -> str:
    return os.getenv(
        "CRAWLER_CONTROL_TOKEN",
        "local-dev-crawler-token",
    )


@router.get(
    "/sources",
    summary="Get available crawler sources",
)
async def crawler_sources():
    return {
        "items": [
            {
                "name": feed.name,
                "source": feed.source,
                "enabled": feed.enabled,
            }
            for feed in DEFAULT_RSS_FEEDS
        ]
    }


@router.get(
    "/status",
    summary="Get crawler status",
)
async def crawler_status():
    url = f"{get_crawler_url()}/status"

    try:
        async with httpx.AsyncClient(
            timeout=5
        ) as client:
            response = await client.get(
                url,
                headers={
                    "X-Crawler-Token":
                        get_crawler_token(),
                },
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Crawler status service unavailable."
                ),
            )

        return response.json()

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot reach crawler: {exc}",
        ) from exc


@router.post(
    "/run-now",
    summary="Trigger crawler immediately",
)
async def crawler_run_now(
    payload: CrawlerRunRequest | None = None,
):
    payload = payload or CrawlerRunRequest()

    if (
        payload.from_date is not None
        and payload.to_date is not None
        and payload.from_date > payload.to_date
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "from_date must be less than or "
                "equal to to_date."
            ),
        )

    url = f"{get_crawler_url()}/run"

    request_body = payload.model_dump(
        mode="json",
        exclude_none=True,
    )

    try:
        async with httpx.AsyncClient(
            timeout=5
        ) as client:
            response = await client.post(
                url,
                headers={
                    "X-Crawler-Token":
                        get_crawler_token(),
                    "Content-Type":
                        "application/json",
                },
                json=request_body,
            )

        if response.status_code == 409:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Crawler is already running."
                ),
            )

        if response.status_code == 400:
            try:
                detail = response.json().get(
                    "detail",
                    "Invalid crawler request.",
                )
            except Exception:
                detail = (
                    "Invalid crawler request."
                )

            raise HTTPException(
                status_code=400,
                detail=detail,
            )

        if response.status_code != 202:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Crawler rejected the request."
                ),
            )

        return response.json()

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot reach crawler: {exc}",
        ) from exc