from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/crawler",
    tags=["Crawler"],
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
    "/status",
    summary="Get crawler status",
)
async def crawler_status():
    url = f"{get_crawler_url()}/status"

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                url,
                headers={
                    "X-Crawler-Token": get_crawler_token(),
                },
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="Crawler status service unavailable.",
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
async def crawler_run_now():
    url = f"{get_crawler_url()}/run"

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                url,
                headers={
                    "X-Crawler-Token": get_crawler_token(),
                },
            )

        if response.status_code == 409:
            raise HTTPException(
                status_code=409,
                detail="Crawler is already running.",
            )

        if response.status_code != 202:
            raise HTTPException(
                status_code=502,
                detail="Crawler rejected the request.",
            )

        return response.json()

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot reach crawler: {exc}",
        ) from exc
