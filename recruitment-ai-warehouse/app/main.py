"""FastAPI backend – TalentLens: Kho dữ liệu tuyển dụng có AI phân tích pipeline ứng viên."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import ai, analytics, auth, candidates, etl, reports
from app.seed import init_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_database()
    yield


app = FastAPI(
    title="TalentLens API",
    description="Kho dữ liệu tuyển dụng có AI phân tích pipeline ứng viên – ETL đa nguồn, BI, NLP/AI, RBAC.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
for module in (auth, candidates, analytics, ai, etl, reports):
    app.include_router(module.router, prefix="/api")


@app.get("/", tags=["Hệ thống"])
def root():
    return {"app": settings.app_name, "docs": "/docs", "health": "/api/health"}


@app.get("/api/health", tags=["Hệ thống"])
def health():
    return {"status": "ok", "ai_provider": "claude" if settings.use_claude else "local"}
